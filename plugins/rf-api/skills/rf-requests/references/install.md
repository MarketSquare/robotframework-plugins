# Installing RequestsLibrary

Commands are in uv form. For a new environment, Poetry and venv + pip forms, and the general troubleshooting (wrong interpreter, PEP 668, old Python), see `rf-setup` (plugin `rf-core`): `uv add <pkg>` is `poetry add <pkg>` (pip alternative: `.venv/bin/python -m pip install <pkg>`), and `uv run <cmd>` is `poetry run <cmd>` or `.venv/bin/<cmd>`. Versions and floors checked on PyPI 2026-09-26.

```bash
uv add robotframework-requests
```

- Package `robotframework-requests` (0.9.7). Module `RequestsLibrary`. No step after installing.
- Verify: `uv run python -c "import RequestsLibrary"`.
