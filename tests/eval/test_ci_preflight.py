"""CI preflight path mapping (task 7.1) and workflow structure (7.2-7.4)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from rf_skill_eval import cli
from rf_skill_eval.application.preflight import frontmatter_description, map_changed_paths

_REPO = Path(__file__).resolve().parents[2]
_DIRS = {
    "rf-browser": "rf-browser",
    "rf-selenium": "rf-selenium",
    "rf-requests": "rf-requests",
    "rf-restinstance": "rf-restinstance",
}
_TASKS = {"plugins/rf-web/evals/tasks/narrow/narrow-browser-login-01.yaml": "rf-browser"}
_FIXTURES = {"sut-api": {"rf-requests", "rf-restinstance"}}
runner = CliRunner()


def _map(paths: list[str], changed: set[str] | None = None):  # type: ignore[no-untyped-def]
    return map_changed_paths(
        paths,
        dir_to_skill=_DIRS,
        task_skill=_TASKS.get,
        fixture_skills=_FIXTURES,
        description_changed=lambda p: p in (changed or set()),
    )


@pytest.mark.parametrize(
    ("paths", "skills"),
    [
        (["plugins/rf-web/skills/rf-selenium/references/locators.md"], {"rf-selenium"}),
        (["plugins/rf-web/skills/rf-selenium/SKILL.md"], {"rf-selenium"}),
        (["plugins/rf-web/evals/tasks/narrow/narrow-browser-login-01.yaml"], {"rf-browser"}),
        (["eval/fixtures/sut-api/libraries/ApiServer.py"], {"rf-requests", "rf-restinstance"}),
        (["plugins/rf-core/hooks/hooks.json"], {"plugin"}),
        (["README.md", "docs/ci/usage.md"], set()),
    ],
)
def test_changed_paths_map_to_skills(paths: list[str], skills: set[str]) -> None:
    result = _map(paths)
    assert result.skills == skills
    assert result.full_tier is False


def test_harness_change_selects_full_narrow_tier() -> None:
    result = _map(["src/rf_skill_eval/cli.py", "plugins/rf-web/skills/rf-browser/SKILL.md"])
    assert result.full_tier is True
    assert result.skills_arg() == ""
    assert result.github_outputs()["full_tier"] == "true"


def test_scoped_run_always_includes_canaries() -> None:
    assert _map(["plugins/rf-web/skills/rf-selenium/SKILL.md"]).skills_arg() == "plugin,rf-selenium"


def test_description_change_triggers_trigger_eval() -> None:
    result = _map(["plugins/rf-web/skills/rf-browser/SKILL.md"], changed={"plugins/rf-web/skills/rf-browser/SKILL.md"})
    assert result.trigger_skills == {"rf-browser"}
    assert result.github_outputs()["run_triggers"] == "true"
    body_only = _map(["plugins/rf-web/skills/rf-browser/SKILL.md"])
    assert body_only.trigger_skills == set()
    assert body_only.github_outputs()["run_triggers"] == "false"


def test_trigger_set_change_runs_that_set() -> None:
    assert _map(["plugins/rf-api/evals/triggers/rf-requests.yaml"]).trigger_skills == {"rf-requests"}


def test_nothing_relevant_means_no_evals() -> None:
    assert _map(["README.md"]).github_outputs()["run_evals"] == "false"


def test_frontmatter_description() -> None:
    text = '---\nname: x\ndescription: "Writes, fixes: tests"\nlicense: Apache-2.0\n---\nbody\n'
    assert frontmatter_description(text) == "Writes, fixes: tests"
    assert frontmatter_description("no frontmatter") is None
    assert frontmatter_description(None) is None


def test_preflight_cli_with_paths_file(tmp_path: Path) -> None:
    paths = tmp_path / "paths.txt"
    paths.write_text("plugins/rf-web/skills/rf-selenium/SKILL.md\nplugins/rf-api/evals/tasks/narrow/narrow-requests-users-01.yaml\n")
    out = tmp_path / "gh_output"
    res = runner.invoke(cli.app, ["preflight", "--paths-file", str(paths),
                                  "--github-output", str(out)])
    assert res.exit_code == 0, res.stdout
    outputs = dict(line.split("=", 1) for line in out.read_text().splitlines())
    assert outputs["skills"] == "plugin,rf-requests,rf-selenium"
    assert outputs["run_evals"] == "true"
    # without git history a changed SKILL.md is assumed to carry a new description
    assert outputs["trigger_skills"] == "rf-selenium"


# --- workflow structure ----------------------------------------------------------------

_WORKFLOW = _REPO / ".github" / "workflows" / "skill-evaluation.yml"


def _wf() -> dict:  # type: ignore[type-arg]
    return yaml.safe_load(_WORKFLOW.read_text())


def _job_text(job: dict) -> str:  # type: ignore[type-arg]
    parts = [str(v) for v in (job.get("env") or {}).values()]
    parts += [str(step.get("run", "")) for step in job["steps"]]
    parts += [str(step.get("with", "")) for step in job["steps"]]
    return "\n".join(parts)


def test_workflow_is_valid_yaml_with_expected_jobs() -> None:
    wf = _wf()
    assert {"preflight", "pr-eval", "full-eval"} <= set(wf["jobs"])


def test_every_harness_invocation_has_a_cost_cap() -> None:
    text = _WORKFLOW.read_text()
    for cmd in ("run-batch", "trigger"):
        for line in [ln for ln in text.splitlines() if f"rf-skill-eval {cmd}" in ln]:
            block = text[text.index(line):text.index(line) + 800]
            assert "--max-cost-usd" in block, line


def test_pr_job_is_treatment_only_runs_3_and_gated_on_the_preflight_model() -> None:
    wf = _wf()
    job = wf["jobs"]["pr-eval"]
    text = _job_text(job)
    assert "--arms treatment" in text
    assert "--runs 3" in text
    assert '--model "${EVAL_MODEL}"' in text
    assert '--max-turns-factor "${TURNS_FACTOR}"' in text
    assert job["env"]["EVAL_MODEL"] == "${{ needs.preflight.outputs.model }}"
    assert wf["env"]["HAIKU_MODEL"] == "claude-haiku-5-5"
    assert wf["env"]["OPENROUTER_MODEL"] == "z-ai/glm-5.3-flash"
    assert "rf-skill-eval gate" in text
    assert '--baseline "${BASELINES}narrow.json"' in text
    assert "--split validation" in text


def _run_creds(tmp_path: Path, **env: str) -> dict[str, str]:
    """Run the preflight credentials step's script with the given secrets set."""
    import os
    import subprocess

    wf = _wf()
    step = next(s for s in wf["jobs"]["preflight"]["steps"] if s.get("id") == "creds")
    out = tmp_path / "out"
    out.write_text("")
    base = {"PATH": os.environ["PATH"], "GITHUB_OUTPUT": str(out), "FORK_PR": "false",
            "REQUESTED": "", "CLAUDE_CODE_OAUTH_TOKEN": "", "ANTHROPIC_API_KEY": "",
            "OPENROUTER_API_KEY": "", **{k: str(v) for k, v in wf["env"].items()}}
    subprocess.run(["bash", "-eo", "pipefail", "-c", step["run"]], env={**base, **env}, check=True)
    return dict(line.split("=", 1) for line in out.read_text().splitlines() if "=" in line)


