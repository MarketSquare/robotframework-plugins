# Demo Login app (Android)

The app is built and installed on the emulator by the app team; this
repository holds only the tests. The screens below are what the tests target.

| Package / activity | `com.example.demologin` / `.LoginActivity` |
|---|---|
| Appium server | `http://127.0.0.1:4723` |
| Automation | `UiAutomator2` (Android 14 emulator `emulator-5554`) |

## Login screen

| Element | accessibility id | resource-id |
|---|---|---|
| Username field | `username_input` | `com.example.demologin:id/username` |
| Password field | `password_input` | `com.example.demologin:id/password` |
| Sign-in button | `login_button` | `com.example.demologin:id/login` |
| Error banner (bad credentials) | `login_error` | `com.example.demologin:id/error` |

## Home screen (after `demo` / `demo`)

| Element | accessibility id | resource-id |
|---|---|---|
| Welcome text ("Welcome, demo") | `welcome_text` | `com.example.demologin:id/welcome` |
| Log-out button | `logout_button` | `com.example.demologin:id/logout` |
