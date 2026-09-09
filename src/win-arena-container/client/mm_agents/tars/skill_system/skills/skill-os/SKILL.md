---
name: skill-os
description: >-
  Windows 11 desktop settings, File Explorer, and system configuration.
---
## Domain notes

- System settings are graded from real Windows state, not screenshots alone.
- Prefer Settings, Control Panel, and File Explorer for user-facing tasks. Use
  PowerShell only when the task allows a command-line route.

## Operating rules

- Save requested files under the exact path in the task. The benchmark user
  profile is `C:\Users\Docker`; its desktop is `C:\Users\Docker\Desktop`.
- Verify system changes with read-only PowerShell (`Get-ItemProperty`,
  `Get-CimInstance`, `Get-ChildItem`) when useful.
- Do not modify unrelated policies, services, users, or registry keys.

## Keyboard shortcuts

- `Win`: open Start.
- `Win+I`: open Settings.
- `Win+E`: open File Explorer.
- `Win+D`: show desktop.
- `Win+Up` / `Win+Down`: maximize / restore a window.
- `Win+Left` / `Win+Right`: snap a window.
- `Alt+Tab`: switch windows.
- `Alt+F4`: close the active window.
- `Ctrl+L`: focus File Explorer's address bar.
- `Ctrl+Shift+N`: create a folder in File Explorer.
- `F2`: rename the selected item.
- `Delete`: move the selected item to Recycle Bin.

## Cautions

- Keep the requested final application or Settings page visibly open when the
  task is graded on both persistent state and GUI state.
- Clipboard tasks require durable clipboard content; verify by reading or
  pasting it before finishing.