def test_preflight_prefers_openrouter_when_its_key_is_set(tmp_path: Path) -> None:
    got = _run_creds(tmp_path, OPENROUTER_API_KEY="k", CLAUDE_CODE_OAUTH_TOKEN="t")
    assert got == {
        "has_credentials": "true",
        "provider": "openrouter",
        "model": "z-ai/glm-5.3-flash",
        "turns_factor": "1.5",
        "baseline_subdir": "openrouter/glm-5.3-flash/",
    }


def test_preflight_falls_back_to_claude(tmp_path: Path) -> None:
    got = _run_creds(tmp_path, CLAUDE_CODE_OAUTH_TOKEN="t")
    assert (got["provider"], got["model"], got["turns_factor"], got["baseline_subdir"]) == (
        "claude", "claude-haiku-5-5", "1.0", "")


def test_manual_claude_run_overrides_openrouter(tmp_path: Path) -> None:
    got = _run_creds(tmp_path, OPENROUTER_API_KEY="k", CLAUDE_CODE_OAUTH_TOKEN="t", REQUESTED="claude")
    assert got["provider"] == "claude"


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"REQUESTED": "openrouter", "CLAUDE_CODE_OAUTH_TOKEN": "t"},
        {"FORK_PR": "true", "OPENROUTER_API_KEY": "k"},
    ],
)
def test_preflight_without_usable_credentials(tmp_path: Path, env: dict[str, str]) -> None:
    assert _run_creds(tmp_path, **env) == {"has_credentials": "false"}


