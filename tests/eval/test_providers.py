"""OpenRouter provider tier (openrouter-ci-eval-tier, spec eval-model-providers).

A fake ``claude`` executable records its argv and environment and prints a
canned stream-json result, so no model is ever called.
"""

from __future__ import annotations

import dataclasses
import json
import sqlite3
import stat
import sys
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from rf_skill_eval.application.baseline import baselines_dir_for, build_tier_baseline
from rf_skill_eval.application.batch import BatchExecutor, Budget, check_runtime_model, plan_batch
from rf_skill_eval.application.catalog import load_task_file
from rf_skill_eval.application.gate import gate_tasks
from rf_skill_eval.application.staging import staged_tree
from rf_skill_eval.cli import _resolve_provider, app
from rf_skill_eval.domain.pricing import PROVIDER_PRICES, priced_cost
from rf_skill_eval.domain.profile import Profile
from rf_skill_eval.domain.results import aggregate_replicates
from rf_skill_eval.domain.run import RunUsage
from rf_skill_eval.domain.task import (
    DEEPSEEK_FLASH_MODEL,
    OPENROUTER_MODELS,
    Task,
    provider_for,
)
from rf_skill_eval.errors import AuthConfigError, ModelNotAllowedError
from rf_skill_eval.infrastructure.persistence.sqlite_repo import SqliteRunRepository
from rf_skill_eval.infrastructure.runner.claude_code_runner import (
    OPENROUTER_BASE_URL,
    ClaudeCodeRunner,
)
from rf_skill_eval.infrastructure.telemetry.session_parser import parse_result_usage
from rf_skill_eval.reporting.eval_report import build_report, render_markdown
from rf_skill_eval.scoring.rubric import RubricGrader

from .results_factory import make_result

_REPO = Path(__file__).resolve().parents[2]
_PLUGIN = staged_tree(_REPO / "plugins")
DS = DEEPSEEK_FLASH_MODEL
FAKE_KEY = "fake-openrouter-key-for-tests-never-stored"
cli = CliRunner()

_FAKE_CLAUDE = """#!{python}
import json, os, sys
keys = ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "CLAUDE_CODE_SUBAGENT_MODEL")
record = {{"argv": sys.argv[1:], "env": {{k: os.environ.get(k) for k in keys}}}}
with open(os.environ["FAKE_CLAUDE_LOG"], "a") as fh:
    fh.write(json.dumps(record) + "\\n")
models = os.environ.get("FAKE_CLAUDE_MODELS", "").split(",")
print(json.dumps({{"type": "result", "subtype": os.environ.get("FAKE_CLAUDE_SUBTYPE", "success"),
                  "is_error": False, "num_turns": 3, "duration_ms": 10, "total_cost_usd": 0.4,
                  "usage": {{"input_tokens": 1000000, "output_tokens": 100000,
                            "cache_read_input_tokens": 5000000,
                            "cache_creation_input_tokens": 0}},
                  "modelUsage": {{m: {{}} for m in models if m}}}}))
"""


@pytest.fixture
def fake_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    exe = tmp_path / "bin" / "claude"
    exe.parent.mkdir()
    exe.write_text(_FAKE_CLAUDE.format(python=sys.executable))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("FAKE_CLAUDE_MODELS", DS)
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE_KEY)
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "claude-oauth-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-api-secret")
    (tmp_path / "fake-repo").mkdir()
    return exe


def _calls(tmp_path: Path) -> list[dict]:
    return [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]


def _task(**kw: object) -> Task:
    data: dict[str, object] = {
        "id": "narrow-or-01",
        "skill": "rf-browser",
        "prompt": "do it",
        "fixture": "sut-minimal",
        "max_turns": 14,
        "timeout_seconds": 60,
    }
    data.update(kw)
    task = Task.model_validate(data)
    return task.model_copy(update={"model": DS})


def _runner(tmp_path: Path, exe: Path) -> ClaudeCodeRunner:
    return ClaudeCodeRunner(
        claude_binary=str(exe),
        fixtures_root=_REPO / "eval" / "fixtures",
        repo_root=tmp_path / "fake-repo",
        plugin_root=_PLUGIN,
    )


# --- 1.1 model policy ------------------------------------------------------------


def test_openrouter_model_is_run_time_only() -> None:
    check_runtime_model(DS, allow_opus=False, max_cost_usd=None)
    with pytest.raises(ValueError, match="run-time only"):
        Task(id="t", skill="rf-browser", prompt="p", model=DS)


