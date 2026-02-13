# Inline Workflow Validation Enhancement Summary

## Overview

The ConfigValidator has been enhanced to detect and validate inline workflows embedded within action configurations. These inline workflows were previously missed during validation because they aren't part of the main workflows array.

## Changes Made

### 1. Enhanced ValidationError Dataclass

Added support for inline workflow context tracking:

```python
@dataclass
class ValidationError:
    # ... existing fields ...
    is_inline: bool = False
    parent_action_id: str | None = None
    inline_workflow_context: str | None = None
```

### 2. Enhanced ValidationReport Dataclass

Added tracking for inline workflow validation results:

```python
@dataclass
class ValidationReport:
    # ... existing fields ...
    total_inline_workflows: int = 0
    valid_inline_workflows: int = 0
    invalid_inline_workflows: int = 0
    inline_workflow_errors: list[ValidationError] = None
```

### 3. New _find_inline_workflows() Method

This method walks through all actions in all workflows and detects embedded workflow definitions. It supports multiple patterns:

**Pattern 1: RunWorkflow with Inline Definition**
```json
{
  "type": "RUN_WORKFLOW",
  "config": {
    "workflow": {
      "id": "inline_workflow",
      "actions": [...],
      "connections": {...}
    }
  }
}
```

**Pattern 2: IF Action with Inline Workflows**
```json
{
  "type": "IF",
  "config": {
    "condition": {...},
    "thenWorkflow": {
      "id": "then_branch",
      "actions": [...]
    },
    "elseWorkflow": {
      "id": "else_branch",
      "actions": [...]
    }
  }
}
```

**Pattern 3: LOOP Action with Inline Workflow**
```json
{
  "type": "LOOP",
  "config": {
    "loopType": "FOR",
    "iterations": 5,
    "workflow": {
      "id": "loop_body",
      "actions": [...]
    }
  }
}
```

**Pattern 4: TRY_CATCH Action with Inline Workflows**
```json
{
  "type": "TRY_CATCH",
  "config": {
    "tryWorkflow": {...},
    "catchWorkflow": {...},
    "finallyWorkflow": {...}
  }
}
```

**Pattern 5: SWITCH Action with Inline Workflows**
```json
{
  "type": "SWITCH",
  "config": {
    "expression": "variable",
    "cases": [
      {
        "value": "case1",
        "workflow": {...}
      }
    ],
    "defaultWorkflow": {...}
  }
}
```

### 4. Enhanced validate_file() Method

Now validates both main workflows AND inline workflows:

```python
# Validate main workflows
for workflow in workflows:
    validated = self.Workflow.model_validate(workflow)

# Validate inline workflows
inline_workflows = self._find_inline_workflows(workflows)
for parent_workflow_id, parent_workflow_name, action_id, inline_workflow in inline_workflows:
    validated = self.Workflow.model_validate(inline_workflow)
```

### 5. Enhanced print_report() Method

Now displays inline workflow validation results separately:

- Success summary includes inline workflow count
- Error summary shows inline workflow error count
- Dedicated "Inline Workflow Errors" section groups errors by parent context
- Clear indication of parent workflow and parent action

## Example Output

### Successful Validation with Inline Workflows

```
================================================================================
Config Validation Report: config.json
================================================================================

✅ PASSED - All 3 workflows are valid, 5 inline workflows are valid
```

### Failed Validation with Inline Workflow Errors

```
================================================================================
Config Validation Report: config.json
================================================================================

❌ FAILED - 1/3 workflows have errors
           2/5 inline workflows have errors

📝 Workflow: Main Workflow
   ID: main_workflow
   Errors: 2

   ❌ connections
      Type: missing
      Message: Field required

   ❌ actions.0.config.target.type
      Type: literal_error
      Message: Input should be 'coordinates', 'image', or 'region'

================================================================================
💡 How to Fix:
================================================================================

[Migration hints if applicable...]

================================================================================
📦 Inline Workflow Errors:
================================================================================

📝 Inline Workflow in: Main Workflow
   Parent Action: if_action_1.then
   Context: Inline workflow in action 'if_action_1.then'
   Errors: 2

   ❌ format
      Type: missing
      Message: Field required

   ❌ connections
      Type: missing
      Message: Field required

📝 Inline Workflow in: Main Workflow
   Parent Action: loop_action_2.loop
   Context: Inline workflow in action 'loop_action_2.loop'
   Errors: 1

   ❌ version
      Type: missing
      Message: Field required
```

## Types of Inline Workflows Detected

The validator now detects the following types of inline workflows:

1. **RUN_WORKFLOW inline definitions** - Complete workflows embedded in RUN_WORKFLOW actions
2. **IF then/else branches** - Workflows in conditional branches (if_action.then, if_action.else)
3. **LOOP bodies** - Workflows executed in loop iterations (loop_action.loop)
4. **TRY_CATCH blocks** - Workflows in try/catch/finally blocks (action.try, action.catch, action.finally)
5. **SWITCH cases** - Workflows in switch case branches (action.case[N], action.default)

## Benefits

1. **Complete Validation** - No more hidden schema errors in inline workflows
2. **Clear Error Context** - Errors show exactly which action contains the invalid inline workflow
3. **Separate Reporting** - Inline workflow errors are clearly distinguished from main workflow errors
4. **Hierarchical Understanding** - See which parent workflow and action contains problematic inline workflows
5. **Comprehensive Coverage** - Supports all action types that can contain inline workflows

## Usage

```python
from qontinui_devtools.config_validator import ConfigValidator

validator = ConfigValidator()
report = validator.validate_file("config.json")

# Check if validation passed
if not report.is_valid:
    report.print_report(verbose=True)

    # Access inline workflow errors
    for error in report.inline_workflow_errors:
        print(f"Inline error in {error.parent_action_id}: {error.message}")
```

## Testing

Run the example script to see inline workflow validation in action:

```bash
python examples/test_inline_workflow_validation.py
```

This creates a test config with intentional schema errors in an inline workflow and demonstrates how they're detected and reported.