def test_eval_jobs_get_only_the_providers_credentials() -> None:
    wf = _wf()
    for name in ("pr-eval", "full-eval"):
        for step in wf["jobs"][name]["steps"]:
            env = step.get("env") or {}
            for var, value in env.items():
                if "secrets.CLAUDE_CODE_OAUTH_TOKEN" in str(value):
                    assert "provider == 'claude'" in str(value), (name, step.get("name"), var)
                if "secrets.OPENROUTER_API_KEY" in str(value) and var != "OPENROUTER_API_KEY":
                    raise AssertionError((name, step.get("name"), var))


def test_openrouter_jobs_report_spend_and_smoke() -> None:
    wf = _wf()
    for name in ("pr-eval", "full-eval"):
        names = [s.get("name", "") for s in wf["jobs"][name]["steps"]]
        assert "Spend before (OpenRouter key)" in names
        assert "Spend after (OpenRouter key)" in names
        assert "Smoke test (one OpenRouter session)" in names
    assert "--warn-drift 0.25" in _job_text(wf["jobs"]["full-eval"])


def test_spend_summary(tmp_path: Path) -> None:
    import json
    import sqlite3
    import subprocess
    import sys

    (tmp_path / "before.json").write_text(json.dumps({"usage": 1.0, "limit": 50, "limit_remaining": 49}))
    (tmp_path / "after.json").write_text(json.dumps({"usage": 1.84, "limit": 50, "limit_remaining": 48.16}))
    runs = tmp_path / "runs"
    runs.mkdir()
    conn = sqlite3.connect(runs / "eval.db")
    conn.execute("CREATE TABLE runs (total_cost_usd REAL)")
    conn.executemany("INSERT INTO runs VALUES (?)", [(0.7,), (0.63,)])
    conn.commit()
    conn.close()
    out = subprocess.run(
        [sys.executable, "-I", str(_REPO / "scripts" / "openrouter-ci.py"), "summary",
         str(tmp_path / "before.json"), str(tmp_path / "after.json"), str(runs),
         "--warn-drift", "0.25", "--out", str(tmp_path / "spend.md")],
        capture_output=True, text=True, check=True,
    )
    md = (tmp_path / "spend.md").read_text()
    assert "| 0.84 |" in md and "| 1.33 |" in md
    assert "::warning::" in out.stdout  # 1.33 vs 0.84 is 58% apart


def test_full_job_runs_both_arms_and_uploads_candidate_baseline() -> None:
    text = _job_text(_wf()["jobs"]["full-eval"])
    assert '--arms "${ARMS}"' in text
    assert "'treatment,baseline'" in text
    assert "candidate-baseline" in text
    assert "baseline update" in text


def test_missing_credentials_reported_not_run() -> None:
    text = _WORKFLOW.read_text()
    assert "not run: no credentials" in text


def test_manual_dispatch_inputs() -> None:
    wf = _wf()
    on = wf.get("on") or wf.get(True)  # PyYAML parses bare `on` as True
    inputs = on["workflow_dispatch"]["inputs"]
    assert {"model", "runs", "allow_opus"} <= set(inputs)
    assert "claude-opus-5-5" in inputs["model"]["options"]
    assert "schedule" in on


def test_deleted_or_renamed_skill_dirs_are_ignored() -> None:
    # Regression (PR #13): a PR that renamed skills/robotframework-appium-skill/
    # to skills/rf-appium/ made preflight request evals for the old dir name.
    res = _map(
        [
            "skills/robotframework-appium-skill/SKILL.md",
            "plugins/rf-agentskills/skills/appium/SKILL.md",
            "plugins/rf-core/evals/triggers/rf-keyword-builder.yaml",
            "plugins/rf-web/skills/rf-browser/SKILL.md",
        ],
        changed={"skills/robotframework-appium-skill/SKILL.md"},
    )
    assert "robotframework-appium-skill" not in res.skills
    assert "appium" not in res.skills
    assert "rf-browser" in res.skills
    assert not ({"robotframework-appium-skill", "rf-keyword-builder"} & res.trigger_skills)
    assert any("not shipped" in r for r in res.reasons)


# --- fork PRs never run live evals (content-security-scanning, task 5.6) --------

_EVAL_SECRETS = (
    "secrets.CLAUDE_CODE_OAUTH_TOKEN",
    "secrets.ANTHROPIC_API_KEY",
    "secrets.OPENROUTER_API_KEY",
)


def _triggers(wf: dict) -> set[str]:  # type: ignore[type-arg]
    on = wf.get("on", wf.get(True))
    return set(on) if isinstance(on, dict) else {on} if isinstance(on, str) else set(on)


