"""Adapter protocol shared by every per-agent installer.

An adapter is a small class with three responsibilities:

1. ``detect()`` — best-effort check for whether the target agent is
   installed on this machine. Used by ``robotframework-plugins targets`` and to
   gate ``install --all``.
2. ``plan(opts)`` — produce a :class:`InstallPlan` describing every
   file to write and every config-merge to perform. **No I/O** here so
   that ``--dry-run`` can render the plan without side effects and
   tests can assert on the plan structure.
3. ``post_install(opts)`` — return a list of human-readable warnings or
   next-step instructions printed after a successful install (e.g.
   "enable preview flags X, Y").

The CLI's ``install`` flow is:

    plan = adapter.plan(opts)
    if --dry-run: render(plan); return
    execute(plan)              # writes files, performs merges
    manifest.upsert(...)       # records what we wrote
    print(adapter.post_install(opts))   # nudges to user

Tests in ``tests/installer/test_adapter_*.py`` assert on plan structure
without ever touching real user homes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

from .._assets import DEFAULT_PLUGIN, content_plugins


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InstallOptions:
    """User-supplied flags passed to every adapter for one install run."""

    scope: str = "project"              # "project" (default) | "user"
    project_dir: Path | None = None     # project scope target; defaults to CWD
    prefix: Path | None = None          # override the install root (for tests / sandboxing)
    what: frozenset[str] = field(
        default_factory=lambda: frozenset({"skills", "agents", "hooks"})
    )
    dry_run: bool = False
    force: bool = False                 # overwrite even when destination is user-modified
    mode: str = "files"                 # "files" (copy the bundle) | "plugin" (point at the marketplace)
    ref: str | None = None              # plugin mode: pin the marketplace to this git ref / tag
    # The bundled plugins this run installs, and the one an adapter's
    # ``plan`` is planning right now (the CLI plans each in turn).
    plugins: tuple[str, ...] = field(default_factory=content_plugins)
    plugin: str = DEFAULT_PLUGIN
    # True when ``--plugins`` named the plugins. Otherwise an upgrade keeps
    # what the target already has (see ``upgrade_plugins``).
    plugins_explicit: bool = False


@dataclass(frozen=True)
class InstallTarget:
    """One file that should be written to ``dst`` (post-transform).

    ``payload`` is the bytes that go to disk. ``transform_name`` is a
    string label (e.g. ``"skill_md_to_cursor_mdc"``) recorded in the
    manifest for traceability — uninstall doesn't *use* it, but it
    makes ``robotframework-plugins list --verbose`` informative.

    Marking ``executable=True`` makes the dispatcher chmod +x after
    write (no-op on Windows; harmless).
    """

    dst: Path
    payload: bytes
    transform_name: str | None = None
    executable: bool = False
    plugin: str | None = None           # bundled plugin the file comes from (set by the CLI)


@dataclass(frozen=True)
class ConfigMergeOp:
    """A merge into a pre-existing config file.

    ``apply`` is a callable that performs the merge and returns the
    list of keys it added at the location identified by ``key_path``.
    The dispatcher records the result in the manifest's
    ``config_merges`` so ``uninstall`` can later remove only those
    keys, traversing into ``key_path`` first.

    ``kind`` tags the file format so uninstall can dispatch to the
    right remover (``json_top``, ``json_nested``, ``toml_table``,
    ``yaml_block``). ``key_path`` is the parent traversal: ``()`` for
    top-level merges, e.g. ``("mcpServers",)`` for nested merges into
    ``mcpServers`` inside a ``.mcp.json`` file.

    ``revert`` is the in-process reverse — adapters expose it for
    transactional rollback in case ``apply`` later fails. Out-of-
    process uninstall (``robotframework-plugins uninstall``) reconstructs
    deletion from ``kind`` + ``key_path`` + recorded ``added_keys``
    rather than calling this callback (it lives in the install
    process only).
    """

    path: Path
    description: str  # human readable, shown in --dry-run output
    apply: Callable[[], list[str]]
    revert: Callable[[], None]  # called by uninstall in same process
    kind: str = "json_top"
    key_path: tuple[str, ...] = ()
    # For kind="json_hooks": the install-dir ownership marker so that
    # out-of-process uninstall can remove only rf-agentskills-owned hook
    # matcher-groups (see transforms.remove_owned_hook_entries).
    marker: str | None = None


@dataclass(frozen=True)
class InstallPlan:
    """Everything one adapter wants to do for a single install."""

    targets: tuple[InstallTarget, ...] = ()
    merges: tuple[ConfigMergeOp, ...] = ()
    notes: tuple[str, ...] = ()         # "matched feature shipped but disabled" etc.


# ---------------------------------------------------------------------------
# Protocol — adapters implement this informally; we declare it for type checkers
# ---------------------------------------------------------------------------


class Adapter(Protocol):
    """The contract every per-agent adapter satisfies.

    Implemented as a Protocol rather than an ABC so adapters can be
    plain classes; the CLI uses :class:`AdapterBase` for shared
    helpers but adapters needn't subclass it.
    """

    name: str           # short id, e.g. "claude-code", used by --agent
    pretty: str         # display name, e.g. "Claude Code"

    def detect(self) -> bool: ...

    def plan(self, opts: InstallOptions) -> InstallPlan: ...

    def post_install(self, opts: InstallOptions) -> list[str]: ...


# ---------------------------------------------------------------------------
# Helpers shared by concrete adapters
# ---------------------------------------------------------------------------


class AdapterBase:
    """Convenience base — adapters can subclass for shared helpers.

    Not required (the protocol is structural) but eliminates a lot of
    boilerplate in each adapter for things like "where is the install
    root, with --prefix and --scope folded in".
    """

    name: str = "?"
    pretty: str = "?"

    # Whether the agent substitutes ${CLAUDE_SKILL_DIR} in SKILL.md content
    # itself (Claude Code does). When False, installed skill text files get
    # the absolute installed skill dir written in (transforms.substitute_skill_dir).
    expands_skill_dir: bool = False

    # Default user-config root if --prefix is not set. Overridden per
    # adapter (e.g. ~/.claude or ~/.codex).
    user_root_subpath: tuple[str, ...] = ()
    project_root_subpath: tuple[str, ...] = (".claude",)

    def install_root(self, opts: InstallOptions) -> Path:
        """The base directory we write into for this install."""
        if opts.prefix is not None:
            return opts.prefix
        if opts.scope == "project":
            # project scope defaults to the current directory
            project = opts.project_dir if opts.project_dir is not None else Path.cwd()
            return project.joinpath(*self.project_root_subpath)
        return Path.home().joinpath(*self.user_root_subpath)

    @staticmethod
    def filtered(items: Iterable[Any], what: frozenset[str], category: str) -> list[Any]:
        """Filter helper for ``--what`` selectivity."""
        return list(items) if category in what else []

    def plugin_plan(self, opts: InstallOptions) -> InstallPlan | None:
        """Plan for ``--mode plugin``; ``None`` means "no marketplace, copy files"."""
        return None

    def plugin_commands(self, opts: InstallOptions) -> list[list[str]]:
        """Per-user commands plugin mode prints (and runs with ``--yes``)."""
        return []

    def render_skill_dir(self, payload: bytes, src: Path, skill_dir_dst: Path) -> bytes:
        """Apply ``${CLAUDE_SKILL_DIR}`` substitution for non-expanding agents."""
        from .. import transforms as _x  # local import: transforms has no adapter deps

        if self.expands_skill_dir or not _x.is_substitution_candidate(src):
            return payload
        return _x.substitute_skill_dir_bytes(
            payload, _x.to_native_path_string(skill_dir_dst.resolve())
        )


# ---------------------------------------------------------------------------
# Plugin mode (marketplace-distribution): point an agent at the marketplace
# ---------------------------------------------------------------------------

MARKETPLACE_NAME = "robotframework-plugins"
MARKETPLACE_REPO = "MarketSquare/robotframework-plugins"
#: The marketplace this one replaces; its settings entries are migrated on reinstall.
OLD_MARKETPLACE_NAME = "robotframework-agentskills"
OLD_MARKETPLACE_REPO = "manykarim/robotframework-agentskills"
PLUGIN_NAME = "rf-agentskills"
PLUGIN_ID = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"


def plugin_id(plugin: str) -> str:
    """Install id of a bundled plugin in the marketplace: ``<plugin>@robotframework-plugins``."""
    return f"{plugin}@{MARKETPLACE_NAME}"


def support_dir_name(plugin: str) -> str:
    """Folder that holds a plugin's scripts, hooks and skill scripts in file mode."""
    return f"{plugin}-files"


