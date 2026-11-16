# sut-minimal

A small Robot Framework project: a shared resource file, a few test files, a
sample `output.xml` and mocked API data in `data/`. No browser or network
dependency.

Run the smoke test:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
robot tests/example.robot
```
