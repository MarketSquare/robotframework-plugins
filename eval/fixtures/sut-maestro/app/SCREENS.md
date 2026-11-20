# Demo Login app (Android)

The app is built and installed on the emulator by the app team; this
repository holds only the tests. The screens below are what the tests target.

| App id | `com.example.demologin` |
|---|---|
| Device | Android 14 emulator `emulator-5554` |
| Driver | Maestro CLI (no Appium server) |

## Login screen

| Element | resource-id | text |
|---|---|---|
| Username field | `com.example.demologin:id/username` | Username |
| Password field | `com.example.demologin:id/password` | Password |
| Sign-in button | `com.example.demologin:id/login` | Sign in |
| Error banner (bad credentials) | `com.example.demologin:id/error` | Wrong username or password |

## Home screen (after `demo` / `demo`)

| Element | resource-id | text |
|---|---|---|
| Welcome text | `com.example.demologin:id/welcome` | Welcome, demo |
| Log-out button | `com.example.demologin:id/logout` | Log out |