#: Test hook: a local checkout to use as the marketplace instead of GitHub.
MARKETPLACE_DIR_ENV = "RF_AGENTSKILLS_MARKETPLACE_DIR"


def marketplace_source(ref: str | None) -> dict[str, Any]:
    """``extraKnownMarketplaces`` source: GitHub (optionally pinned) or a local dir."""
    local = os.environ.get(MARKETPLACE_DIR_ENV)
    if local:
        return {"source": "directory", "path": str(Path(local).resolve())}
    source: dict[str, Any] = {"source": "github", "repo": MARKETPLACE_REPO}
    if ref:
        source["ref"] = ref
    return source


def _old_marketplace_entry(settings_path: Path) -> dict[str, Any] | None:
    """The ``robotframework-agentskills`` marketplace entry in ``settings_path``, if any.

    Only an entry whose source is the old GitHub repository counts, so a
    user's own marketplace that happens to share the name is left alone.
    """
    import json

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("extraKnownMarketplaces"), dict):
        return None
    entry = data["extraKnownMarketplaces"].get(OLD_MARKETPLACE_NAME)
    if not isinstance(entry, dict):
        return None
    source = entry.get("source")
    if not isinstance(source, dict) or source.get("repo") != OLD_MARKETPLACE_REPO:
        return None
    return entry


