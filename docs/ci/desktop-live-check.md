# rf-desktop live check

The CI runner has no desktop, so the eval grades rf-desktop's PlatynUI suites statically: `keywords_resolve` checks that every keyword exists, and `platynui_locators` rejects locators known to fail on a real desktop. Neither runs a suite. The live check does: on a Windows desktop, it runs the suites one eval run wrote, and the skill's example, against the real Calculator, and reports how many pass per tier and arm.

Run it by hand:

- before a release of `rf-desktop`;
- when the `sut-platynui` fixture README, the PlatynUI tasks or the locator guidance in `rf-platynui` change;
- when the static and the live picture may differ, for example after a PlatynUI upgrade.

It isn't part of CI, and it never writes baselines.

## Set up the Windows machine

You need Windows 10 or 11 with the Calculator app, a logged-in and unlocked desktop session, Python 3.12, uv and git.

```bat
git clone https://github.com/MarketSquare/robotframework-plugins C:\workspace\robotframework-plugins
cd /d C:\workspace\robotframework-plugins
uv venv --python 3.12 .venv-desktop
uv pip install --python .venv-desktop --prerelease allow robotframework==7.5.1 robotframework-PlatynUI==0.12.0.dev330 platynui-cli==0.12.0.dev330
```

These are the versions of the committed libdoc spec (`eval/fixtures/sut-platynui/specs/`). Check that PlatynUI sees Calculator: start it, then run

```bat
.venv-desktop\Scripts\platynui-cli.exe query "//control:Text[@Id='CalculatorResults']"
```

It prints the result display twice (once through the desktop tree, once through the application tree). If it prints nothing, Calculator isn't ready yet; a cold start can take more than 4 seconds.

## Get a run's artifacts

Download the full-run artifact of an eval run on any machine with `gh`, and copy it to the Windows machine:

```bash
gh run download <run-id> -R MarketSquare/robotframework-plugins -n skill-eval-full-rf-desktop-<run-id> -D live-check/<run-id>
```

The artifacts hold model-written suites. Treat them as untrusted: keep them in their own directory and run the script with `python -I` from the repository, not from inside the artifact directory.

## Run it

List what would run first. This collects the `tests/calculator.robot` of every PlatynUI session, plus the skill's example, and screens each one:

```bat
.venv-desktop\Scripts\python.exe -I scripts\desktop-live-check.py C:\workspace\live-check\<run-id> --list
```

Screening skips a suite, with a reason, when it:

- imports a library other than `PlatynUI.BareMetal`, `BuiltIn`, `Collections` or `String` (the skill's example may also import `Process`, to start Calculator);
- imports a variable file, or a resource outside its session's workspace;
- calls `Evaluate`, `Run Process`, `Start Process` (except the example), `Call Method` or an `Import …` keyword;
- has text that could run Python in an expression, such as `${{ }}`, `__`, `import` or `subprocess`.

Then run it in the desktop session:

```bat
.venv-desktop\Scripts\python.exe -I scripts\desktop-live-check.py C:\workspace\live-check\<run-id> --out C:\workspace\live-check\<run-id>-results
```

For each suite it closes Calculator, starts a fresh one (the example starts its own), waits until the result display answers a query, and runs `robot` with a 150-second limit (`--timeout`). Expect about half a minute per suite, since a locator that matches nothing waits 30 seconds before it fails; the 64 suites of 2026-11-12 took 32 minutes. Don't use the mouse or keyboard meanwhile: PlatynUI moves the real pointer.

### Over SSH

An SSH session can't see the desktop, so UI Automation finds nothing. Run the check through a scheduled task that runs in the logged-in session (`/it`). Create the task once, as the logged-in user:

```bat
schtasks /create /tn rf-desktop-live-check /tr C:\workspace\live-check\run.cmd /sc once /st 00:00 /sd 01.01.2030 /it /ru %USERNAME% /f
```

`C:\workspace\live-check\run.cmd` runs the check and marks the end of the output:

```bat
@echo off
cd /d C:\workspace\robotframework-plugins
.venv-desktop\Scripts\python.exe -I scripts\desktop-live-check.py C:\workspace\live-check\current --out C:\workspace\live-check\current-results > C:\workspace\live-check\out.txt 2>&1
echo DONE>> C:\workspace\live-check\out.txt
```

Then, over SSH: copy the artifacts to `C:\workspace\live-check\current`, delete the old `out.txt`, start the task with `schtasks /run /tn rf-desktop-live-check`, and wait until `out.txt` ends with `DONE`. The `/sd` date only keeps the task from running by itself; use the date format of the machine's locale.

## Read the report

```
display language: de_DE

tier     arm        suites passed skipped
example  example         1      1       0
narrow   baseline        3      0       0
narrow   treatment       5      1       0
...

most common failures:
   15  ElementNotFoundError: No UiNode found for UiNodeDescriptor query Q within timeout of N seconds.
```

- **display language** matters: `@Name` values follow it (a German desktop shows `Rechner`, `Eins`, `Gleich`). A suite that finds controls by English names passes on an English desktop only. Compare runs on the same language, or note it next to the numbers.
- **suites** counts the sessions that wrote the suite; a session that wrote nothing isn't listed.
- **passed** counts suites whose every test passed against the real Calculator.
- **most common failures** groups failure messages with quoted values and numbers replaced by `Q` and `N`.

Each suite's `output.xml`, `log.html` and `report.html` are under `--out`, in a folder named after the tier and session.

Put the per-arm pass counts next to the static ones (the candidate baseline's `keywords_resolve` and `platynui_locators` verdicts) in the PR that changes the fixture, the tasks or the skill. If a suite passes live and fails the static gate, or the other way round, look at it: either the static check needs a rule, or the live run hit something the eval can't see.

## Example results

On 2026-11-12, on German Windows 11 with PlatynUI 0.12.0.dev330, the 63 suites of runs 42887127109, 42993062842 and 43167186288 all failed as written: they used the old README's `@Name='Calculator'` window and `@AutomationId` locators. The skill's example passed. Those results led to the `@Id` locators in the fixture README and the `platynui_locators` check.
