#!/usr/bin/env node
// maybe_remind_robot_tests.mjs — Conditional Stop hook.
//
// Reads the Claude Code Stop event JSON on stdin, inspects the session
// transcript for any tool result that wrote a .robot or .resource file,
// and only emits an additionalContext reminder ("run robot, inspect
// report.html") when at least one such file was touched. Sessions that
// produced only non-RF artifacts get no injection, and neither do sessions
// that ran Robot Framework (`robot`, `python -m robot`, `robotcode robot`,
// dry runs included) after their last .robot/.resource write.
//
// Cross-platform port of maybe_remind_robot_tests.sh. Reads the
// transcript via streaming-ish chunking so very long sessions don't
// blow up memory.
//
// Schema:
//   stdin  — Claude Code Stop event JSON. Includes transcript_path.
//   stdout — Either empty (no reminder) or one JSON object with
//            hookSpecificOutput.additionalContext.
//   exit   — Always 0.
import { readFileSync, existsSync, statSync, openSync, readSync, closeSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

let raw = "";
try { raw = readFileSync(0, "utf-8"); } catch { process.exit(0); }
if (!raw) process.exit(0);

let event;
try { event = JSON.parse(raw); } catch { process.exit(0); }

// Break the Stop-hook loop. Claude Code sets `stop_hook_active` when this
// Stop fires as a continuation of a previous Stop-hook block; emitting any
// model-facing output here would re-invoke the model and loop until the
// block cap. Always no-op in that state.
if (event?.stop_hook_active) process.exit(0);

const transcript = (event?.transcript_path ?? "").toString();
if (!transcript || !existsSync(transcript)) process.exit(0);

// Fire the reminder at most once per session. Without this, every later turn
// that touched a .robot file re-emits it (the noise the loop amplified). The
// marker is a tiny file in the OS temp dir keyed by session_id; all I/O is
// best-effort and must never break the (non-blocking) hook.
const sessionId = (event?.session_id ?? "").toString();
let marker = "";
if (sessionId) {
  const safe = sessionId.replace(/[^A-Za-z0-9._-]/g, "_");
  marker = join(tmpdir(), `rf-agentskills-reminded-${safe}`);
  try {
    if (existsSync(marker)) process.exit(0);
  } catch {
    // Can't stat the marker — fall through and emit (guard above prevents loops).
  }
}

// Pattern: `"file_path"  :  "...path.robot"` (or .resource). Matches the
// `grep -E` regex from the bash original. Whitespace optional between
// quotes and colon.
const FILE_PATH_RE = /"file_path"\s*:\s*"[^"]*\.(?:robot|resource)"/gi;
// A Bash tool call's `"command": "…"` (JSON string, escapes kept).
const COMMAND_RE = /"command"\s*:\s*"((?:[^"\\]|\\.)*)"/g;
// Robot Framework run at a command position: start, after ; & | ( or a
// `uv/poetry/pipenv run`, optionally with a path (`.venv/bin/robot`).
const RF_RUN_RE = new RegExp(
  String.raw`(?:^|[;&|(]\s*|\b(?:uv|poetry|pipenv)\s+run\s+)(?:[\w.~/\\-]*[/\\])?` +
    String.raw`(?:python3?(?:\.exe)?\s+-m\s+robot(?=\s|$)|robotcode(?:\.exe)?(?:\s+\S+)*?\s+robot\b|robot(?:\.exe)?(?=\s|$))`,
);
const CARRY = 4096;

// Offsets of the last .robot/.resource file_path and the last Robot
// Framework run command in the transcript (-1 when absent).
function lastWriteAndRun(path) {
  // The transcript is a JSONL file that can be tens of MB on long
  // sessions. Read in 64 KB chunks rather than slurping it all.
  const size = (() => { try { return statSync(path).size; } catch { return 0; } })();
  const found = { write: -1, run: -1 };
  if (!size) return found;
  const BUF = Buffer.alloc(65536);
  const fd = openSync(path, "r");
  let pos = 0;
  let carry = "";
  try {
    while (pos < size) {
      const n = readSync(fd, BUF, 0, BUF.length, pos);
      if (n <= 0) break;
      // Stitch the boundary with the previous chunk so we don't miss a
      // match split across the seam (offsets are approximate, in chars).
      const chunk = carry + BUF.slice(0, n).toString("utf-8");
      const base = pos - carry.length;
      for (const m of chunk.matchAll(FILE_PATH_RE)) found.write = Math.max(found.write, base + m.index);
      for (const m of chunk.matchAll(COMMAND_RE)) {
        if (RF_RUN_RE.test(m[1])) found.run = Math.max(found.run, base + m.index);
      }
      carry = chunk.length > CARRY ? chunk.slice(-CARRY) : chunk;
      pos += n;
    }
  } finally {
    try { closeSync(fd); } catch {}
  }
  return found;
}

const { write: lastWrite, run: lastRun } = lastWriteAndRun(transcript);
if (lastWrite < 0) process.exit(0);
// The suite already ran (or dry-ran) after the last write: nothing to remind.
if (lastRun > lastWrite) process.exit(0);

const payload = {
  hookSpecificOutput: {
    hookEventName: "Stop",
    additionalContext: [
      "Robot Framework artifacts detected this session. Recommended next steps:",
      '\n  1. Run the affected tests where they can run: uv run robotcode robot -bl "<Suite.Test>" (or a whole directory)',
      "\n  2. Read the results: uv run robotcode results summary --failed, then robotcode results log --failed",
      " (not using uv: run robotcode from the project's .venv; see rf-setup)",
      "\n  3. Open results/report.html for the rendered report.",
    ].join(""),
  },
};

// Record that this session has been reminded (best-effort).
if (marker) {
  try { writeFileSync(marker, ""); } catch { /* ignore — never break the hook */ }
}

process.stdout.write(JSON.stringify(payload) + "\n");
process.exit(0);
