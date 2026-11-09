# Installing SeleniumLibrary

Commands are in uv form. For a new environment, Poetry and venv + pip forms, and the general troubleshooting (wrong interpreter, PEP 668, old Python), see `rf-setup` (plugin `rf-core`): `uv add <pkg>` is `poetry add <pkg>` (pip alternative: `.venv/bin/python -m pip install <pkg>`), and `uv run <cmd>` is `poetry run <cmd>` or `.venv/bin/<cmd>`. Versions and floors checked on PyPI 2026-09-26.

```bash
uv add robotframework-seleniumlibrary
```

- Package `robotframework-seleniumlibrary` (6.9, Python ≥ 3.10). Module `SeleniumLibrary`. It pulls in `selenium` 4.x.
- After installing: a real browser (Chrome, Firefox, Edge) must be installed. **Selenium Manager** (built into selenium ≥ 4.6) downloads a matching driver on first use. Don't install chromedriver by hand unless the machine is offline.
- Offline or locked-down CI: preinstall the driver and put it on PATH; Selenium Manager then finds it.
- Verify: `uv run python -c "import SeleniumLibrary"`, then a one-line `Open Browser    about:blank    headlesschrome` test.
