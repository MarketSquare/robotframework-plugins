#!/usr/bin/env node
// check_rf_environment.mjs — Check the Robot Framework environment at session start.
//
// Called by the SessionStart hook. Writes a diagnostic summary to stderr so the
// agent sees the environment state. Always exits 0 (informational only — never
// blocks session start).
//
// Interpreter resolution is shared with the validation hooks (_python_env.mjs):
// VIRTUAL_ENV -> <cwd>/.venv -> python_runtime.json -> python3/python. The
// SessionStart event's `cwd` selects the project (process cwd when it has none);
// a missing, empty or malformed event produces no output. Install advice follows the rf-setup skill (project environment,
// `uv add …`); it never recommends `pip install` or `rfbrowser init`.
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import {
  PROBE_TIMEOUT_MS,
  findInterpreterWith,
  findRobotcode,
  firstPython,
  projectRoot,
  spawnOptions,
  versionAtLeast,
} from "./_python_env.mjs";

const ROBOTCODE_MIN = "2.8";
const MARKETPLACE = "robotframework-plugins";

// Libraries a technology plugin covers (detection signals only; the install
// steps live in each library's skill). Import name, label, plugin, skill.
const LIBRARIES = [
  ["Browser", "Browser Library", "rf-web", "rf-browser"],
  ["SeleniumLibrary", "SeleniumLibrary", "rf-web", "rf-selenium"],
  ["RequestsLibrary", "RequestsLibrary", "rf-api", "rf-requests"],
  ["REST", "RESTinstance", "rf-api", "rf-restinstance"],
  ["AppiumLibrary", "AppiumLibrary", "rf-mobile", "rf-appium"],
  ["PlatynUI", "PlatynUI", "rf-desktop", "rf-platynui"],
];

// Whether the skill is already there: in this plugin tree (the rf-agentskills
// bundle, or a file-mode install's support folder next to the skills), or in
// a sibling plugin of the same marketplace cache. Best effort; unknown = no.
function skillPresent(plugin, skill) {
  const root = process.env.CLAUDE_PLUGIN_ROOT;
  if (!root) return false;
  const candidates = [
    join(root, "skills", skill),
    join(root, "..", "skills", skill),
    join(root, "..", plugin, "skills", skill),
    join(root, "..", "..", plugin),
  ];
  return candidates.some((p) => existsSync(p));
}

// The command that installs a plugin in the agent running this hook, judged by
// where the agent put the plugin; a file-mode install gets the installer.
function installCommand(plugin) {
  const root = (process.env.CLAUDE_PLUGIN_ROOT ?? "").replace(/\\/g, "/");
  if (root.includes("/.copilot/")) return `copilot plugin install ${plugin}@${MARKETPLACE}`;
  if (root.includes("/.codex/")) return `codex plugin add ${plugin}@${MARKETPLACE}`;
  if (root.includes("/.claude/plugins/")) return `/plugin install ${plugin}@${MARKETPLACE}`;
  return "uvx robotframework-plugins install (adds the plugins for the libraries the project declares)";
}

// Missing, empty or malformed event -> no output (the hook never blocks).
let event = null;
try {
  event = JSON.parse(readFileSync(0, "utf-8"));
} catch {
  process.exit(0);
}
if (!event || typeof event !== "object" || Array.isArray(event)) process.exit(0);
const cwd = projectRoot(event);

const found = [];
const missing = [];

function pythonImportExists(py, importName) {
  if (!py) return false;
  const r = spawnSync(py, ["-c", `import ${importName}`], {
    ...spawnOptions(PROBE_TIMEOUT_MS),
    stdio: "ignore",
  });
  return r.status === 0;
}

function check(ok, label) {
  (ok ? found : missing).push(label);
  return ok;
}

process.stderr.write("=== Robot Framework Environment Check ===\n");

// Prefer the interpreter that has Robot Framework; else the first one that runs.
const py = findInterpreterWith("robot", cwd) ?? firstPython(cwd);

