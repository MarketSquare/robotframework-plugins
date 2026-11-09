# Installing RESTinstance

Commands are in uv form. For a new environment, Poetry and venv + pip forms, and the general troubleshooting (wrong interpreter, PEP 668, old Python), see `rf-setup` (plugin `rf-core`): `uv add <pkg>` is `poetry add <pkg>` (pip alternative: `.venv/bin/python -m pip install <pkg>`), and `uv run <cmd>` is `poetry run <cmd>` or `.venv/bin/<cmd>`. Versions and floors checked on PyPI 2026-09-26.

```bash
uv add RESTinstance
```

- Package `RESTinstance` (1.8.0, **Python ≥ 3.11**). Module `REST`.
- Importing it prints `SyntaxWarning: invalid escape sequence` lines from its `flex` dependency on Python 3.12+. They are harmless.
- Verify: `uv run python -c "import REST"`.