def test_unlisted_openrouter_model_names_the_permitted_ids() -> None:
    with pytest.raises(ModelNotAllowedError) as exc:
        check_runtime_model("z-ai/glm-5.3-flash", allow_opus=False, max_cost_usd=None)
    assert DS in str(exc.value)


def test_every_openrouter_model_has_a_price() -> None:
    assert set(PROVIDER_PRICES) == set(OPENROUTER_MODELS)


@pytest.mark.parametrize("key", ["turns_factor", "provider"])
def test_task_file_may_not_declare_run_time_settings(tmp_path: Path, key: str) -> None:
    path = tmp_path / "t.yaml"
    path.write_text(f"id: t\nskill: rf-browser\nprompt: p\n{key}: 1.5\n")
    with pytest.raises(ValueError, match="run-time setting"):
        load_task_file(path)


# --- 1.2 provider selection --------------------------------------------------------


def test_provider_is_derived_from_the_model() -> None:
    assert provider_for(DS) == "openrouter"
    assert provider_for("claude-haiku-5-5") == "anthropic"
    assert _resolve_provider(None, {DS}) == "openrouter"
    assert _resolve_provider(None, {"claude-haiku-5-5"}) == "anthropic"


@pytest.mark.parametrize(
    ("provider", "model"), [("openrouter", "claude-haiku-5-5"), ("anthropic", DS)]
)
def test_mismatched_provider_and_model_refused(provider: str, model: str) -> None:
    with pytest.raises(typer.Exit) as exc:
        _resolve_provider(provider, {model})
    assert exc.value.exit_code == 2


def test_cli_refuses_openrouter_with_a_claude_model() -> None:
    result = cli.invoke(
        app,
        ["run-batch", "--tier", "narrow", "--provider", "openrouter", "--model", "claude-haiku-5-5",
         "--output", "/nonexistent-never-written"],
    )
    assert result.exit_code == 2
    assert DS in result.stdout


def test_cli_without_openrouter_key_is_not_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    result = cli.invoke(
        app, ["run-batch", "--tier", "narrow", "--model", DS, "--output", "/nonexistent-never-written"]
    )
    assert result.exit_code == 2
    assert "OPENROUTER_API_KEY" in result.stdout


# --- 1.3 persistence ------------------------------------------------------------------


def test_runs_store_provider_and_factor_and_old_databases_migrate(tmp_path: Path) -> None:
    db = tmp_path / "eval.db"
    with SqliteRunRepository(db):
        pass
    # Turn it into a schema-2 database (no provider / turns_factor columns).
    conn = sqlite3.connect(db)
    conn.execute("ALTER TABLE runs DROP COLUMN provider")
    conn.execute("ALTER TABLE runs DROP COLUMN turns_factor")
    conn.execute("PRAGMA user_version = 2")
    conn.commit()
    conn.close()
    run = make_result("t", "treatment", 0, model=DS).run.model_copy(
        update={"provider": "openrouter", "turns_factor": 1.5}
    )
    with SqliteRunRepository(db) as repo:
        assert repo.schema_version == 3
        repo.save_run(run)
        stored = repo.load_run(run.id)
    assert stored is not None
    assert (stored.provider, stored.turns_factor, stored.model) == ("openrouter", 1.5, DS)


# --- 2.1 session environment ---------------------------------------------------------


def test_openrouter_session_env(tmp_path: Path, fake_claude: Path) -> None:
    out = tmp_path / "runs"
    run = _runner(tmp_path, fake_claude).execute(
        _task(), Profile.for_arm("treatment", out / "cfg"), out
    )
    assert run.error is None, run.error
    assert (run.provider, run.model) == ("openrouter", DS)
    env = _calls(tmp_path)[0]["env"]
    assert env["ANTHROPIC_BASE_URL"] == OPENROUTER_BASE_URL
    assert env["ANTHROPIC_AUTH_TOKEN"] == FAKE_KEY
    assert env["ANTHROPIC_API_KEY"] == ""
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] is None
    for alias in ("HAIKU", "SONNET", "OPUS"):
        assert env[f"ANTHROPIC_DEFAULT_{alias}_MODEL"] == DS
    assert env["CLAUDE_CODE_SUBAGENT_MODEL"] == DS


def test_claude_session_env_is_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fake")
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    env = ClaudeCodeRunner(fixtures_root=tmp_path, repo_root=tmp_path)._build_env(
        tmp_path, model="claude-haiku-5-5"
    )
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "fake"
    assert "ANTHROPIC_BASE_URL" not in env


def test_missing_openrouter_key_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fake")
    with pytest.raises(AuthConfigError, match="OPENROUTER_API_KEY"):
        ClaudeCodeRunner(fixtures_root=tmp_path, repo_root=tmp_path)._build_env(tmp_path, model=DS)


