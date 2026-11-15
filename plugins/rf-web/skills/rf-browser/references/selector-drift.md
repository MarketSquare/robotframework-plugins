# Selector drift and flaky UI tests

Use this when a UI test fails because an element is not found, is hidden or has moved, or passes on some runs and fails on others.

## Decide what changed

1. Read the failing step. A locator that matches nothing points at the selector or the page. A timeout on an element that is visible in the log points at timing.
2. Measure before any rerun. Read the element's position and size with `Get BoundingBox` twice, a short time apart, and check whether an animation runs on it.
3. Rerun only after you know what changed. Running unchanged code again only shows that the result is unstable.
4. Decide who owns the cause:
   - the test: the selector is too weak, or the test does not wait for the state it needs;
   - the app: the element is missing, has moved or shows the wrong content.

   Only the app case becomes a defect report.

## Pick a locator that survives a redesign

- Prefer, in order: test ids (`[data-testid="save"]`), accessible roles (`role=button[name="Save"]`), short CSS, text (`text=Save`), XPath last. This is the order in `SKILL.md`.
- Check the match count with an operator in the getter, for example `Get Element Count    role=button[name="Save"]    ==    1`.
- Avoid long CSS paths and `nth-child` chains. They break when the markup changes.
- Read `references/locators.md` for the full order of locator strategies.

## Elements outside the viewport and menus

- A design-library menu can close when the page scrolls. Scroll the trigger into view first with `Scroll To Element`, then open the menu and click the option with no scroll in between.

## New and flaky tests

- To decide whether one failing test is flaky or a real defect, rerun that test three times with no code change. A test that passes on some runs and fails on others is flaky; one that fails every run points at the selector or the app.
- Quarantine a flaky test with a tag and a tracked issue. Do not add retries or longer timeouts to hide the cause.
