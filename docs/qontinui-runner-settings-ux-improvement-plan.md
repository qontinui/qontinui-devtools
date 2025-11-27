# Qontinui-Runner Settings Tab UX Improvement Plan

## Problem Statement

The Settings tab currently contains 6 distinct functional areas in a single scrollable container, making it difficult for users to:
- Find specific settings quickly
- Understand what each section does
- Navigate between unrelated functionality
- Determine which settings are essential vs. advanced

### Current Structure (1700+ lines in Settings.tsx)

1. **Quick Connect** - WebSocket connection via QR/paste
2. **Application** - Auto-load last config toggle
3. **Cloud Sync** - WebSocket streaming configuration
4. **Debug** - Image matching debug options
5. **Screenshot Capture Tool** - Manual screenshot collection
6. **Local Storage** - Storage usage and cleanup

---

## Proposed Solution: Tabbed Settings with Categories

### Option A: Vertical Tab Navigation (Recommended)

Replace the scrollable list with a left-side vertical tab navigation:

```
┌─────────────────────────────────────────────────────────┐
│ Settings                                                │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  Connection  │  [Selected tab content area]             │
│  ─────────── │                                          │
│  General     │  Quick Connect to qontinui.io            │
│  ─────────── │  ────────────────────────────────────    │
│  Capture     │  Paste connection details from           │
│  ─────────── │  qontinui.io/connect-runner...           │
│  Storage     │                                          │
│  ─────────── │  [Connection String input]               │
│  Advanced    │                                          │
│              │  [Scan QR] [Connect] [Clear]             │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

**Tab Categories:**

| Tab | Contains | Icon |
|-----|----------|------|
| **Connection** | Quick Connect + Cloud Sync | `Wifi` |
| **General** | Application settings | `Settings` |
| **Capture** | Screenshot Capture Tool | `Camera` |
| **Storage** | Local Storage management | `HardDrive` |
| **Advanced** | Debug settings | `Bug` or `Wrench` |

### Option B: Horizontal Tabs

Similar to the existing log tabs (General, Images, Actions, Settings):

```
┌─────────────────────────────────────────────────────────┐
│ Settings                                                │
├─────────────────────────────────────────────────────────┤
│ [Connection] [General] [Capture] [Storage] [Advanced]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Selected tab content]                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Option C: Accordion Collapse (Minimal Change)

Keep current structure but add collapsible sections with only one open at a time:

```
┌─────────────────────────────────────────────────────────┐
│ Settings                                                │
├─────────────────────────────────────────────────────────┤
│ ▶ Connection (Click to expand)                          │
│ ▼ General                                               │
│   ┌─────────────────────────────────────────────────┐   │
│   │ Auto-load Last Configuration on Startup         │   │
│   │ [Toggle switch]                                 │   │
│   └─────────────────────────────────────────────────┘   │
│ ▶ Capture                                               │
│ ▶ Storage                                               │
│ ▶ Advanced                                              │
└─────────────────────────────────────────────────────────┘
```

---

## Section Descriptions (Add to UI)

Each section should have a brief description explaining its purpose:

### Connection
> **Connect your runner to qontinui.io for real-time monitoring, cloud storage, and collaboration features.**

Contains:
- Quick Connect (QR scan or paste connection string)
- Cloud Sync settings (what data to send)

### General
> **Application-level preferences that control startup behavior and defaults.**

Contains:
- Auto-load last configuration on startup

### Capture
> **Tools for collecting screenshots to build automation configurations.**

Contains:
- Screenshot Capture Tool settings
- Manual click capture mode
- Output folder and naming options
- Screen selection
- Capture timing delays

### Storage
> **Manage local storage for screenshots and videos captured during automation sessions.**

Contains:
- Storage usage display (screenshots/videos)
- Storage paths
- Cleanup actions (delete old, clear all)

### Advanced
> **Developer and debugging options for troubleshooting automation issues.**

Contains:
- Image Match Debug Mode
- Top matches display count

---

## Implementation Plan

### Phase 1: Component Refactoring

Split `Settings.tsx` (1700+ lines) into smaller components:

```
src/components/settings/
├── Settings.tsx              # Main container with tab navigation
├── ConnectionSettings.tsx    # Quick Connect + Cloud Sync
├── GeneralSettings.tsx       # Application preferences
├── CaptureSettings.tsx       # Screenshot capture tool
├── StorageSettings.tsx       # Local storage management
├── AdvancedSettings.tsx      # Debug settings
└── SettingsTab.tsx           # Reusable tab component
```

### Phase 2: State Management

Extract shared state into a settings context or use existing patterns:

```typescript
// src/contexts/SettingsContext.tsx
interface SettingsContextValue {
  activeTab: 'connection' | 'general' | 'capture' | 'storage' | 'advanced';
  setActiveTab: (tab: string) => void;
  // ... shared settings state
}
```

### Phase 3: UI Implementation

1. Create tab navigation component using Radix UI Tabs (already in dependencies)
2. Add section descriptions as subtitle text below each section header
3. Implement tab persistence (remember last selected tab)
4. Add keyboard navigation (arrow keys, tab key)

### Phase 4: Visual Polish

1. Add icons to each tab for quick recognition
2. Use consistent spacing and typography
3. Add subtle animations for tab transitions
4. Consider a "search settings" feature for power users

---

## Code Example: Tab Structure

```tsx
import * as Tabs from "@radix-ui/react-tabs";
import { Wifi, Settings, Camera, HardDrive, Wrench } from "lucide-react";

export function Settings() {
  return (
    <Tabs.Root defaultValue="connection" orientation="vertical">
      <div className="flex">
        {/* Left sidebar with tabs */}
        <Tabs.List className="flex flex-col w-48 border-r border-border">
          <Tabs.Trigger value="connection" className="...">
            <Wifi className="w-4 h-4" />
            Connection
          </Tabs.Trigger>
          <Tabs.Trigger value="general" className="...">
            <Settings className="w-4 h-4" />
            General
          </Tabs.Trigger>
          <Tabs.Trigger value="capture" className="...">
            <Camera className="w-4 h-4" />
            Capture
          </Tabs.Trigger>
          <Tabs.Trigger value="storage" className="...">
            <HardDrive className="w-4 h-4" />
            Storage
          </Tabs.Trigger>
          <Tabs.Trigger value="advanced" className="...">
            <Wrench className="w-4 h-4" />
            Advanced
          </Tabs.Trigger>
        </Tabs.List>

        {/* Content area */}
        <div className="flex-1 p-6">
          <Tabs.Content value="connection">
            <SectionHeader
              title="Connection"
              description="Connect your runner to qontinui.io for real-time monitoring and cloud storage."
            />
            <ConnectionSettings />
          </Tabs.Content>
          {/* ... other tabs */}
        </div>
      </div>
    </Tabs.Root>
  );
}

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-6">
      <h3 className="text-xl font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground mt-1">{description}</p>
    </div>
  );
}
```

---

## Alternative: Quick Settings vs. Full Settings

For users who just want common operations, add a "Quick Settings" panel accessible from the main toolbar:

```
┌─────────────────────────────────────┐
│ Quick Settings                    ✕ │
├─────────────────────────────────────┤
│                                     │
│ Cloud Sync: [Connected ●]           │
│                                     │
│ Auto-load Config: [On]              │
│                                     │
│ Debug Mode: [Off]                   │
│                                     │
│ ──────────────────────────────────  │
│ [Open Full Settings]                │
│                                     │
└─────────────────────────────────────┘
```

---

## Summary of Recommendations

1. **Primary**: Implement vertical tab navigation (Option A)
2. **Add descriptions** to each settings section
3. **Split Settings.tsx** into focused sub-components
4. **Use Radix UI Tabs** (already in project dependencies)
5. **Consider Quick Settings** popover for common toggles
6. **Persist active tab** between sessions

### Priority Order

| Priority | Task | Effort |
|----------|------|--------|
| P0 | Add section descriptions | Low |
| P1 | Split into sub-components | Medium |
| P1 | Add vertical tab navigation | Medium |
| P2 | Persist tab selection | Low |
| P3 | Add Quick Settings popover | Medium |
| P3 | Add settings search | High |

---

## Benefits

- **Discoverability**: Users can quickly scan tab names to find what they need
- **Reduced cognitive load**: Only one category visible at a time
- **Scalability**: Easy to add new settings categories
- **Maintainability**: Smaller, focused components are easier to test and modify
- **Accessibility**: Tab navigation follows ARIA patterns
