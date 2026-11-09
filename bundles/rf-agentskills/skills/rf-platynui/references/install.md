# Installing PlatynUI (preview)

Commands are in uv form. For a new environment, Poetry and venv + pip forms, and the general troubleshooting (wrong interpreter, PEP 668, old Python), see `rf-setup` (plugin `rf-core`): `uv add <pkg>` is `poetry add <pkg>` (pip alternative: `.venv/bin/python -m pip install <pkg>`), and `uv run <cmd>` is `poetry run <cmd>` or `.venv/bin/<cmd>`. Versions and floors checked on PyPI 2026-09-26.

Package `robotframework-PlatynUI`. The documented `PlatynUI.BareMetal` library exists only as a **pre-release** (Python ≥ 3.12). A plain install resolves the old 0.9.2, which is a different library.

```bash
uv add robotframework-PlatynUI==0.12.0.dev330             # verified pin   # pip: pip install robotframework-PlatynUI==0.12.0.dev330
uv add --prerelease allow robotframework-PlatynUI         # latest pre-release   # pip: pip install --pre robotframework-PlatynUI
```

- The wheel is prebuilt: it bundles the compiled `platynui-native` runtime. No Rust toolchain or git checkout is needed.
- Linux also needs a running AT-SPI2 accessibility bus and, recommended, an X11 session: see `platform-setup.md`.
- The optional CLI and inspector are standalone tools: `uv tool install --prerelease allow platynui-cli` and `uv tool install --prerelease allow platynui-inspector` (see `cli-and-inspector.md`).
