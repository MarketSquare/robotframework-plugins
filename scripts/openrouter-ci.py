#!/usr/bin/env python3
"""CI helpers for the OpenRouter eval tier (openrouter-ci-eval-tier D7).

  openrouter-ci.py spend                  print the key's usage, limit and remaining credit (JSON)
  openrouter-ci.py smoke MODEL            one Claude Code session on MODEL; fail unless it answers
                                          and every request went to MODEL
  openrouter-ci.py summary BEFORE AFTER RUNS [--warn-drift F] [--out FILE]
                                          markdown: the key's spend during the job next to the
                                          harness's priced estimate; with --warn-drift, a
                                          ::warning:: when they differ by more than F (0.25 = 25%)

The key comes from OPENROUTER_API_KEY and is never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

KEY_URL = "https://openrouter.ai/api/v1/key"


def _key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set")
    return key


def spend() -> int:
    req = urllib.request.Request(KEY_URL, headers={"Authorization": f"Bearer {_key()}"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed https URL
        data = json.load(resp)["data"]
    print(json.dumps({k: data.get(k) for k in ("usage", "limit", "limit_remaining")}))
    return 0


def smoke(model: str) -> int:
    # The same session environment the harness gives an OpenRouter run.
    from rf_skill_eval.infrastructure.runner.claude_code_runner import openrouter_env

    with tempfile.TemporaryDirectory() as tmp:
        env = openrouter_env(os.environ.copy(), model)
        env["CLAUDE_CONFIG_DIR"] = tmp
        out = subprocess.run(
            ["claude", "-p", "Reply with the single word: ready", "--model", model,
             "--max-turns", "2", "--output-format", "json"],
            capture_output=True, text=True, timeout=120, env=env, cwd=tmp, check=False,
        )
    try:
        result = json.loads(out.stdout)
    except json.JSONDecodeError:
        print(f"::error::smoke session printed no JSON (exit {out.returncode}): {out.stderr[:300]}")
        return 1
    models = sorted((result.get("modelUsage") or {}).keys())
    print(f"result={str(result.get('result'))[:80]!r} is_error={result.get('is_error')} models={models}")
    if result.get("is_error") or not result.get("result"):
        print("::error::the OpenRouter smoke session failed")
        return 1
    if models and models != [model]:
        print(f"::error::the smoke session used {models}, not only {model}")
        return 1
    return 0


def _priced_total(runs_dir: Path) -> float:
    total = 0.0
    for db in runs_dir.rglob("eval.db"):
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
            total += conn.execute("SELECT COALESCE(SUM(total_cost_usd), 0) FROM runs").fetchone()[0]
    for results in runs_dir.rglob("trigger-results*.json"):
        total += float(json.loads(results.read_text("utf-8")).get("spent_usd") or 0.0)
    return total


def _load(path: Path) -> dict[str, float | None] | None:
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def summary(before: Path, after: Path, runs_dir: Path, warn_drift: float | None, out: Path | None) -> int:
    b, a = _load(before), _load(after)
    priced = _priced_total(runs_dir) if runs_dir.is_dir() else 0.0
    lines = ["### OpenRouter spend", ""]
    if b is None or a is None or b.get("usage") is None or a.get("usage") is None:
        lines.append(f"Key spend unavailable (spend file missing). Harness estimate: ${priced:.2f}.")
        spent = None
    else:
        spent = float(a["usage"] or 0) - float(b["usage"] or 0)
        lines += [
            "| | USD |",
            "|---|---|",
            f"| Key spend during this job (includes concurrent jobs) | {spent:.2f} |",
            f"| Harness estimate (OpenRouter list prices) | {priced:.2f} |",
            f"| Credit remaining on the key | {a.get('limit_remaining')} |",
        ]
    text = "\n".join(lines) + "\n"
    if out is not None:
        out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if warn_drift is not None and spent is not None and spent > 0:
        drift = abs(priced - spent) / spent
        if drift > warn_drift:
            print(
                f"::warning::priced estimate ${priced:.2f} differs from the key's spend "
                f"${spent:.2f} by {drift:.0%}; check PROVIDER_PRICES in src/rf_skill_eval/domain/pricing.py"
            )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("spend")
    smoke_p = sub.add_parser("smoke")
    smoke_p.add_argument("model")
    sum_p = sub.add_parser("summary")
    sum_p.add_argument("before", type=Path)
    sum_p.add_argument("after", type=Path)
    sum_p.add_argument("runs_dir", type=Path)
    sum_p.add_argument("--warn-drift", type=float, default=None)
    sum_p.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    if args.cmd == "spend":
        return spend()
    if args.cmd == "smoke":
        return smoke(args.model)
    return summary(args.before, args.after, args.runs_dir, args.warn_drift, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
