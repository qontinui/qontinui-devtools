# Inline Workflow Detection Flow

## Detection Process

```
ConfigValidator.validate_file()
│
├─→ Load and parse JSON config
│
├─→ Validate Main Workflows
│   │
│   ├─→ For each workflow in workflows array:
│   │   └─→ Workflow.model_validate(workflow)
│   │       ├─→ ✅ Valid → increment valid_count
│   │       └─→ ❌ Invalid → capture errors
│
└─→ Validate Inline Workflows
    │
    ├─→ _find_inline_workflows(workflows)
    │   │
    │   └─→ Walk through all actions in all workflows:
    │       │
    │       ├─→ Pattern 1: RUN_WORKFLOW
    │       │   └─→ config.workflow (if dict with actions)
    │       │
    │       ├─→ Pattern 2: IF Action
    │       │   ├─→ config.thenWorkflow
    │       │   └─→ config.elseWorkflow
    │       │
    │       ├─→ Pattern 3: LOOP Action
    │       │   └─→ config.workflow
    │       │
    │       ├─→ Pattern 4: TRY_CATCH Action
    │       │   ├─→ config.tryWorkflow
    │       │   ├─→ config.catchWorkflow
    │       │   └─→ config.finallyWorkflow
    │       │
    │       └─→ Pattern 5: SWITCH Action
    │           ├─→ config.cases[*].workflow
    │           └─→ config.defaultWorkflow
    │
    └─→ For each inline workflow found:
        └─→ Workflow.model_validate(inline_workflow)
            ├─→ ✅ Valid → increment inline_valid_count
            └─→ ❌ Invalid → capture inline_errors with context
```

## Data Flow

```
Config File
    ↓
workflows[] array
    ↓
    ├─→ Main Workflow Validation
    │   └─→ errors[] (main workflow errors)
    │
    └─→ Inline Workflow Detection
        ↓
        workflows[] → _find_inline_workflows()
        ↓
        └─→ For each workflow:
            └─→ For each action:
                └─→ Check action.type and action.config
                    ↓
                    └─→ Extract inline workflows
                        ↓
                        [
                          (parent_workflow_id, parent_workflow_name,
                           action_id, inline_workflow_dict)
                        ]
        ↓
        Inline Workflow Validation
        ↓
        inline_workflow_errors[] (with context)
```

## Error Context Structure

```python
ValidationError(
    workflow_id="main_workflow",           # Parent workflow ID
    workflow_name="Main Workflow",         # Parent workflow name
    field="connections",                   # Field with error
    error_type="missing",                  # Error type
    message="Field required",              # Error message
    current_value=None,                    # Current value
    expected_type="dict",                  # Expected type
    location=["connections"],              # Field location
    is_inline=True,                        # ✨ Marks as inline workflow error
    parent_action_id="if_action_1.then",   # ✨ Parent action context
    inline_workflow_context="Inline workflow in action 'if_action_1.then'"  # ✨ Description
)
```

## Detection Example

### Input Config Structure

```json
{
  "workflows": [
    {
      "id": "main",
      "actions": [
        {
          "id": "if_1",
          "type": "IF",
          "config": {
            "condition": {...},
            "thenWorkflow": {          ← Inline workflow detected!
              "id": "then_branch",
              "actions": [...],
              "connections": {...}
            }
          }
        }
      ]
    }
  ]
}
```

### Detection Output

```python
[
  (
    "main",                    # parent_workflow_id
    "Main Workflow",           # parent_workflow_name
    "if_1.then",              # action_id with context
    {                         # inline_workflow_dict
      "id": "then_branch",
      "actions": [...],
      "connections": {...}
    }
  )
]
```

## Validation Report Structure

```python
ValidationReport(
    config_path=Path("config.json"),
    is_valid=False,

    # Main workflows
    total_workflows=3,
    valid_workflows=2,
    invalid_workflows=1,
    errors=[...],              # Main workflow errors

    # Inline workflows (NEW!)
    total_inline_workflows=5,
    valid_inline_workflows=3,
    invalid_inline_workflows=2,
    inline_workflow_errors=[...],  # Inline workflow errors with context

    warnings=[]
)
```

## Action Type → Inline Workflow Mapping

| Action Type | Config Path(s) | Context Suffix |
|-------------|----------------|----------------|
| RUN_WORKFLOW | `config.workflow` | `{action_id}` |
| IF | `config.thenWorkflow` | `{action_id}.then` |
| IF | `config.elseWorkflow` | `{action_id}.else` |
| LOOP | `config.workflow` | `{action_id}.loop` |
| TRY_CATCH | `config.tryWorkflow` | `{action_id}.try` |
| TRY_CATCH | `config.catchWorkflow` | `{action_id}.catch` |
| TRY_CATCH | `config.finallyWorkflow` | `{action_id}.finally` |
| SWITCH | `config.cases[N].workflow` | `{action_id}.case[{N}]` |
| SWITCH | `config.defaultWorkflow` | `{action_id}.default` |

## Report Output Structure

```
Main Workflow Errors Section
    ├─→ Grouped by workflow_id
    └─→ Shows field-level errors

Migration Hints Section
    └─→ Shows common migration patterns

Inline Workflow Errors Section (NEW!)
    ├─→ Grouped by inline_workflow_context
    ├─→ Shows parent workflow and action
    └─→ Shows field-level errors with context

Warnings Section
    └─→ General warnings
```
