"""Run — one concrete `(task, arm, replicate)` invocation outcome."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .task import DEFAULT_MODEL, Provider, provider_for


class RunUsage(BaseModel):
    """Usage numbers from the stream-json ``result`` line (design D5)."""

    model_config = ConfigDict(frozen=True)

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    num_turns: int = 0
    duration_ms: int = 0
    total_cost_usd: float = 0.0
    is_error: bool = False
    #: The ``result`` line's ``subtype`` (``success``, ``error_max_turns``, ...).
    subtype: str = ""
    #: Models named in the result's ``modelUsage``.
    models: tuple[str, ...] = ()
    #: ``reported`` (Claude Code's ``total_cost_usd``) or ``priced`` (the
    #: harness's estimate from provider list prices).
    cost_source: str = "reported"

    @property
    def hit_turn_limit(self) -> bool:
        return self.subtype == "error_max_turns"

    @property
    def total_input_tokens(self) -> int:
        """Input tokens including cache creation and cache reads."""
        return (
            self.input_tokens + self.cache_creation_input_tokens + self.cache_read_input_tokens
        )


class Run(BaseModel):
    """Record of a single Claude Code session invocation.

    A Run is immutable once created; its artifacts live under
    ``artifacts_dir`` and must not be rewritten after the fact.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    profile_name: str = Field(min_length=1)
    started_at: datetime
    finished_at: datetime | None = None
    exit_code: int | None = None
    session_jsonl_path: Path | None = None
    artifacts_dir: Path
    workspace_dir: Path | None = None
    model: str = DEFAULT_MODEL
    #: Empty on older records: derived from ``model`` (``effective_provider``).
    provider: str = ""
    #: The run-time ``--max-turns-factor`` the session ran with.
    turns_factor: float = 1.0
    timed_out: bool = False
    #: ``treatment`` or ``baseline`` (older records: derived from profile name).
    arm: str = ""
    replicate: int = 0
    usage: RunUsage | None = None
    #: Set when the run is not trustworthy (arm leak, isolation violation,
    #: budget, runner error).
    error: str | None = None

    @field_validator("artifacts_dir", "workspace_dir", "session_jsonl_path")
    @classmethod
    def _absolute(cls, value: Path | None) -> Path | None:
        # Graders run subprocesses with ``cwd=<workspace>``; a relative path
        # (e.g. from ``--output eval/runs/x``) would then resolve against the
        # wrong directory (robot exit 252, empty grader output).
        return value.absolute() if value is not None else None

    @property
    def effective_arm(self) -> str:
        if self.arm:
            return self.arm
        return "baseline" if self.profile_name in ("baseline", "control") else "treatment"

    @property
    def effective_provider(self) -> Provider:
        return "openrouter" if self.provider == "openrouter" else provider_for(self.model)

    @property
    def effective_workspace(self) -> Path:
        """Directory where the agent's file outputs live.

        Graders resolve relative paths against this. Defaults to
        ``artifacts_dir`` when no fixture workspace was provisioned.
        """
        return self.workspace_dir or self.artifacts_dir

    def duration_seconds(self) -> float | None:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    def succeeded(self) -> bool:
        """A run 'succeeded' when the subprocess exited cleanly.

        This does **not** mean the skill produced correct output — that
        is what the grader is for.
        """

        return self.exit_code == 0 and not self.timed_out and self.error is None