# --- 2.2 doctor ---------------------------------------------------------------------------


def test_doctor_checks_the_openrouter_key(monkeypatch: pytest.MonkeyPatch) -> None:
    pinged: list[str] = []
    monkeypatch.setattr(
        "rf_skill_eval.cli._claude_auth_ping",
        lambda _b, provider="anthropic": (pinged.append(provider) or True, "stubbed"),
    )
    monkeypatch.setattr("rf_skill_eval.cli.get_settings", lambda: _settings(openrouter=FAKE_KEY))
    result = cli.invoke(app, ["doctor", "--provider", "openrouter"])
    assert "OPENROUTER_API_KEY" in result.stdout
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in result.stdout
    assert FAKE_KEY not in result.stdout
    assert pinged in ([], ["openrouter"])


def test_doctor_without_openrouter_key_fails_the_row(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("rf_skill_eval.cli.get_settings", lambda: _settings(openrouter=None))
    result = cli.invoke(app, ["doctor", "--provider", "openrouter"])
    row = next(line for line in result.stdout.splitlines() if "OPENROUTER_API_KEY" in line)
    assert "FAIL" in row


def _settings(*, openrouter: str | None):  # type: ignore[no-untyped-def]
    from rf_skill_eval.config import Settings

    return Settings(openrouter_api_key=openrouter, claude_code_oauth_token=None, anthropic_api_key=None)


# --- 2.3 provider_model -------------------------------------------------------------------


def test_usage_records_models_and_subtype(tmp_path: Path) -> None:
    stream = tmp_path / "s.jsonl"
    stream.write_text(json.dumps({
        "type": "result", "subtype": "error_max_turns", "usage": {},
        "modelUsage": {DS: {}, "claude-haiku-5-5": {}},
    }) + "\n")
    usage = parse_result_usage(stream)
    assert usage is not None
    assert usage.models == ("claude-haiku-5-5", DS)
    assert usage.hit_turn_limit


def test_unexpected_model_makes_the_run_incomplete(
    tmp_path: Path, fake_claude: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_CLAUDE_MODELS", f"{DS},claude-haiku-5-5")
    out = tmp_path / "runs"
    run = _runner(tmp_path, fake_claude).execute(
        _task(), Profile.for_arm("treatment", out / "cfg"), out
    )
    assert run.error is not None
    assert run.error.startswith("provider_model:")
    assert "claude-haiku-5-5" in run.error


# --- 2.4 the key never reaches stored output ----------------------------------------------


def test_key_never_stored(tmp_path: Path, fake_claude: Path) -> None:
    out = tmp_path / "runs"
    runner = _runner(tmp_path, fake_claude)
    with SqliteRunRepository(out / "eval.db") as repo:
        outcome = BatchExecutor(runner, RubricGrader(), repo, out).execute(
            plan_batch([_task()], ("treatment", "baseline"), 1)
        )
    (out / "report.md").write_text(render_markdown(build_report(outcome.results)))
    leaks = [
        p for p in out.rglob("*")
        if p.is_file() and FAKE_KEY.encode() in p.read_bytes()
    ]
    assert leaks == []


# --- 3.1 priced cost ------------------------------------------------------------------------


def test_priced_cost_arithmetic() -> None:
    cost = priced_cost(
        DS,
        input_tokens=1_000_000,
        cache_read_input_tokens=5_000_000,
        cache_creation_input_tokens=0,
        output_tokens=100_000,
    )
    p = PROVIDER_PRICES[DS]
    assert cost == pytest.approx(p.input + 5 * p.cache_read + 0.1 * p.output)


def test_openrouter_run_is_priced_not_reported(tmp_path: Path, fake_claude: Path) -> None:
    out = tmp_path / "runs"
    run = _runner(tmp_path, fake_claude).execute(
        _task(), Profile.for_arm("treatment", out / "cfg"), out
    )
    assert run.usage is not None
    assert run.usage.cost_source == "priced"
    assert run.usage.total_cost_usd == pytest.approx(
        priced_cost(DS, input_tokens=1_000_000, cache_read_input_tokens=5_000_000,
                    cache_creation_input_tokens=0, output_tokens=100_000)
    )
    assert run.usage.total_cost_usd != pytest.approx(0.4)  # Claude Code's figure


def test_budget_uses_priced_cost() -> None:
    # Claude Code said $3 per run ($30 in all); priced, they cost $0.09 each.
    budget = Budget(cap_usd=2.0)
    for i in range(10):
        r = _or_result(i, stopped=False).run  # type: ignore[attr-defined]
        budget.charge(r.model_copy(update={"usage": r.usage.model_copy(update={"total_cost_usd": 0.09})}))
    assert not budget.exhausted
    assert budget.spent_usd == pytest.approx(0.9)


# --- 3.3 / 3.4 reports and turn limits --------------------------------------------------------


def _or_result(idx: int, *, stopped: bool) -> object:
    r = make_result("t", "treatment", idx, model=DS)
    usage = (r.run.usage or RunUsage()).model_copy(
        update={"cost_source": "priced", "subtype": "error_max_turns" if stopped else "success"}
    )
    run = r.run.model_copy(update={"usage": usage, "provider": "openrouter", "turns_factor": 1.5})
    return dataclasses.replace(r, run=run)


def test_report_labels_estimates_and_turn_limit_stops() -> None:
    results = [_or_result(0, stopped=True), _or_result(1, stopped=True), _or_result(2, stopped=False)]
    md = render_markdown(build_report(results))  # type: ignore[arg-type]
    assert "estimated cost (OpenRouter list prices)" in md
    assert "(2 at limit)" in md
    assert "(est.)" in md
    assert "**turn-limit stops:** 2" in md


def test_scaled_turn_limit(tmp_path: Path, fake_claude: Path) -> None:
    out = tmp_path / "runs"
    task = _task().model_copy(update={"turns_factor": 1.5})
    run = _runner(tmp_path, fake_claude).execute(task, Profile.for_arm("treatment", out / "cfg"), out)
    argv = _calls(tmp_path)[0]["argv"]
    assert argv[argv.index("--max-turns") + 1] == "21"
    assert argv[argv.index("--model") + 1] == DS
    assert run.turns_factor == 1.5


def test_turn_limit_factor_is_bounded() -> None:
    result = cli.invoke(app, ["run-batch", "--max-turns-factor", "3.5", "--model", DS])
    assert result.exit_code == 2


# --- 4.1 / 4.2 per-model baselines ---------------------------------------------------------------


def test_baseline_dir_per_model(tmp_path: Path) -> None:
    assert baselines_dir_for(tmp_path, "claude-haiku-5-5") == tmp_path
    assert baselines_dir_for(tmp_path, DS) == tmp_path / "openrouter" / "deepseek-v4.1-flash"
    assert baselines_dir_for(tmp_path, None) == tmp_path


def _or_baseline(factor: float) -> dict:
    results = [_or_result(i, stopped=False) for i in range(3)]
    results = [
        dataclasses.replace(r, run=r.run.model_copy(update={"turns_factor": factor}))  # type: ignore[attr-defined]
        for r in results
    ]
    return build_tier_baseline(
        aggregate_replicates(results),  # type: ignore[arg-type]
        tier="narrow",
        task_hashes={"t": "h1"},
        harness_version="0",
        claude_code_version="x",
    )


def test_baseline_entries_record_provider_and_factor() -> None:
    entry = _or_baseline(1.5)["entries"]["t|treatment"]
    assert (entry["provider"], entry["turns_factor"], entry["cost_source"]) == ("openrouter", 1.5, "priced")


def test_turn_limit_factor_mismatch_needs_rebaseline() -> None:
    current = aggregate_replicates([_or_result(i, stopped=False) for i in range(3)])  # type: ignore[arg-type]
    report = gate_tasks(current, _or_baseline(1.0), {"t": "h1"})
    assert report.status == "rebaseline-needed"
    assert any("turn-limit factor differs" in f.message for f in report.findings)
    assert gate_tasks(current, _or_baseline(1.5), {"t": "h1"}).status == "pass"


def test_gate_defaults_to_the_models_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evals = tmp_path / "evals"
    (evals / "tasks").mkdir(parents=True)
    monkeypatch.setattr("rf_skill_eval.cli._evals", lambda *parts, root=None: evals.joinpath(*parts))
    runs = tmp_path / "runs"
    with SqliteRunRepository(runs / "eval.db") as repo:
        for i in range(3):
            r = _or_result(i, stopped=False)
            repo.save_run(r.run)  # type: ignore[attr-defined]
            repo.save_scorecard(r.scorecard)  # type: ignore[attr-defined]
    target = evals / "baselines" / "openrouter" / "deepseek-v4.1-flash" / "narrow.json"
    result = cli.invoke(app, ["gate", "--runs-dir", str(runs)])
    # No baseline file yet: the gate looked for the DeepSeek one, not the Haiku one.
    assert not target.exists()
    assert result.exit_code == 3
    assert "no stored baseline entry" in result.stdout
