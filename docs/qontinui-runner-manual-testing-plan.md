# Qontinui-Runner Manual Testing Plan

This document provides a comprehensive manual testing plan for all qontinui-runner functionality.

## Overview

Qontinui-Runner is a cross-platform desktop application (Windows, macOS, Linux) built with Tauri (Rust backend) + React/TypeScript frontend that executes GUI automation workflows locally.

---

## 1. Application Startup & Initialization

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 1.1 Cold start | Launch app from fresh install | Window appears top-center, Python executor auto-starts |
| 1.2 Status indicator | Check status after startup | Shows "Python: Running", "Config: Not Loaded", "Execution: Idle" |
| 1.3 Auto-load config (enabled) | Enable auto-load, close & reopen app | Last config auto-loads on startup |
| 1.4 Auto-load config (disabled) | Disable auto-load, close & reopen app | App starts with no config loaded |
| 1.5 Python executor failure | Kill Python process manually | Error displayed, reconnection attempted |

---

## 2. Configuration Management

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 2.1 Load valid config | Click "Load Configuration", select valid JSON | Config loads, workflows populate dropdown |
| 2.2 Load invalid config | Select malformed JSON file | Error displayed, no crash |
| 2.3 Load non-existent file | Manually enter bad path | Error displayed gracefully |
| 2.4 Workflow filtering | Load config with multiple workflows | Only "Main" category workflows shown |
| 2.5 Workflow selection | Select different workflow from dropdown | Workflow ID saved, persists on restart |
| 2.6 Config metadata display | Load config | Name, description, author shown correctly |

---

## 3. Execution Control

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 3.1 Start execution | Load config, select workflow, click Start | Execution begins, app minimizes, status shows "Executing" |
| 3.2 Stop execution | Click Stop during execution | Execution halts, app restores, status shows "Idle" |
| 3.3 Execute without config | Click Start with no config loaded | Button disabled or error shown |
| 3.4 Execute without workflow | Load config but don't select workflow | Appropriate error or default behavior |
| 3.5 Monitor selection | Select different monitor before execution | Automation targets correct monitor |
| 3.6 Multi-monitor detection | System with 2+ monitors | All monitors appear in dropdown with specs |

---

## 4. State Machine Navigation

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 4.1 View active states | During execution, check state viewer | Current states displayed correctly |
| 4.2 Execute transition | Select specific transition ID | Transition executes, state changes |
| 4.3 Navigate to single state | Call navigate_to_state | System navigates to target state |
| 4.4 Navigate to multiple states | Call navigate_to_multiple_states | System navigates through states sequentially |
| 4.5 Get available transitions | Query from current state | Returns valid transition options |

---

## 5. Logging System

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 5.1 General logs tab | Run execution, view General tab | Logs appear with timestamps and levels |
| 5.2 Log level filtering | Select Info/Warning/Error/Debug filter | Only matching logs shown |
| 5.3 Image Recognition tab | Run execution with image matching | Image match logs with confidence scores |
| 5.4 Actions tab | Run execution | Hierarchical action tree displayed |
| 5.5 Clear logs | Click clear button | Logs cleared from view |
| 5.6 Clipboard export | Click copy to clipboard | Logs copied in readable format |
| 5.7 Auto-scroll | Enable auto-scroll during execution | View scrolls to newest entries |
| 5.8 Action detail modal | Click action in tree | Modal shows action details |
| 5.9 Image detail modal | Click image match entry | Modal shows template, screenshot, match visualization |

---

## 6. Debug Settings

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 6.1 Enable image debug | Toggle enable_image_debug ON | Detailed image match logging appears |
| 6.2 Top matches count | Set top_matches_count to 5 | Top 5 matches shown in image logs |
| 6.3 Settings persistence | Change debug settings, restart app | Settings retained |
| 6.4 Debug images | Enable debug, run execution | Debug images with match boxes available |

---

## 7. Screenshot Capture

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 7.1 Enable screenshot capture | Enable in Settings tab | Screenshots captured during execution |
| 7.2 Manual click screenshots | Enable "capture on manual clicks" | Screenshots taken on click actions |
| 7.3 Custom output folder | Set custom folder path | Screenshots saved to specified location |
| 7.4 Custom base name | Set screenshot base name | Files named with custom prefix |
| 7.5 Screen selection | Select specific screen for capture | Only selected screen captured |
| 7.6 Save screenshot to disk | Click save button on screenshot | Image saved to selected location |

---

## 8. Video Recording

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 8.1 Start recording | Click start recording | Recording begins, status shows "Recording" |
| 8.2 Stop recording | Click stop recording | Recording stops, video file created |
| 8.3 Save video | Click save video button | Video saved to chosen destination |
| 8.4 Recording status | Check status during recording | Accurate status displayed |
| 8.5 Recording during execution | Start recording, then start execution | Both work simultaneously |

---