def test_live_evals_never_use_pull_request_target_or_workflow_run() -> None:
    """Those events run with secrets on fork code; no workflow that holds the
    eval secrets may use them."""
    for path in sorted((_REPO / ".github" / "workflows").glob("*.yml")):
        text = path.read_text()
        if any(s in text for s in _EVAL_SECRETS):
            assert not _triggers(yaml.safe_load(text)) & {"pull_request_target", "workflow_run"}, path.name


def test_fork_prs_have_no_credentials() -> None:
    wf = _wf()
    creds = next(s for s in wf["jobs"]["preflight"]["steps"] if s.get("id") == "creds")
    assert "head.repo.full_name != github.repository" in creds["env"]["FORK_PR"]
    assert creds["run"].lstrip().startswith('if [ "${FORK_PR}" = "true" ]; then\n  echo "has_credentials=false"')
    assert "github.event.pull_request.head.repo.full_name == github.repository" in wf["jobs"]["pr-eval"]["if"]
    assert _triggers(wf) == {"pull_request", "schedule", "workflow_dispatch"}


def test_trigger_evals_never_run_after_a_failed_doctor() -> None:
    # Run 42885585678: Doctor failed, the tiers were skipped, and the trigger
    # step (if: always()) went on spending.
    wf = _wf()
    for name in ("pr-eval", "full-eval"):
        steps = wf["jobs"][name]["steps"]
        assert any(s.get("id") == "doctor" for s in steps)
        triggers = next(s for s in steps if s.get("id") == "triggers")
        assert "steps.doctor.outcome == 'success'" in triggers["if"]


def _run_select_legs(tmp_path: Path, plugins: list[str], **env: str) -> list[dict[str, str]]:
    """Run the preflight select step's leg builder over all-plugins legs."""
    import json
    import os
    import subprocess

    wf = _wf()
    step = next(s for s in wf["jobs"]["preflight"]["steps"] if s.get("id") == "select")
    script = step["run"].split("<<'PY'\n", 1)[1].rsplit("PY", 1)[0]
    legs = tmp_path / "legs"
    legs.mkdir()
    for plugin in plugins:
        (legs / f"{plugin}.env").write_text("run_evals=true\nfull_tier=true\nskills=\n")
    base = {"PATH": os.environ["PATH"], **{k: str(v) for k, v in wf["env"].items()}}
    out = subprocess.run(["python3", "-I", "-c", textwrap.dedent(script), str(legs)],
                         env={**base, **env}, capture_output=True, text=True, check=True).stdout
    values = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    return json.loads(values["matrix"])


_DESKTOP_OVERRIDE = '{"rf-desktop": "2.0"}'


def test_a_plugin_can_get_its_own_openrouter_turn_factor(tmp_path: Path) -> None:
    legs = _run_select_legs(tmp_path, ["rf-api", "rf-desktop"], PROVIDER="openrouter", DEFAULT_FACTOR="1.5",
                            OPENROUTER_TURNS_FACTORS=_DESKTOP_OVERRIDE)
    assert {leg["plugin"]: leg["turns_factor"] for leg in legs} == {"rf-api": "1.5", "rf-desktop": "2.0"}


def test_no_plugin_overrides_the_openrouter_turn_factor(tmp_path: Path) -> None:
    legs = _run_select_legs(tmp_path, ["rf-api", "rf-desktop"], PROVIDER="openrouter", DEFAULT_FACTOR="1.5")
    assert {leg["turns_factor"] for leg in legs} == {"1.5"}


def test_claude_runs_ignore_the_openrouter_turn_factors(tmp_path: Path) -> None:
    legs = _run_select_legs(tmp_path, ["rf-desktop"], PROVIDER="claude", DEFAULT_FACTOR="1.0",
                            OPENROUTER_TURNS_FACTORS=_DESKTOP_OVERRIDE)
    assert legs[0]["turns_factor"] == "1.0"


def test_plugins_input_limits_the_matrix(tmp_path: Path) -> None:
    legs = _run_select_legs(tmp_path, ["rf-api", "rf-core", "rf-desktop"], PROVIDER="openrouter",
                            DEFAULT_FACTOR="1.5", ONLY_PLUGINS="rf-desktop, rf-api")
    assert [leg["plugin"] for leg in legs] == ["rf-api", "rf-desktop"]


def test_eval_jobs_take_the_turn_factor_from_the_matrix_leg() -> None:
    wf = _wf()
    for name in ("pr-eval", "full-eval"):
        assert wf["jobs"][name]["env"]["TURNS_FACTOR"] == "${{ matrix.turns_factor }}"
