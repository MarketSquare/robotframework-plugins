# library-lending

Acceptance tests for the city library's lending service. The service runs in
memory (`sut/LibraryService.py`, a Robot Framework library with one fresh
instance per test); its business rules are in the module docstring. The
library's calendar starts on 2026-11-12, so due dates are fixed (`Set Today`
moves it).

- `tests/`: acceptance tests (none yet).
- `resources/`: shared keywords for the tests.
- `smoke/library_service.robot`: a technical check that the service library
  loads and lends a book.

`robot.toml` puts `resources/` and `sut/` on the python-path, so both are
imported by name. Run from this directory with robotcode, which reads
`robot.toml`:

```bash
robotcode robot              # the acceptance tests in tests/
robotcode robot smoke
```