## 9. WebSocket/Cloud Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 9.1 Configure WebSocket | Enter URL, email, password in Settings | Settings saved |
| 9.2 Connect WebSocket | Click connect with valid credentials | Connection established |
| 9.3 Invalid credentials | Connect with bad credentials | Error displayed, graceful failure |
| 9.4 Screenshot streaming | Run execution with WS connected | Live screenshots appear in qontinui-web |
| 9.5 Log streaming | Run execution with WS connected | Logs stream to cloud in real-time |
| 9.6 Disconnect | Click disconnect | Connection closed cleanly |
| 9.7 Auto-reconnect | Kill network mid-execution | Automatic reconnection attempted |
| 9.8 QR code scanner | Click QR scan button | Camera opens, scans connection QR |
| 9.9 Disabled mode | Disable WebSocket | Execution works without cloud features |

---

## 10. Storage Management

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 10.1 View storage usage | Check storage stats | Shows accurate usage numbers |
| 10.2 Delete old sessions | Delete sessions older than X days | Old data removed |
| 10.3 Clear all storage | Click clear all | All local data removed |
| 10.4 Storage paths | Query storage paths | Returns valid accessible paths |

---

## 11. File Operations

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 11.1 Open config folder | Click "Open Folder" | Native file explorer opens to config directory |
| 11.2 Open screenshot folder | Navigate to screenshot output | Folder opens with saved screenshots |
| 11.3 File dialog (load) | Click load configuration | Native file picker appears |

---

## 12. Error Handling

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 12.1 Python executor crash | Force kill Python process | Error displayed, recovery attempted |
| 12.2 Invalid action | Config with bad action definition | Error logged, execution continues or stops gracefully |
| 12.3 Image not found | Element not on screen | Timeout, retry, error logged per failure strategy |
| 12.4 Network timeout | Disconnect network during cloud sync | Graceful degradation, local execution continues |
| 12.5 Disk full | Fill disk during screenshot save | Error displayed, no crash |

---

## 13. Cross-Platform Testing

| Test | Platform | Verify |
|------|----------|--------|
| 13.1 Windows | Windows 10/11 | All features work, Explorer opens |
| 13.2 macOS | macOS 12+ | All features work, Finder opens |
| 13.3 Linux | Ubuntu/Debian | All features work, xdg-open works |

---

## 14. Python Bridge Integration

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 14.1 Real mode execution | Run with actual GUI target | Mouse/keyboard actions performed |
| 14.2 Event translation | Execute actions | Events correctly translated to Tauri format |
| 14.3 Qontinui library | Run complex workflow | Library functions called correctly |
| 14.4 Health monitoring | Leave app idle | Health checks pass, connection maintained |
| 14.5 Graceful shutdown | Close app during execution | Python process terminates cleanly |

---

## 15. Update Checking (Production Only)

| Test | Steps | Expected Result |
|------|-------|-----------------|
| 15.1 Check for updates | Click check updates (production build) | Update status displayed |
| 15.2 Update available | When update exists | Prompt to download shown |
| 15.3 No update | When on latest version | "Up to date" message |

---

## Test Data Requirements

- **Demo config**: `qontinui-runner/demo-config.json`
- **Example configs**: `qontinui-runner/examples/`
- **Valid target application** (e.g., Notepad for notepad_automation.json)
- **Multi-monitor setup** (for monitor tests)
- **Network access** (for WebSocket tests)
- **qontinui-web backend running** (for cloud tests)

---

## Key File Paths

| Component | Path | Purpose |
|-----------|------|---------|
| Main App | `qontinui-runner/src/App.tsx` | Application entry point |
| Execution Context | `qontinui-runner/src/contexts/ExecutionContext.tsx` | Core execution state management |
| Commands Handler | `qontinui-runner/src-tauri/src/commands.rs` | All Tauri commands |
| Python Bridge | `qontinui-runner/src-tauri/src/executor/python_bridge.rs` | Python process management |
| Settings Panel | `qontinui-runner/src/components/Settings.tsx` | Settings UI and WebSocket config |
| Log Manager | `qontinui-runner/src/managers/LogManager.ts` | Log filtering and management |
| Demo Config | `qontinui-runner/demo-config.json` | Example automation configuration |
| Python Executor | `qontinui-runner/python-bridge/qontinui_executor.py` | Main Python execution engine |

---

## Test Coverage Summary

| Category | Test Count |
|----------|------------|
| Startup & Initialization | 5 |
| Configuration Management | 6 |
| Execution Control | 6 |
| State Machine Navigation | 5 |
| Logging System | 9 |
| Debug Settings | 4 |
| Screenshot Capture | 6 |
| Video Recording | 5 |
| WebSocket/Cloud | 9 |
| Storage Management | 4 |
| File Operations | 3 |
| Error Handling | 5 |
| Cross-Platform | 3 |
| Python Bridge | 5 |
| Update Checking | 3 |
| **Total** | **78** |
