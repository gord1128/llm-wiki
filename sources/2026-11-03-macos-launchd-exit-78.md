# Source: macOS launchd Exit 78 on External Volume Incident Note

Date: 2026-11-03
Environment: macOS 27.2 (Darwin 25.x), External SSD Volume (`/Volumes/Hyeonssd`)

## Incident Summary
- Symptom: LaunchAgent registered via `~/Library/LaunchAgents/com.user.aside.plist` fails immediately upon reboot with `Service exited with abnormal code: 78 (EX_CONFIG)`.
- Cause:
  1. Boot-time volume mount latency: `/Volumes/Hyeonssd` mounts after launchd processes user daemons.
  2. Sandboxing / TCC: Non-interactive launchd daemon lacks entitlement to access removable volume before user login.
- Solution:
  - Migrate from launchd to PID-based management script (`service.sh`) triggered on user terminal session or post-mount hook.
