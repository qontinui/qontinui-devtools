# State Detection Integration - Quick Start

## File Locations

| File | Path | Lines | Purpose |
|------|------|-------|---------|
| **StateDetectionService.ts** | `/Users/jspinak/Documents/qontinui/qontinui-runner/src/services/StateDetectionService.ts` | 625 | Main TypeScript service |
| **state_detection_bridge.py** | `/Users/jspinak/Documents/qontinui/qontinui-runner/python/state_detection_bridge.py` | 225 | Python bridge script |
| **StateDetectionExample.ts** | `/Users/jspinak/Documents/qontinui/qontinui-runner/src/examples/StateDetectionExample.ts` | 362 | Usage examples |
| **README** | `/Users/jspinak/Documents/qontinui/qontinui-runner/src/services/StateDetectionService.README.md` | - | Full documentation |

## Minimal Usage Example

```typescript
import { stateDetectionService } from './services/StateDetectionService';

// Analyze a session
const result = await stateDetectionService.processSession('/path/to/screenshots');

// Use the results
console.log(`Found ${result.stateImages.length} elements`);
console.log(`Detected ${result.states.length} states`);
```

## With Error Handling

```typescript
import {
  stateDetectionService,
  StateDetectionError,
  StateDetectionErrorType
} from './services/StateDetectionService';

try {
  const result = await stateDetectionService.processSession(
    '/path/to/screenshots',
    {
      processingMode: 'fast',
      timeout: 300000
    }
  );

  // Success - process results
  result.stateImages.forEach(element => {
    console.log(`${element.name}: ${element.tags.join(', ')}`);
  });

} catch (error) {
  if (error instanceof StateDetectionError) {
    console.error(`Detection failed: ${error.type} - ${error.message}`);
  }
}
```

## Key Features

1. **Full TypeScript Types** - Complete type safety for all interfaces
2. **Process Management** - Automatic lifecycle management of Python processes
3. **Error Handling** - Typed error codes with detailed error information
4. **Configurable** - Extensive configuration options for different use cases
5. **Production Ready** - Robust error handling and process cleanup

## Configuration Quick Reference

```typescript
{
  minRegionSize: [20, 20],           // Minimum element size
  maxRegionSize: [500, 500],         // Maximum element size
  stabilityThreshold: 0.98,          // Pixel stability (0.0-1.0)
  processingMode: 'full',            // 'fast' | 'full' | 'accurate'
  timeout: 300000                    // 5 minutes
}
```

## Next Steps

1. **Test the bridge script:**
   ```bash
   python3 python/state_detection_bridge.py \
     /path/to/screenshots \
     '{"processing_mode": "fast"}'
   ```

2. **Import in your code:**
   ```typescript
   import { stateDetectionService } from './services/StateDetectionService';
   ```

3. **Run analysis:**
   ```typescript
   const result = await stateDetectionService.processSession('/screenshots');
   ```

4. **See full examples:**
   - Check `/Users/jspinak/Documents/qontinui/qontinui-runner/src/examples/StateDetectionExample.ts`
   - Read `/Users/jspinak/Documents/qontinui/qontinui-runner/src/services/StateDetectionService.README.md`

## TypeScript Interfaces Summary

```typescript
// Main result
interface StateDetectionResult {
  success: boolean;
  stateImages: StateImageInfo[];     // Detected UI elements
  states: DetectedState[];           // Detected application states
  totalScreenshots: number;
  processingTime: number;
}

// UI Element
interface StateImageInfo {
  id: string;
  name: string;
  x: number, y: number;              // Position
  width: number, height: number;     // Size
  frequency: number;                 // How often it appears (0.0-1.0)
  tags: string[];                    // Element types ['button', 'icon', ...]
}

// Application State
interface DetectedState {
  id: string;
  name: string;
  stateImageIds: string[];           // Elements in this state
  confidence: number;                // Detection confidence (0.0-1.0)
}
```

## Common Patterns

### Filter by Element Type
```typescript
const buttons = result.stateImages.filter(img =>
  img.tags.includes('button')
);
```

### Find High-Frequency Elements
```typescript
const persistentElements = result.stateImages.filter(img =>
  img.frequency > 0.8
);
```

### Find High-Confidence States
```typescript
const reliableStates = result.states.filter(state =>
  state.confidence > 0.9
);
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Python not found | `service.setPythonPath('/usr/local/bin/python3')` |
| Timeout | Increase timeout: `{ timeout: 600000 }` |
| JSON parse error | Check Python script only prints JSON to stdout |
| Process not cleaning up | Call `service.killAllProcesses()` |

## Complete Documentation

For complete documentation, see:
- **Full API docs:** `/Users/jspinak/Documents/qontinui/qontinui-runner/src/services/StateDetectionService.README.md`
- **Implementation details:** `/Users/jspinak/Documents/qontinui/qontinui-runner/STATE_DETECTION_INTEGRATION.md`
- **Code examples:** `/Users/jspinak/Documents/qontinui/qontinui-runner/src/examples/StateDetectionExample.ts`
