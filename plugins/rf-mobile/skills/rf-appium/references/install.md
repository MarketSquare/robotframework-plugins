# Installing AppiumLibrary

Commands are in uv form. For a new environment, Poetry and venv + pip forms, and the general troubleshooting (wrong interpreter, PEP 668, old Python), see `rf-setup` (plugin `rf-core`): `uv add <pkg>` is `poetry add <pkg>` (pip alternative: `.venv/bin/python -m pip install <pkg>`), and `uv run <cmd>` is `poetry run <cmd>` or `.venv/bin/<cmd>`. Versions and floors checked on PyPI 2026-09-26.

```bash
uv add robotframework-appiumlibrary
```

- Package `robotframework-appiumlibrary` (3.2). Module `AppiumLibrary`. It pulls in `Appium-Python-Client`.
- After installing: the **Appium server** and platform drivers are Node tools, installed outside the Python environment:

```bash
npm install -g appium                        # Appium 3.x; Node ^20.19, ^22.12 or ≥ 24
appium driver install uiautomator2           # Android
appium driver install xcuitest               # iOS (macOS + Xcode)
appium driver list
appium driver doctor uiautomator2            # checks ANDROID_HOME, JDK, adb …
appium                                       # start the server (default http://127.0.0.1:4723)
```

- Android also needs the Android SDK (`ANDROID_HOME`), a JDK and an emulator or device. iOS needs Xcode. See `platform-specific.md`.