process.stderr.write("\nCore:\n");
check(py !== null, "python3");
const rfOk = pythonImportExists(py, "robot");
check(rfOk, "robotframework");
let rfVersion = "not installed";
if (rfOk) {
  const r = spawnSync(py, ["-c", "import robot; print(robot.version.VERSION)"], {
    ...spawnOptions(PROBE_TIMEOUT_MS),
    encoding: "utf-8",
  });
  if (r.status === 0) rfVersion = (r.stdout ?? "").trim() || rfVersion;
}
process.stderr.write(`  Robot Framework version: ${rfVersion}\n`);
if (py) process.stderr.write(`  Interpreter: ${py}\n`);

process.stderr.write("\nrobotcode (required by rf-core):\n");
const rc = findRobotcode(cwd, { withVersion: true });
const rcOk = rc !== null && versionAtLeast(rc.version, ROBOTCODE_MIN);
check(rcOk, `robotcode[all]>=${ROBOTCODE_MIN}`);
if (rcOk) {
  process.stderr.write(`  robotcode ${rc.version}: available (${rc.exe}); errors are checked on every .robot/.resource edit\n`);
} else {
  process.stderr.write(
    (rc
      ? `  robotcode ${rc.version ?? "(unknown version)"} is older than ${ROBOTCODE_MIN} (robotcode doc needs ${ROBOTCODE_MIN}): `
      : "  robotcode: not installed — ") +
      "keyword lookup (robotcode doc), result analysis (robotcode results) and the error check on edit " +
      "need it. Install it into the project environment: uv add --dev \"robotcode[all]>=2.8\" " +
      "(see the rf-setup skill). Recommended companion plugin: robotcode@robotframework-agent-plugins.\n",
  );
}
const robocopOk = check(pythonImportExists(py, "robocop") ||
  findInterpreterWith("robocop", cwd) !== null, "robotframework-robocop");
process.stderr.write(
  robocopOk
    ? "  Robocop: available (deprecation and formatting advice on edit)\n"
    : "  Robocop: not installed — deprecation and formatting advice on edit is disabled " +
        "(it comes with robotcode[all])\n",
);

// Test libraries: report the ones the project has, and the plugin for each.
const plugins = new Map();
for (const [importName, label, plugin, skill] of LIBRARIES) {
  if (pythonImportExists(py, importName)) {
    found.push(label);
    if (!plugins.has(plugin)) plugins.set(plugin, { labels: [], present: true });
    const entry = plugins.get(plugin);
    entry.labels.push(label);
    entry.present = entry.present && skillPresent(plugin, skill);
  }
}
if (plugins.size) {
  process.stderr.write("\nTest libraries and their plugins:\n");
  for (const [plugin, { labels, present }] of plugins) {
    process.stderr.write(
      present
        ? `  ${labels.join(", ")}: covered by plugin ${plugin} (installed)\n`
        : `  ${labels.join(", ")}: covered by plugin ${plugin}, not installed. Install: ${installCommand(plugin)}\n`,
    );
  }
}

process.stderr.write("\n--- Summary ---\n");
if (found.length) {
  process.stderr.write(`Available: ${found.join(", ")}\n`);
}
if (missing.length) {
  process.stderr.write(`Not installed: ${missing.join(", ")}\n`);
  process.stderr.write(
    "\nInstall only what the project needs, into the project environment. " +
      "See the rf-setup skill for the full steps (uv, venv, poetry):\n",
  );
  process.stderr.write("  uv add robotframework                        # core\n");
  process.stderr.write("  uv add --dev \"robotcode[all]>=2.8\"         # required: robotcode CLI + Robocop\n");
  process.stderr.write(
    "  Test libraries: the library's own skill gives its install steps " +
      "(plugins rf-web, rf-api, rf-mobile, rf-desktop).\n",
  );
} else {
  process.stderr.write("All checked packages are installed.\n");
}
process.stderr.write("=== End Environment Check ===\n");

process.exit(0);