def old_marketplace_note(settings_path: Path) -> str | None:
    """A note naming the migration, when ``settings_path`` holds the old entry."""
    if _old_marketplace_entry(settings_path) is None:
        return None
    return (
        f"{settings_path}: replaced the {OLD_MARKETPLACE_NAME} marketplace "
        f"({OLD_MARKETPLACE_REPO}) with {MARKETPLACE_NAME} ({MARKETPLACE_REPO})."
    )


def enabled_marketplace_plugins(settings_path: Path) -> list[str]:
    """Plugins ``settings_path`` already enables from this marketplace; the old
    ``rf-agentskills@robotframework-agentskills`` entry counts as the bundle."""
    import json

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    enabled = data.get("enabledPlugins") if isinstance(data, dict) else None
    if not isinstance(enabled, dict):
        return []
    names: list[str] = []
    for key, on in enabled.items():
        name, _, market = str(key).partition("@")
        if on and (market == MARKETPLACE_NAME or (market == OLD_MARKETPLACE_NAME and name == PLUGIN_NAME)):
            if name not in names:
                names.append(name)
    return names


def upgrade_plugins(settings_path: Path, opts: InstallOptions) -> tuple[str, ...]:
    """The plugins to enable in ``settings_path``: ``--plugins`` when given;
    otherwise what the file already enables (an upgrade, so nothing the user
    had disappears), else ``opts.plugins``."""
    if opts.plugins_explicit:
        return opts.plugins
    return tuple(enabled_marketplace_plugins(settings_path)) or opts.plugins


def marketplace_settings_merges(
    settings_path: Path, ref: str | None, plugins: Iterable[str] = (PLUGIN_NAME,)
) -> list[ConfigMergeOp]:
    """Merge ``extraKnownMarketplaces`` + ``enabledPlugins`` into a settings JSON.

    The shape Claude Code, Copilot CLI and VS Code read from ``.claude/settings.json``
    (Copilot also from ``.github/copilot/settings.json``). Each key is its own
    ``json_nested`` merge, so uninstall removes exactly the entries we added.

    When the file still holds the old ``robotframework-agentskills`` entries,
    they are removed first, and the old entry's ``ref`` pin is kept unless
    ``ref`` is given. The removal adds no keys, so uninstall has nothing of
    it to undo.
    """
    from .. import transforms as _x

    migrations: list[ConfigMergeOp] = []
    old = _old_marketplace_entry(settings_path)
    if old is not None:
        if ref is None:
            ref = old["source"].get("ref")

        def drop_old() -> list[str]:
            _x.remove_json_keys_at_path(settings_path, ["extraKnownMarketplaces"], [OLD_MARKETPLACE_NAME])
            _x.remove_json_keys_at_path(
                settings_path, ["enabledPlugins"], [f"{PLUGIN_NAME}@{OLD_MARKETPLACE_NAME}"])
            return []

        migrations.append(ConfigMergeOp(
            path=settings_path,
            description=f"replace marketplace {OLD_MARKETPLACE_NAME} in {settings_path}",
            apply=drop_old,
            revert=lambda: None,
            kind="json_nested",
            key_path=("extraKnownMarketplaces",),
        ))

    def op(key: str, values: dict[str, Any], what: str) -> ConfigMergeOp:
        return ConfigMergeOp(
            path=settings_path,
            description=f"add {what} to {settings_path}",
            apply=lambda: _x.merge_json_at_path(settings_path, [key], values),
            revert=lambda: _x.remove_json_keys_at_path(settings_path, [key], list(values)),
            kind="json_nested",
            key_path=(key,),
        )

    return [
        *migrations,
        op("extraKnownMarketplaces", {MARKETPLACE_NAME: {"source": marketplace_source(ref)}},
           f"marketplace {MARKETPLACE_NAME}"),
        op("enabledPlugins", {plugin_id(p): True for p in plugins},
           "enabled plugin(s) " + ", ".join(plugin_id(p) for p in plugins)),
    ]


def skill_script_files(src_root: Path) -> list[Path]:
    """Every file under ``skills/<skill>/scripts/`` of the bundled plugin tree.

    Adapters that install hooks stage these under
    ``rf-agentskills-files/skills/<skill>/scripts/`` too: the Stop hook runs
    ``../skills/rf-results/scripts/rf_results.py`` relative to the hook
    scripts, independent of where the agent's skills are installed.
    """
    return [
        f for f in sorted(src_root.glob("skills/*/scripts/**/*"))
        if f.is_file() and "__pycache__" not in f.parts
    ]
