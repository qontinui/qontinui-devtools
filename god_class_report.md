# God Class Detection Report

Found 267 god classes violating Single Responsibility Principle.

## Summary

- **Total Classes Analyzed**: 267
- **Critical Severity**: 3
- **High Severity**: 3
- **Medium Severity**: 261

## Thresholds Used

- **Minimum Lines**: 500
- **Minimum Methods**: 30
- **Maximum LCOM**: 0.8

## Detailed Analysis

### 1. Region [CRITICAL]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/region.py:20`

**Metrics**:
- Lines of Code: 330
- Method Count: 82
- Attribute Count: 0
- Cyclomatic Complexity: 51
- LCOM (Lack of Cohesion): 0.813

**Detected Responsibilities**:

- From Operations

---

### 2. State [CRITICAL]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state.py:33`

**Metrics**:
- Lines of Code: 277
- Method Count: 98
- Attribute Count: 0
- Cyclomatic Complexity: 51
- LCOM (Lack of Cohesion): 0.738

**Detected Responsibilities**:

- Add Operations
- Data Access
- Hidden Operations
- State Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 36
  - Methods: `get_transitions_to, get_possible_next_states, get_state_images, set_search_region_for_all_images, get_boundaries, set_probability_to_base_probability`

---

### 3. QontinuiTransformer [CRITICAL]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/dsl/parser.py:185`

**Metrics**:
- Lines of Code: 201
- Method Count: 90
- Attribute Count: 5
- Cyclomatic Complexity: 99
- LCOM (Lack of Cohesion): 0.995

**Detected Responsibilities**:

- Action Operations
- Element Operations
- Json Operations
- State Operations
- Transition Operations

---

### 4. AssertionConverter [HIGH]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/translation/assertion_converter.py:9`

**Metrics**:
- Lines of Code: 415
- Method Count: 56
- Attribute Count: 2
- Cyclomatic Complexity: 126
- LCOM (Lack of Cohesion): 0.607

**Detected Responsibilities**:

- Convert Operations
- Extract Operations
- Transformation

**Extraction Suggestions**:

- **Transformer**
  - Responsibility: Transformer
  - Methods to Extract: 3
  - Estimated Lines: 40
  - Methods: `convert_assertion, convert_multiple_assertions, convert_custom_assertion`

---

### 5. SpringTestAdapter [HIGH]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/translation/spring_test_adapter.py:14`

**Metrics**:
- Lines of Code: 377
- Method Count: 64
- Attribute Count: 3
- Cyclomatic Complexity: 75
- LCOM (Lack of Cohesion): 0.923

**Detected Responsibilities**:

- Convert Operations
- Extract Operations
- Handle Operations

---

### 6. Pattern [HIGH]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/pattern.py:23`

**Metrics**:
- Lines of Code: 315
- Method Count: 56
- Attribute Count: 0
- Cyclomatic Complexity: 37
- LCOM (Lack of Cohesion): 0.820

**Detected Responsibilities**:

- Data Access
- From Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 8
  - Estimated Lines: 77
  - Methods: `get_image, get_imgpath, get_b_image, get_effective_similarity, set_search_regions_to, get_regions, get_regions_for_search, get_region`

---

### 7. TestDiagnosticReporter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_diagnostic_reporter.py:28`

**Metrics**:
- Lines of Code: 501
- Method Count: 54
- Attribute Count: 0
- Cyclomatic Complexity: 151
- LCOM (Lack of Cohesion): 0.279

**Detected Responsibilities**:

- Test Operations

---

### 8. TestFixSuggestionEngine [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_fix_suggestion_engine.py:24`

**Metrics**:
- Lines of Code: 462
- Method Count: 54
- Attribute Count: 0
- Cyclomatic Complexity: 149
- LCOM (Lack of Cohesion): 0.279

**Detected Responsibilities**:

- Test Operations

---

### 9. PynputController [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/implementations/pynput_controller.py:18`

**Metrics**:
- Lines of Code: 438
- Method Count: 46
- Attribute Count: 5
- Cyclomatic Complexity: 73
- LCOM (Lack of Cohesion): 0.805

**Detected Responsibilities**:

- Key Operations
- Mouse Operations

---

### 10. PytestRunner [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/execution/pytest_runner.py:24`

**Metrics**:
- Lines of Code: 405
- Method Count: 28
- Attribute Count: 3
- Cyclomatic Complexity: 81
- LCOM (Lack of Cohesion): 0.821

**Detected Responsibilities**:

- Parse Operations
- Run Operations

---

### 11. PixelStabilityAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/pixel_analysis/analyzer.py:18`

**Metrics**:
- Lines of Code: 394
- Method Count: 28
- Attribute Count: 3
- Cyclomatic Complexity: 71
- LCOM (Lack of Cohesion): 0.859

**Detected Responsibilities**:

- Calculate Operations

---

### 12. LLMTestTranslator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/execution/llm_test_translator.py:22`

**Metrics**:
- Lines of Code: 392
- Method Count: 38
- Attribute Count: 4
- Cyclomatic Complexity: 77
- LCOM (Lack of Cohesion): 0.961

**Detected Responsibilities**:

- Generate Operations
- Translate Operations

---

### 13. IntegrationTestEnvironment [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/translation/integration_test_environment.py:48`

**Metrics**:
- Lines of Code: 391
- Method Count: 32
- Attribute Count: 6
- Cyclomatic Complexity: 40
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Initialization
- Setup Operations

---

### 14. QontinuiMockGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/mocks/qontinui_mock_generator.py:11`

**Metrics**:
- Lines of Code: 389
- Method Count: 40
- Attribute Count: 4
- Cyclomatic Complexity: 46
- LCOM (Lack of Cohesion): 0.883

**Detected Responsibilities**:

- Generate Operations
- Map Operations

---

### 15. LLMTestTranslator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/translation/llm_test_translator.py:34`

**Metrics**:
- Lines of Code: 385
- Method Count: 38
- Attribute Count: 4
- Cyclomatic Complexity: 36
- LCOM (Lack of Cohesion): 0.895

**Detected Responsibilities**:

- Parse Operations
- Translate Operations

---

### 16. GraphTraverser [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/graph_traversal.py:44`

**Metrics**:
- Lines of Code: 361
- Method Count: 36
- Attribute Count: 7
- Cyclomatic Complexity: 92
- LCOM (Lack of Cohesion): 0.669

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 51
  - Methods: `get_entry_actions, get_next_actions, set_breakpoint, get_execution_path, get_statistics`

---

### 17. DelegatingActionExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/action_executors/delegating_executor.py:21`

**Metrics**:
- Lines of Code: 359
- Method Count: 20
- Attribute Count: 14
- Cyclomatic Complexity: 46
- LCOM (Lack of Cohesion): 0.944

**Detected Responsibilities**:

- Emit Operations

---

### 18. TestTestClassifier [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_classifier.py:22`

**Metrics**:
- Lines of Code: 357
- Method Count: 36
- Attribute Count: 0
- Cyclomatic Complexity: 68
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Test Operations

---

### 19. SemanticScene [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/core/semantic_scene.py:18`

**Metrics**:
- Lines of Code: 356
- Method Count: 50
- Attribute Count: 0
- Cyclomatic Complexity: 112
- LCOM (Lack of Cohesion): 0.343

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 15
  - Estimated Lines: 196
  - Methods: `get_object_by_id, find_by_description, find_by_type, find_in_region, find_closest_to, find_interactable, find_with_text, get_objects_above, get_objects_below, get_objects_left_of`

---

### 20. TestBehaviorComparator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_behavior_comparator.py:16`

**Metrics**:
- Lines of Code: 356
- Method Count: 58
- Attribute Count: 0
- Cyclomatic Complexity: 109
- LCOM (Lack of Cohesion): 0.200

**Detected Responsibilities**:

- Test Operations

---

### 21. BrobotConverter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/migrations/brobot_converter.py:44`

**Metrics**:
- Lines of Code: 354
- Method Count: 32
- Attribute Count: 7
- Cyclomatic Complexity: 71
- LCOM (Lack of Cohesion): 0.714

**Detected Responsibilities**:

- Convert Operations
- Find Operations

---

### 22. TestEndToEndMigrationWorkflow [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_end_to_end_workflow.py:20`

**Metrics**:
- Lines of Code: 344
- Method Count: 28
- Attribute Count: 0
- Cyclomatic Complexity: 60
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Test Operations

---

### 23. FindWrapper [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/wrappers/find_wrapper.py:30`

**Metrics**:
- Lines of Code: 342
- Method Count: 22
- Attribute Count: 3
- Cyclomatic Complexity: 51
- LCOM (Lack of Cohesion): 0.889

---

### 24. StateStore [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state_store.py:23`

**Metrics**:
- Lines of Code: 340
- Method Count: 52
- Attribute Count: 9
- Cyclomatic Complexity: 52
- LCOM (Lack of Cohesion): 0.330

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 11
  - Estimated Lines: 116
  - Methods: `get_all, get_active_states, get_current_state, set_current_state, get_transitions, get_metadata, get_status, get_children, get_parent, find_by_tag`

---

### 25. HybridTestTranslator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/translation/hybrid_test_translator.py:60`

**Metrics**:
- Lines of Code: 336
- Method Count: 38
- Attribute Count: 7
- Cyclomatic Complexity: 75
- LCOM (Lack of Cohesion): 0.686

**Detected Responsibilities**:

- Translate Operations

---

### 26. BehaviorComparatorImpl [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/behavior_comparator.py:55`

**Metrics**:
- Lines of Code: 336
- Method Count: 42
- Attribute Count: 3
- Cyclomatic Complexity: 61
- LCOM (Lack of Cohesion): 0.989

**Detected Responsibilities**:

- Compare Operations
- Execute Operations
- Extract Operations

---

### 27. TestMigrationOrchestrator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/orchestrator.py:75`

**Metrics**:
- Lines of Code: 330
- Method Count: 32
- Attribute Count: 11
- Cyclomatic Complexity: 64
- LCOM (Lack of Cohesion): 0.619

---

### 28. TestFailureAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/test_failure_analyzer.py:37`

**Metrics**:
- Lines of Code: 329
- Method Count: 30
- Attribute Count: 3
- Cyclomatic Complexity: 44
- LCOM (Lack of Cohesion): 0.945

**Detected Responsibilities**:

- Initialize Operations

---

### 29. ProcessorManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/processors/manager.py:26`

**Metrics**:
- Lines of Code: 327
- Method Count: 34
- Attribute Count: 3
- Cyclomatic Complexity: 90
- LCOM (Lack of Cohesion): 0.500

**Detected Responsibilities**:

- Business Logic

**Extraction Suggestions**:

- **BusinessLogicProcessor**
  - Responsibility: BusinessLogic
  - Methods to Extract: 5
  - Estimated Lines: 119
  - Methods: `process_with_best_processor, process_with_all, process_sequential, process_parallel, process_adaptive`

---

### 30. TransitionFunction [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/transition_function.py:38`

**Metrics**:
- Lines of Code: 326
- Method Count: 38
- Attribute Count: 0
- Cyclomatic Complexity: 72
- LCOM (Lack of Cohesion): 0.754

**Detected Responsibilities**:

- Data Access
- Execute Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 31
  - Methods: `set_fallback, set_parameter, get_last_result, get_execution_count`

---

### 31. MaskGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/masks/mask_generator.py:34`

**Metrics**:
- Lines of Code: 325
- Method Count: 24
- Attribute Count: 0
- Cyclomatic Complexity: 45
- LCOM (Lack of Cohesion): 0.927

**Detected Responsibilities**:

- Generate Operations

---

### 32. TestClassifier [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/discovery/classifier.py:22`

**Metrics**:
- Lines of Code: 325
- Method Count: 30
- Attribute Count: 3
- Cyclomatic Complexity: 73
- LCOM (Lack of Cohesion): 0.901

**Detected Responsibilities**:

- Detect Operations

---

### 33. QontinuiStateManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/state_management/manager.py:18`

**Metrics**:
- Lines of Code: 324
- Method Count: 42
- Attribute Count: 11
- Cyclomatic Complexity: 68
- LCOM (Lack of Cohesion): 0.695

**Detected Responsibilities**:

- Create Operations
- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 38
  - Methods: `get_state, get_current_states, get_possible_transitions, get_state_graph_visualization`

---

### 34. TemplateMatcher [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/find/matchers/template_matcher.py:21`

**Metrics**:
- Lines of Code: 324
- Method Count: 18
- Attribute Count: 2
- Cyclomatic Complexity: 58
- LCOM (Lack of Cohesion): 1.000

---

### 35. JavaToPythonTranslator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/translation/java_to_python_translator.py:11`

**Metrics**:
- Lines of Code: 322
- Method Count: 42
- Attribute Count: 2
- Cyclomatic Complexity: 86
- LCOM (Lack of Cohesion): 0.868

**Detected Responsibilities**:

- Translate Operations

---

### 36. OcclusionDetector [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/multistate_integration/occlusion_detector.py:58`

**Metrics**:
- Lines of Code: 315
- Method Count: 38
- Attribute Count: 7
- Cyclomatic Complexity: 69
- LCOM (Lack of Cohesion): 0.477

**Detected Responsibilities**:

- Data Access
- Detect Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 76
  - Methods: `get_covered_states, get_covering_state, get_visible_states, get_all_occluded_states, get_occlusion_chain, get_statistics`

---

### 37. EmbeddingGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/perception/embeddings.py:38`

**Metrics**:
- Lines of Code: 315
- Method Count: 24
- Attribute Count: 8
- Cyclomatic Complexity: 78
- LCOM (Lack of Cohesion): 0.818

**Detected Responsibilities**:

- Encode Operations

---

### 38. PathFinder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/path_finder.py:15`

**Metrics**:
- Lines of Code: 312
- Method Count: 36
- Attribute Count: 0
- Cyclomatic Complexity: 72
- LCOM (Lack of Cohesion): 0.719

**Detected Responsibilities**:

- Data Access
- Find Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 9
  - Estimated Lines: 119
  - Methods: `find_path, find_shortest_path, find_all_paths, get_distance, find_cycles, set_max_depth, set_use_probability, set_use_score, set_allow_loops`

---

### 39. MathExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/math_executor.py:17`

**Metrics**:
- Lines of Code: 310
- Method Count: 28
- Attribute Count: 2
- Cyclomatic Complexity: 53
- LCOM (Lack of Cohesion): 0.987

---

### 40. StringExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/string_executor.py:38`

**Metrics**:
- Lines of Code: 310
- Method Count: 24
- Attribute Count: 1
- Cyclomatic Complexity: 49
- LCOM (Lack of Cohesion): 1.000

---

### 41. Find [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/find/find.py:27`

**Metrics**:
- Lines of Code: 307
- Method Count: 46
- Attribute Count: 5
- Cyclomatic Complexity: 76
- LCOM (Lack of Cohesion): 0.671

---

### 42. TestCoverageTracker [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_coverage_tracker.py:27`

**Metrics**:
- Lines of Code: 307
- Method Count: 38
- Attribute Count: 0
- Cyclomatic Complexity: 131
- LCOM (Lack of Cohesion): 0.012

**Detected Responsibilities**:

- Test Operations

---

### 43. DeletionManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/deletion_manager.py:13`

**Metrics**:
- Lines of Code: 306
- Method Count: 44
- Attribute Count: 3
- Cyclomatic Complexity: 79
- LCOM (Lack of Cohesion): 0.824

---

### 44. TestBrobotTestScanner [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_scanner.py:12`

**Metrics**:
- Lines of Code: 301
- Method Count: 42
- Attribute Count: 0
- Cyclomatic Complexity: 69
- LCOM (Lack of Cohesion): 0.090

**Detected Responsibilities**:

- Test Operations

---

### 45. RegionBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/region/region_builder.py:11`

**Metrics**:
- Lines of Code: 297
- Method Count: 44
- Attribute Count: 12
- Cyclomatic Complexity: 36
- LCOM (Lack of Cohesion): 0.267

**Detected Responsibilities**:

- With Operations

---

### 46. DebugManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/debugging/debug_manager.py:20`

**Metrics**:
- Lines of Code: 296
- Method Count: 44
- Attribute Count: 10
- Cyclomatic Complexity: 65
- LCOM (Lack of Cohesion): 0.424

**Detected Responsibilities**:

- Data Access
- Event Handling
- Register Operations

**Extraction Suggestions**:

- **EventHandler**
  - Responsibility: EventHandler
  - Methods to Extract: 3
  - Estimated Lines: 108
  - Methods: `on_action_start, on_action_complete, on_error`

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 50
  - Methods: `get_instance, get_session, get_active_session, set_active_session, get_statistics`

---

### 47. ConnectionRouter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/connection_router.py:17`

**Metrics**:
- Lines of Code: 296
- Method Count: 26
- Attribute Count: 4
- Cyclomatic Complexity: 66
- LCOM (Lack of Cohesion): 0.909

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 131
  - Methods: `get_action_output_type, get_routing_options, find_reachable_actions, find_unreachable_actions, get_execution_paths, get_critical_path`

---

### 48. TestTestFailureAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_failure_analyzer.py:12`

**Metrics**:
- Lines of Code: 296
- Method Count: 42
- Attribute Count: 0
- Cyclomatic Complexity: 90
- LCOM (Lack of Cohesion): 0.095

**Detected Responsibilities**:

- Test Operations

---

### 49. MSSScreenCapture [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/implementations/mss_capture.py:18`

**Metrics**:
- Lines of Code: 295
- Method Count: 36
- Attribute Count: 7
- Cyclomatic Complexity: 62
- LCOM (Lack of Cohesion): 0.824

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 50
  - Methods: `get_monitors, get_primary_monitor, get_screen_size, get_pixel_color`

---

### 50. ResultValidator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/result_validator.py:76`

**Metrics**:
- Lines of Code: 295
- Method Count: 36
- Attribute Count: 6
- Cyclomatic Complexity: 73
- LCOM (Lack of Cohesion): 0.860

**Detected Responsibilities**:

- Compare Operations
- Validate Operations

---

### 51. Match [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/find/match.py:16`

**Metrics**:
- Lines of Code: 292
- Method Count: 54
- Attribute Count: 0
- Cyclomatic Complexity: 62
- LCOM (Lack of Cohesion): 0.530

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 20
  - Methods: `get_region, get_target, get_text`

---

### 52. ActionRegistry [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/internal/execution/action_registry.py:33`

**Metrics**:
- Lines of Code: 292
- Method Count: 36
- Attribute Count: 5
- Cyclomatic Complexity: 57
- LCOM (Lack of Cohesion): 0.691

**Detected Responsibilities**:

- List Operations

---

### 53. ConfigurationManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/config/configuration_manager.py:19`

**Metrics**:
- Lines of Code: 291
- Method Count: 34
- Attribute Count: 5
- Cyclomatic Complexity: 59
- LCOM (Lack of Cohesion): 0.558

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 77
  - Methods: `get_instance, load_from_file, load_profile, get_settings, get_properties, get_environment, get_info`

---

### 54. TestHybridTestTranslator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_hybrid_translator.py:46`

**Metrics**:
- Lines of Code: 291
- Method Count: 48
- Attribute Count: 0
- Cyclomatic Complexity: 109
- LCOM (Lack of Cohesion): 0.083

**Detected Responsibilities**:

- Test Operations

---

### 55. DebugCLI [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/debugging/cli.py:15`

**Metrics**:
- Lines of Code: 290
- Method Count: 36
- Attribute Count: 2
- Cyclomatic Complexity: 74
- LCOM (Lack of Cohesion): 0.574

**Detected Responsibilities**:

- Do Operations

---

### 56. TestPytestRunner [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_pytest_runner.py:15`

**Metrics**:
- Lines of Code: 287
- Method Count: 54
- Attribute Count: 0
- Cyclomatic Complexity: 120
- LCOM (Lack of Cohesion): 0.074

**Detected Responsibilities**:

- Test Operations

---

### 57. PythonTestGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/execution/python_test_generator.py:22`

**Metrics**:
- Lines of Code: 285
- Method Count: 40
- Attribute Count: 2
- Cyclomatic Complexity: 67
- LCOM (Lack of Cohesion): 0.982

**Detected Responsibilities**:

- Convert Operations
- Generate Operations
- Translate Operations

---

### 58. TestBrobotMockAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_brobot_mock_analyzer.py:19`

**Metrics**:
- Lines of Code: 285
- Method Count: 32
- Attribute Count: 0
- Cyclomatic Complexity: 81
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Test Operations

---

### 59. ActionLifecycle [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/internal/execution/action_lifecycle.py:65`

**Metrics**:
- Lines of Code: 283
- Method Count: 46
- Attribute Count: 4
- Cyclomatic Complexity: 61
- LCOM (Lack of Cohesion): 0.416

**Detected Responsibilities**:

- Data Access
- Validate Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 21
  - Methods: `get_stage, get_state, get_duration`

---

### 60. StateText [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/special/state_text.py:96`

**Metrics**:
- Lines of Code: 279
- Method Count: 50
- Attribute Count: 9
- Cyclomatic Complexity: 44
- LCOM (Lack of Cohesion): 0.717

**Detected Responsibilities**:

- Add Operations
- Clear Operations
- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 36
  - Methods: `set_special_type, set_match_all, get_patterns, get_required_texts, get_forbidden_texts`

---

### 61. TestResultValidator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_result_validator.py:26`

**Metrics**:
- Lines of Code: 278
- Method Count: 34
- Attribute Count: 0
- Cyclomatic Complexity: 87
- LCOM (Lack of Cohesion): 0.228

**Detected Responsibilities**:

- Test Operations

---

### 62. HybridPathFinder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/navigation/hybrid_path_finder.py:87`

**Metrics**:
- Lines of Code: 275
- Method Count: 24
- Attribute Count: 0
- Cyclomatic Complexity: 53
- LCOM (Lack of Cohesion): 0.818

**Detected Responsibilities**:

- Find Operations

---

### 63. MigrationReportingDashboard [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/reporting/dashboard.py:23`

**Metrics**:
- Lines of Code: 275
- Method Count: 40
- Attribute Count: 2
- Cyclomatic Complexity: 53
- LCOM (Lack of Cohesion): 0.994

**Detected Responsibilities**:

- Analyze Operations
- Generate Operations
- Save Operations

---

### 64. ActionHistory [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/action/action_history.py:17`

**Metrics**:
- Lines of Code: 272
- Method Count: 44
- Attribute Count: 0
- Cyclomatic Complexity: 63
- LCOM (Lack of Cohesion): 0.758

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 12
  - Estimated Lines: 156
  - Methods: `get_records_by_state, get_records_by_action, get_recent_records, get_success_rate, get_average_duration, get_match_count_distribution, get_failure_patterns, get_mock_record, get_random_snapshot, get_snapshots`

---

### 65. PixelLocation [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/core/pixel_location.py:30`

**Metrics**:
- Lines of Code: 271
- Method Count: 38
- Attribute Count: 0
- Cyclomatic Complexity: 67
- LCOM (Lack of Cohesion): 0.608

**Detected Responsibilities**:

- Data Access
- From Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 78
  - Methods: `get_centroid, get_overlap_percentage, get_area, get_perimeter, get_compactness, get_contour`

---

### 66. StateRegistry [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/annotations/state_registry.py:36`

**Metrics**:
- Lines of Code: 270
- Method Count: 30
- Attribute Count: 0
- Cyclomatic Complexity: 59
- LCOM (Lack of Cohesion): 0.590

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 9
  - Estimated Lines: 99
  - Methods: `get_state, get_state_id, get_state_by_id, get_transition, get_initial_states, get_group_states, set_active_profile, get_transitions_for_state, get_statistics`

---

### 67. TestMigrationOrchestratorTests [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_migration_orchestrator.py:15`

**Metrics**:
- Lines of Code: 270
- Method Count: 32
- Attribute Count: 0
- Cyclomatic Complexity: 75
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Test Operations

---

### 68. PixelStabilityMatrixAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/pixel_stability_matrix_analyzer.py:34`

**Metrics**:
- Lines of Code: 266
- Method Count: 18
- Attribute Count: 3
- Cyclomatic Complexity: 54
- LCOM (Lack of Cohesion): 0.893

---

### 69. OutputFormatter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/cli_utils/output_formatter.py:8`

**Metrics**:
- Lines of Code: 265
- Method Count: 30
- Attribute Count: 0
- Cyclomatic Complexity: 48
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Display Operations
- Persistence
- Presentation

**Extraction Suggestions**:

- **PersistenceManager**
  - Responsibility: Persistence
  - Methods to Extract: 3
  - Estimated Lines: 66
  - Methods: `save_discovery_results, save_validation_report, save_migration_report`

- **Formatter**
  - Responsibility: Formatter
  - Methods to Extract: 3
  - Estimated Lines: 24
  - Methods: `display_discovery_results, display_validation_results, display_migration_results`

---

### 70. UnifiedCaptureService [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/capture/unified_capture_service.py:57`

**Metrics**:
- Lines of Code: 264
- Method Count: 32
- Attribute Count: 3
- Cyclomatic Complexity: 53
- LCOM (Lack of Cohesion): 0.581

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 36
  - Methods: `get_monitors, get_primary_monitor, set_provider, get_current_provider`

---

### 71. EnhancedActiveStateSet [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/state_management/enhanced_active_state_set.py:28`

**Metrics**:
- Lines of Code: 261
- Method Count: 46
- Attribute Count: 0
- Cyclomatic Complexity: 52
- LCOM (Lack of Cohesion): 0.636

**Detected Responsibilities**:

- Add Operations
- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 57
  - Methods: `get_active_states, get_visible_states, get_hidden_states, get_blocking_states, get_group_states, get_state_groups, get_statistics`

---

### 72. Mouse [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/wrappers/mouse.py:22`

**Metrics**:
- Lines of Code: 255
- Method Count: 24
- Attribute Count: 0
- Cyclomatic Complexity: 33
- LCOM (Lack of Cohesion): 1.000

---

### 73. ActionExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/internal/execution/action_executor.py:100`

**Metrics**:
- Lines of Code: 255
- Method Count: 40
- Attribute Count: 8
- Cyclomatic Complexity: 56
- LCOM (Lack of Cohesion): 0.614

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 31
  - Methods: `get_history, get_metrics, get_current_context, get_instance`

---

### 74. BasicDescriptionGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/description/basic_generator.py:13`

**Metrics**:
- Lines of Code: 255
- Method Count: 22
- Attribute Count: 0
- Cyclomatic Complexity: 81
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Describe Operations

---

### 75. ExecutionEnvironment [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/config/execution_environment.py:93`

**Metrics**:
- Lines of Code: 254
- Method Count: 24
- Attribute Count: 2
- Cyclomatic Complexity: 69
- LCOM (Lack of Cohesion): 0.818

**Detected Responsibilities**:

- Detect Operations

---

### 76. ExecutionModeController [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/wrappers/controller.py:40`

**Metrics**:
- Lines of Code: 254
- Method Count: 36
- Attribute Count: 7
- Cyclomatic Complexity: 30
- LCOM (Lack of Cohesion): 0.963

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 71
  - Methods: `get_instance, set_mock_mode, set_real_mode, set_screenshot_mode, get_execution_mode, get_recording_stats`

---

### 77. TestQontinuiMockGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_qontinui_mock_generator.py:9`

**Metrics**:
- Lines of Code: 254
- Method Count: 44
- Attribute Count: 0
- Cyclomatic Complexity: 124
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Test Operations

---

### 78. TestLLMTestTranslator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_llm_translator.py:19`

**Metrics**:
- Lines of Code: 253
- Method Count: 44
- Attribute Count: 0
- Cyclomatic Complexity: 100
- LCOM (Lack of Cohesion): 0.260

**Detected Responsibilities**:

- Test Operations

---

### 79. StateTransitionsJointTable [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/state_transitions_joint_table.py:28`

**Metrics**:
- Lines of Code: 252
- Method Count: 30
- Attribute Count: 6
- Cyclomatic Complexity: 67
- LCOM (Lack of Cohesion): 0.055

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 109
  - Methods: `get_transitions, get_all_transitions, get_registered_states, get_reachable_states, get_states_that_reach, find_transition, get_statistics`

---

### 80. RoutingContext [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/routing_context.py:40`

**Metrics**:
- Lines of Code: 250
- Method Count: 42
- Attribute Count: 7
- Cyclomatic Complexity: 49
- LCOM (Lack of Cohesion): 0.695

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 12
  - Estimated Lines: 125
  - Methods: `get_route_history, get_execution_path, get_path_with_outputs, get_visit_count, get_output_usage, get_unvisited_actions, get_branch_decisions, get_error_routes, get_execution_duration, get_statistics`

---

### 81. IntelligentRegionDetector [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/pixel_analysis/intelligent_detector.py:12`

**Metrics**:
- Lines of Code: 249
- Method Count: 22
- Attribute Count: 2
- Cyclomatic Complexity: 55
- LCOM (Lack of Cohesion): 0.978

**Detected Responsibilities**:

- Detect Operations

---

### 82. StateTransitionAspect [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/aspects/monitoring/state_transition_aspect.py:99`

**Metrics**:
- Lines of Code: 246
- Method Count: 30
- Attribute Count: 9
- Cyclomatic Complexity: 46
- LCOM (Lack of Cohesion): 0.681

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 48
  - Methods: `get_state_graph, get_transition_stats, get_unreachable_states, get_navigation_patterns`

---

### 83. RectangleDecomposer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/pixel_analysis/decomposer.py:12`

**Metrics**:
- Lines of Code: 245
- Method Count: 20
- Attribute Count: 1
- Cyclomatic Complexity: 56
- LCOM (Lack of Cohesion): 0.972

---

### 84. Image [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/image.py:22`

**Metrics**:
- Lines of Code: 240
- Method Count: 40
- Attribute Count: 0
- Cyclomatic Complexity: 38
- LCOM (Lack of Cohesion): 0.811

**Detected Responsibilities**:

- Data Access
- From Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 43
  - Methods: `get_empty_image, get_mat_bgr, get_mat_hsv`

---

### 85. SAM2Processor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/processors/sam2_processor.py:24`

**Metrics**:
- Lines of Code: 238
- Method Count: 24
- Attribute Count: 6
- Cyclomatic Complexity: 55
- LCOM (Lack of Cohesion): 0.909

---

### 86. FindImage [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/find/find_image.py:12`

**Metrics**:
- Lines of Code: 237
- Method Count: 42
- Attribute Count: 5
- Cyclomatic Complexity: 44
- LCOM (Lack of Cohesion): 0.889

---

### 87. StateTransitionService [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/state_transition_service.py:30`

**Metrics**:
- Lines of Code: 237
- Method Count: 30
- Attribute Count: 4
- Cyclomatic Complexity: 56
- LCOM (Lack of Cohesion): 0.615

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 86
  - Methods: `get_transitions_from, get_transition, get_history, get_registered_states, get_transition_graph, find_path`

---

### 88. TestPythonTestGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_python_test_generator.py:17`

**Metrics**:
- Lines of Code: 237
- Method Count: 54
- Attribute Count: 0
- Cyclomatic Complexity: 85
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Test Operations

---

### 89. SchedulerExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/scheduling/scheduler_executor.py:19`

**Metrics**:
- Lines of Code: 236
- Method Count: 30
- Attribute Count: 6
- Cyclomatic Complexity: 39
- LCOM (Lack of Cohesion): 0.121

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 41
  - Methods: `get_schedule, get_all_schedules, get_execution_history, get_statistics`

---

### 90. SemanticObject [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/core/semantic_object.py:38`

**Metrics**:
- Lines of Code: 235
- Method Count: 44
- Attribute Count: 0
- Cyclomatic Complexity: 30
- LCOM (Lack of Cohesion): 0.736

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 9
  - Estimated Lines: 66
  - Methods: `get_bounding_box, get_attribute, set_object_type, set_interactable, set_color, get_color, set_text, get_text, get_overlap_percentage`

---

### 91. ActionResultBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/result_builder.py:18`

**Metrics**:
- Lines of Code: 234
- Method Count: 40
- Attribute Count: 17
- Cyclomatic Complexity: 27
- LCOM (Lack of Cohesion): 0.865

**Detected Responsibilities**:

- Add Operations
- With Operations

---

### 92. BrobotMockAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/mocks/brobot_mock_analyzer.py:12`

**Metrics**:
- Lines of Code: 233
- Method Count: 26
- Attribute Count: 4
- Cyclomatic Complexity: 47
- LCOM (Lack of Cohesion): 0.985

**Detected Responsibilities**:

- Extract Operations
- Find Operations

---

### 93. Path [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/path.py:14`

**Metrics**:
- Lines of Code: 230
- Method Count: 52
- Attribute Count: 0
- Cyclomatic Complexity: 55
- LCOM (Lack of Cohesion): 0.320

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 8
  - Estimated Lines: 62
  - Methods: `get_state, get_transition, get_first_state, get_last_state, get_loops, get_score, get_probability, get_length`

---

### 94. TransitionSetProcessor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/annotations/transition_set_processor.py:26`

**Metrics**:
- Lines of Code: 228
- Method Count: 18
- Attribute Count: 3
- Cyclomatic Complexity: 37
- LCOM (Lack of Cohesion): 0.964

**Detected Responsibilities**:

- Find Operations

---

### 95. TestAssertionConverter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_assertion_converter.py:8`

**Metrics**:
- Lines of Code: 228
- Method Count: 48
- Attribute Count: 0
- Cyclomatic Complexity: 98
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Test Operations

---

### 96. IInputController [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/interfaces/input_controller.py:73`

**Metrics**:
- Lines of Code: 226
- Method Count: 38
- Attribute Count: 0
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Key Operations
- Mouse Operations

---

### 97. CodeStateTransition [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/navigation/transition/code_state_transition.py:14`

**Metrics**:
- Lines of Code: 226
- Method Count: 50
- Attribute Count: 0
- Cyclomatic Complexity: 38
- LCOM (Lack of Cohesion): 0.893

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 14
  - Estimated Lines: 89
  - Methods: `get_activated_states, get_deactivated_states, set_state_ids, get_task_sequence_optional, get_stays_visible_after_transition, set_stays_visible_after_transition, get_activate, set_activate, get_exit, set_exit`

---

### 98. MergeContext [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/merge_context.py:95`

**Metrics**:
- Lines of Code: 224
- Method Count: 44
- Attribute Count: 10
- Cyclomatic Complexity: 39
- LCOM (Lack of Cohesion): 0.148

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 11
  - Estimated Lines: 84
  - Methods: `get_received_inputs, get_pending_inputs, get_input_count, get_expected_count, get_merged_context, get_input_contexts, get_input_record, get_all_input_records, get_result, get_error`

---

### 99. HALFactory [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/factory.py:44`

**Metrics**:
- Lines of Code: 224
- Method Count: 22
- Attribute Count: 0
- Cyclomatic Complexity: 55
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 139
  - Methods: `get_screen_capture, get_pattern_matcher, get_input_controller, get_ocr_engine, get_platform_specific, get_instance_count`

---

### 100. VariableExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/variable_executor.py:37`

**Metrics**:
- Lines of Code: 219
- Method Count: 16
- Attribute Count: 3
- Cyclomatic Complexity: 25
- LCOM (Lack of Cohesion): 0.857

---

### 101. TestSpringTestAdapter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_spring_test_adapter.py:16`

**Metrics**:
- Lines of Code: 218
- Method Count: 30
- Attribute Count: 0
- Cyclomatic Complexity: 60
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Test Operations

---

### 102. ComprehensiveAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/reporting/comprehensive_analyzer.py:27`

**Metrics**:
- Lines of Code: 218
- Method Count: 14
- Attribute Count: 2
- Cyclomatic Complexity: 58
- LCOM (Lack of Cohesion): 0.933

---

### 103. PureActions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/pure.py:25`

**Metrics**:
- Lines of Code: 215
- Method Count: 30
- Attribute Count: 2
- Cyclomatic Complexity: 41
- LCOM (Lack of Cohesion): 0.396

**Detected Responsibilities**:

- Key Operations
- Mouse Operations

---

### 104. StateTransitionsJointTable [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/enhanced_joint_table.py:17`

**Metrics**:
- Lines of Code: 214
- Method Count: 34
- Attribute Count: 0
- Cyclomatic Complexity: 40
- LCOM (Lack of Cohesion): 0.596

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 12
  - Estimated Lines: 146
  - Methods: `get_transitions_from, get_transitions_to, get_transitions_to_activate, get_transitions_to_any, get_incoming_transitions, get_group, get_groups_for_state, get_initial_states, find_transition_between, get_states_with_transitions_to`

---

### 105. ExecutionPauseController [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/control/execution_pause_controller.py:47`

**Metrics**:
- Lines of Code: 213
- Method Count: 34
- Attribute Count: 6
- Cyclomatic Complexity: 46
- LCOM (Lack of Cohesion): 0.217

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 43
  - Methods: `set_global_pause, set_step_mode, get_pause_points, get_statistics`

---

### 106. ExecutionController [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/execution_controller.py:14`

**Metrics**:
- Lines of Code: 213
- Method Count: 40
- Attribute Count: 16
- Cyclomatic Complexity: 25
- LCOM (Lack of Cohesion): 0.708

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 31
  - Methods: `set_current_action, get_next_pending, set_context, set_pause_at_action`

---

### 107. FindPipeline [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/find_pipeline.py:23`

**Metrics**:
- Lines of Code: 210
- Method Count: 24
- Attribute Count: 0
- Cyclomatic Complexity: 53
- LCOM (Lack of Cohesion): 0.939

---

### 108. FluentActions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/fluent.py:82`

**Metrics**:
- Lines of Code: 209
- Method Count: 40
- Attribute Count: 3
- Cyclomatic Complexity: 31
- LCOM (Lack of Cohesion): 0.257

---

### 109. BreakpointManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/debugging/breakpoint_manager.py:15`

**Metrics**:
- Lines of Code: 208
- Method Count: 32
- Attribute Count: 2
- Cyclomatic Complexity: 42
- LCOM (Lack of Cohesion): 0.514

**Detected Responsibilities**:

- Add Operations

---

### 110. TextFindOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/options/text_find_options.py:54`

**Metrics**:
- Lines of Code: 208
- Method Count: 38
- Attribute Count: 0
- Cyclomatic Complexity: 29
- LCOM (Lack of Cohesion): 0.936

**Detected Responsibilities**:

- With Operations

---

### 111. Matches [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/find/matches.py:16`

**Metrics**:
- Lines of Code: 206
- Method Count: 58
- Attribute Count: 1
- Cyclomatic Complexity: 34
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Filter Operations

---

### 112. MockCapture [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/mock_capture.py:28`

**Metrics**:
- Lines of Code: 205
- Method Count: 22
- Attribute Count: 5
- Cyclomatic Complexity: 28
- LCOM (Lack of Cohesion): 0.822

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 53
  - Methods: `get_monitors, get_primary_monitor, get_screen_size, get_pixel_color`

---

### 113. PatternFindOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/options/pattern_find_options.py:29`

**Metrics**:
- Lines of Code: 204
- Method Count: 32
- Attribute Count: 0
- Cyclomatic Complexity: 28
- LCOM (Lack of Cohesion): 0.933

**Detected Responsibilities**:

- Add Operations
- With Operations

---

### 114. Wait [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/wait/wait.py:126`

**Metrics**:
- Lines of Code: 203
- Method Count: 34
- Attribute Count: 3
- Cyclomatic Complexity: 44
- LCOM (Lack of Cohesion): 0.700

**Detected Responsibilities**:

- Wait Operations

---

### 115. FilterExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/collection_operations/filter_executor.py:18`

**Metrics**:
- Lines of Code: 203
- Method Count: 16
- Attribute Count: 2
- Cyclomatic Complexity: 37
- LCOM (Lack of Cohesion): 0.952

**Detected Responsibilities**:

- Evaluate Operations

---

### 116. StateImage [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state_image.py:21`

**Metrics**:
- Lines of Code: 203
- Method Count: 50
- Attribute Count: 0
- Cyclomatic Complexity: 39
- LCOM (Lack of Cohesion): 0.897

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 12
  - Estimated Lines: 97
  - Methods: `get_pattern, set_fixed, set_shared, set_probability, set_search_region, set_similarity, set_search_regions, get_name, get_patterns, get_owner_state_name`

---

### 117. MatchBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/match/match.py:189`

**Metrics**:
- Lines of Code: 201
- Method Count: 32
- Attribute Count: 14
- Cyclomatic Complexity: 28
- LCOM (Lack of Cohesion): 0.771

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 14
  - Estimated Lines: 145
  - Methods: `set_match, set_region, set_position, set_offset, set_image, set_region_xywh, set_name, set_ocr_text, set_search_image, set_anchors`

---

### 118. TestJavaToPythonTranslator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_java_to_python_translator.py:17`

**Metrics**:
- Lines of Code: 200
- Method Count: 42
- Attribute Count: 0
- Cyclomatic Complexity: 81
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Test Operations

---

### 119. ConditionEvaluator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/control_flow/condition_evaluator.py:17`

**Metrics**:
- Lines of Code: 199
- Method Count: 14
- Attribute Count: 1
- Cyclomatic Complexity: 36
- LCOM (Lack of Cohesion): 0.933

**Detected Responsibilities**:

- Evaluate Operations

---

### 120. ActiveStateSet [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/statemanagement/active_state_set.py:17`

**Metrics**:
- Lines of Code: 198
- Method Count: 42
- Attribute Count: 0
- Cyclomatic Complexity: 44
- LCOM (Lack of Cohesion): 0.495

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 28
  - Methods: `get_active_states, get_state_ids, get_state_enums`

---

### 121. ObjectVectorizer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/perception/vectorization.py:10`

**Metrics**:
- Lines of Code: 197
- Method Count: 24
- Attribute Count: 4
- Cyclomatic Complexity: 35
- LCOM (Lack of Cohesion): 0.891

**Detected Responsibilities**:

- Extract Operations
- Vectorize Operations

---

### 122. SortExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/collection_operations/sort_executor.py:18`

**Metrics**:
- Lines of Code: 195
- Method Count: 16
- Attribute Count: 2
- Cyclomatic Complexity: 33
- LCOM (Lack of Cohesion): 1.000

---

### 123. ObjectCollectionBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/builders/object_collection_builder.py:22`

**Metrics**:
- Lines of Code: 194
- Method Count: 38
- Attribute Count: 5
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 0.712

**Detected Responsibilities**:

- Data Access
- With Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 45
  - Methods: `set_images, set_locations, set_regions, set_matches, set_strings`

---

### 124. FindTextOrchestrator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/implementations/find_text/find_text_orchestrator.py:39`

**Metrics**:
- Lines of Code: 194
- Method Count: 18
- Attribute Count: 0
- Cyclomatic Complexity: 46
- LCOM (Lack of Cohesion): 0.972

---

### 125. MetricsCollector [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/monitoring/metrics.py:111`

**Metrics**:
- Lines of Code: 193
- Method Count: 28
- Attribute Count: 5
- Cyclomatic Complexity: 37
- LCOM (Lack of Cohesion): 0.962

**Detected Responsibilities**:

- Data Access
- Record Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 18
  - Methods: `set_active_states, get_metrics, get_uptime`

---

### 126. BrobotTestScanner [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/discovery/scanner.py:22`

**Metrics**:
- Lines of Code: 193
- Method Count: 20
- Attribute Count: 3
- Cyclomatic Complexity: 44
- LCOM (Lack of Cohesion): 1.000

---

### 127. DebugSession [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/debugging/debug_session.py:15`

**Metrics**:
- Lines of Code: 189
- Method Count: 40
- Attribute Count: 13
- Cyclomatic Complexity: 39
- LCOM (Lack of Cohesion): 0.111

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 31
  - Methods: `get_snapshot, get_all_snapshots, get_info`

---

### 128. TypeAction [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/type/type_action.py:108`

**Metrics**:
- Lines of Code: 187
- Method Count: 42
- Attribute Count: 2
- Cyclomatic Complexity: 44
- LCOM (Lack of Cohesion): 0.900

**Detected Responsibilities**:

- Type Operations

---

### 129. OutputResolver [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/output_resolver.py:15`

**Metrics**:
- Lines of Code: 186
- Method Count: 20
- Attribute Count: 0
- Cyclomatic Complexity: 48
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access
- Resolve Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 66
  - Methods: `get_valid_outputs, get_output_description, get_expected_result_fields`

---

### 130. PatternOptimizer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/pattern_optimizer.py:17`

**Metrics**:
- Lines of Code: 186
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 28
- LCOM (Lack of Cohesion): 0.900

**Detected Responsibilities**:

- Optimize Operations

---

### 131. Action [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action.py:19`

**Metrics**:
- Lines of Code: 185
- Method Count: 14
- Attribute Count: 3
- Cyclomatic Complexity: 36
- LCOM (Lack of Cohesion): 0.933

---

### 132. FindAll [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/implementations/find_all.py:21`

**Metrics**:
- Lines of Code: 184
- Method Count: 16
- Attribute Count: 0
- Cyclomatic Complexity: 41
- LCOM (Lack of Cohesion): 0.964

**Detected Responsibilities**:

- Filter Operations

---

### 133. IPlatformSpecific [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/interfaces/platform_specific.py:58`

**Metrics**:
- Lines of Code: 183
- Method Count: 40
- Attribute Count: 0
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 13
  - Estimated Lines: 103
  - Methods: `get_all_windows, get_window_by_title, get_window_by_process, get_active_window, set_window_focus, get_ui_elements, find_ui_element, set_ui_text, get_ui_text, get_platform_name`

---

### 134. CrossStateAnchor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/cross_state_anchor.py:15`

**Metrics**:
- Lines of Code: 182
- Method Count: 34
- Attribute Count: 0
- Cyclomatic Complexity: 33
- LCOM (Lack of Cohesion): 0.338

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 66
  - Methods: `set_primary_object, set_default_anchor, set_strict_mode, get_anchor_for_state, get_location_for_state, get_states`

---

### 135. Keyboard [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/wrappers/keyboard.py:23`

**Metrics**:
- Lines of Code: 180
- Method Count: 20
- Attribute Count: 2
- Cyclomatic Complexity: 36
- LCOM (Lack of Cohesion): 1.000

---

### 136. StateTransition [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/state_transition.py:26`

**Metrics**:
- Lines of Code: 179
- Method Count: 40
- Attribute Count: 0
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 11
  - Estimated Lines: 69
  - Methods: `get_task_sequence_optional, get_stays_visible_after_transition, set_stays_visible_after_transition, get_activate, set_activate, get_exit, set_exit, get_score, set_score, get_times_successful`

---

### 137. MockActionHistoryFactory [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/mock_action_history_factory.py:14`

**Metrics**:
- Lines of Code: 176
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

---

### 138. StateMetadataTracker [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state_metadata_tracker.py:29`

**Metrics**:
- Lines of Code: 176
- Method Count: 32
- Attribute Count: 2
- Cyclomatic Complexity: 34
- LCOM (Lack of Cohesion): 0.000

**Detected Responsibilities**:

- Data Access
- Record Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 83
  - Methods: `get_metadata, get_access_count, get_transition_count, find_by_tag, get_custom_data, set_custom_data, get_most_accessed`

---

### 139. OCRProcessor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/processors/ocr_processor.py:30`

**Metrics**:
- Lines of Code: 176
- Method Count: 16
- Attribute Count: 2
- Cyclomatic Complexity: 46
- LCOM (Lack of Cohesion): 0.952

---

### 140. ActionValidator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/config/validator.py:22`

**Metrics**:
- Lines of Code: 175
- Method Count: 12
- Attribute Count: 1
- Cyclomatic Complexity: 57
- LCOM (Lack of Cohesion): 0.900

**Detected Responsibilities**:

- Validation

**Extraction Suggestions**:

- **Validator**
  - Responsibility: Validator
  - Methods to Extract: 4
  - Estimated Lines: 139
  - Methods: `validate_action, validate_actions, validate_action_sequence, check_circular_references`

---

### 141. ActionChain [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/chains/action_chain.py:97`

**Metrics**:
- Lines of Code: 174
- Method Count: 34
- Attribute Count: 3
- Cyclomatic Complexity: 27
- LCOM (Lack of Cohesion): 0.717

**Detected Responsibilities**:

- Add Operations
- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 22
  - Methods: `get_action_type, get_execution_history, get_current_index`

---

### 142. MultipleActions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/multiple/multiple_actions.py:120`

**Metrics**:
- Lines of Code: 174
- Method Count: 32
- Attribute Count: 5
- Cyclomatic Complexity: 37
- LCOM (Lack of Cohesion): 0.657

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 36
  - Methods: `get_action_type, get_results, get_successful_tasks, get_failed_tasks, get_execution_history`

---

### 143. StateTransitions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/state_transitions.py:19`

**Metrics**:
- Lines of Code: 174
- Method Count: 44
- Attribute Count: 0
- Cyclomatic Complexity: 42
- LCOM (Lack of Cohesion): 0.260

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 61
  - Methods: `get_state_name, get_transitions, get_from_state, get_to_state, get_between_states, get_by_type, get_best_transition`

---

### 144. ExecutionTracker [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/execution_tracker.py:15`

**Metrics**:
- Lines of Code: 172
- Method Count: 44
- Attribute Count: 14
- Cyclomatic Complexity: 33
- LCOM (Lack of Cohesion): 0.886

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 15
  - Estimated Lines: 91
  - Methods: `get_status, get_current_action, get_iteration_count, get_visited_actions, get_pending_count, get_history, get_action_record, get_failed_actions, get_completed_actions, get_context`

---

### 145. ReduceExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/collection_operations/reduce_executor.py:16`

**Metrics**:
- Lines of Code: 172
- Method Count: 16
- Attribute Count: 2
- Cyclomatic Complexity: 25
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Reduce Operations

---

### 146. ActionResult [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_result.py:20`

**Metrics**:
- Lines of Code: 171
- Method Count: 28
- Attribute Count: 17
- Cyclomatic Complexity: 26
- LCOM (Lack of Cohesion): 0.923

**Detected Responsibilities**:

- Add Operations

---

### 147. StableRegionExtractor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/pixel_analysis/extractor.py:12`

**Metrics**:
- Lines of Code: 171
- Method Count: 16
- Attribute Count: 3
- Cyclomatic Complexity: 40
- LCOM (Lack of Cohesion): 0.952

---

### 148. AnnotationProcessor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/annotations/annotation_processor.py:27`

**Metrics**:
- Lines of Code: 170
- Method Count: 14
- Attribute Count: 8
- Cyclomatic Complexity: 32
- LCOM (Lack of Cohesion): 0.867

---

### 149. BaseFindOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/options/base_find_options.py:43`

**Metrics**:
- Lines of Code: 170
- Method Count: 34
- Attribute Count: 0
- Cyclomatic Complexity: 27
- LCOM (Lack of Cohesion): 0.860

**Detected Responsibilities**:

- Data Access
- Enable Operations
- With Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 28
  - Methods: `get_strategy, find_all, find_first, find_best`

---

### 150. StateBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state.py:403`

**Metrics**:
- Lines of Code: 169
- Method Count: 30
- Attribute Count: 16
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 0.857

**Detected Responsibilities**:

- Data Access
- With Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 45
  - Methods: `set_blocking, set_path_score, set_base_mock_find_stochastic_modifier, set_is_initial, set_usable_area`

---

### 151. SearchRegions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/search_regions.py:14`

**Metrics**:
- Lines of Code: 168
- Method Count: 30
- Attribute Count: 2
- Cyclomatic Complexity: 36
- LCOM (Lack of Cohesion): 0.516

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 67
  - Methods: `set_fixed_region, set_regions, get_regions, get_fixed_if_defined_or_random_region, get_one_region, get_regions_for_search, get_fixed_region`

---

### 152. MockScreen [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/mock_screen.py:20`

**Metrics**:
- Lines of Code: 167
- Method Count: 30
- Attribute Count: 4
- Cyclomatic Complexity: 20
- LCOM (Lack of Cohesion): 0.791

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 9
  - Estimated Lines: 94
  - Methods: `get_screen_size, get_monitor_count, get_monitors, get_primary_monitor, get_pixel_color, set_mock_screen, get_mock_screen, set_screen_size, get_capture_count`

---

### 153. Click [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/click/click.py:17`

**Metrics**:
- Lines of Code: 167
- Method Count: 12
- Attribute Count: 4
- Cyclomatic Complexity: 35
- LCOM (Lack of Cohesion): 0.900

---

### 154. ExecutionContext [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/orchestration/execution_context.py:110`

**Metrics**:
- Lines of Code: 164
- Method Count: 42
- Attribute Count: 4
- Cyclomatic Complexity: 30
- LCOM (Lack of Cohesion): 0.732

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 46
  - Methods: `set_variable, get_variable, set_metadata, get_metadata, get_last_action_state, get_failed_actions`

---

### 155. Drag [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/drag/drag.py:22`

**Metrics**:
- Lines of Code: 163
- Method Count: 18
- Attribute Count: 2
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Create Operations

---

### 156. PairwiseStateAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/pixel_analysis/pairwise_analyzer.py:14`

**Metrics**:
- Lines of Code: 163
- Method Count: 14
- Attribute Count: 1
- Cyclomatic Complexity: 41
- LCOM (Lack of Cohesion): 0.933

---

### 157. ExecutionState [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/execution_state.py:25`

**Metrics**:
- Lines of Code: 161
- Method Count: 72
- Attribute Count: 5
- Cyclomatic Complexity: 38
- LCOM (Lack of Cohesion): 0.494

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 15
  - Estimated Lines: 45
  - Methods: `set_current_action, get_next_pending, set_context, set_pause_at_action, get_current_action, get_iteration_count, get_pending_count, get_history, get_action_record, get_failed_actions`

---

### 158. RelativeRegion [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/region/relative_region.py:26`

**Metrics**:
- Lines of Code: 161
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 27
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 92
  - Methods: `get_adjacent, get_grid_region, get_columns, get_rows`

---

### 159. ActionChainExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/internal/execution/action_chain_executor.py:16`

**Metrics**:
- Lines of Code: 161
- Method Count: 14
- Attribute Count: 2
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 0.800

**Detected Responsibilities**:

- Execute Operations

---

### 160. Key [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/keys.py:14`

**Metrics**:
- Lines of Code: 160
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 10
- LCOM (Lack of Cohesion): 1.000

---

### 161. Screen [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/wrappers/screen.py:24`

**Metrics**:
- Lines of Code: 160
- Method Count: 20
- Attribute Count: 0
- Cyclomatic Complexity: 24
- LCOM (Lack of Cohesion): 1.000

---

### 162. FindImageOrchestrator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/implementations/find_image/find_image_orchestrator.py:21`

**Metrics**:
- Lines of Code: 160
- Method Count: 18
- Attribute Count: 3
- Cyclomatic Complexity: 31
- LCOM (Lack of Cohesion): 1.000

---

### 163. MockInput [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/mock_input.py:14`

**Metrics**:
- Lines of Code: 159
- Method Count: 48
- Attribute Count: 3
- Cyclomatic Complexity: 47
- LCOM (Lack of Cohesion): 0.632

**Detected Responsibilities**:

- Data Access
- Key Operations
- Mouse Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 9
  - Methods: `get_mouse_position, get_action_history, get_last_action`

---

### 164. ErrorAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/reporting/error_analyzer.py:21`

**Metrics**:
- Lines of Code: 158
- Method Count: 24
- Attribute Count: 1
- Cyclomatic Complexity: 32
- LCOM (Lack of Cohesion): 0.964

**Detected Responsibilities**:

- Extract Operations

---

### 165. StateMemory [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/statemanagement/state_memory.py:35`

**Metrics**:
- Lines of Code: 150
- Method Count: 32
- Attribute Count: 0
- Cyclomatic Complexity: 32
- LCOM (Lack of Cohesion): 0.217

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 42
  - Methods: `get_active_state_list, get_active_state_names, set_active_states, get_active_state_count, set_expected_states`

---

### 166. ActionConfigBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_config.py:156`

**Metrics**:
- Lines of Code: 149
- Method Count: 26
- Attribute Count: 7
- Cyclomatic Complexity: 16
- LCOM (Lack of Cohesion): 0.848

**Detected Responsibilities**:

- Data Access
- With Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 57
  - Methods: `set_pause_before_begin, set_pause_after_end, set_success_criteria, set_illustrate, set_log_type, set_logging_options`

---

### 167. Text [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/text.py:11`

**Metrics**:
- Lines of Code: 149
- Method Count: 36
- Attribute Count: 0
- Cyclomatic Complexity: 25
- LCOM (Lack of Cohesion): 0.516

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 39
  - Methods: `get_all, get_most_common, get_unique, get_frequency, get_confidence`

---

### 168. QontinuiShutdownHandler [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/lifecycle/shutdown_handler.py:19`

**Metrics**:
- Lines of Code: 148
- Method Count: 26
- Attribute Count: 4
- Cyclomatic Complexity: 34
- LCOM (Lack of Cohesion): 0.924

**Detected Responsibilities**:

- Cleanup Operations

---

### 169. MockFind [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/mock_find.py:22`

**Metrics**:
- Lines of Code: 148
- Method Count: 16
- Attribute Count: 1
- Cyclomatic Complexity: 30
- LCOM (Lack of Cohesion): 0.905

---

### 170. RegionTransforms [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/region_transforms.py:14`

**Metrics**:
- Lines of Code: 145
- Method Count: 18
- Attribute Count: 0
- Cyclomatic Complexity: 15
- LCOM (Lack of Cohesion): 1.000

---

### 171. ActionRecord [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/snapshot.py:23`

**Metrics**:
- Lines of Code: 144
- Method Count: 12
- Attribute Count: 0
- Cyclomatic Complexity: 26
- LCOM (Lack of Cohesion): 1.000

---

### 172. ActionHistory [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/action_history.py:16`

**Metrics**:
- Lines of Code: 143
- Method Count: 36
- Attribute Count: 0
- Cyclomatic Complexity: 65
- LCOM (Lack of Cohesion): 0.307

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 9
  - Estimated Lines: 83
  - Methods: `get_snapshot, get_snapshots_by_action_type, get_snapshots_by_state, get_successful_snapshots, get_failed_snapshots, get_random_snapshot, get_transitions_from_screenshot, get_transitions_to_screenshot, get_statistics`

---

### 173. PatternFactory [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/pattern_factory.py:14`

**Metrics**:
- Lines of Code: 142
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 31
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- From Operations

---

### 174. CoverageComparator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/coverage_comparator.py:22`

**Metrics**:
- Lines of Code: 140
- Method Count: 14
- Attribute Count: 1
- Cyclomatic Complexity: 42
- LCOM (Lack of Cohesion): 0.933

**Detected Responsibilities**:

- Update Operations

---

### 175. Movement [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/movement.py:13`

**Metrics**:
- Lines of Code: 139
- Method Count: 32
- Attribute Count: 0
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 0.650

---

### 176. StateString [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state_string.py:18`

**Metrics**:
- Lines of Code: 139
- Method Count: 36
- Attribute Count: 0
- Cyclomatic Complexity: 27
- LCOM (Lack of Cohesion): 0.869

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 8
  - Estimated Lines: 62
  - Methods: `find_on_screen, get_string, set_identifier, set_input_text, set_expected_text, set_regex, get_owner_state_name, set_times_acted_on`

---

### 177. StateEventEmitter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/state_management/event_emitter.py:31`

**Metrics**:
- Lines of Code: 138
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 18
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Emit Operations

---

### 178. Anchor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/anchor.py:33`

**Metrics**:
- Lines of Code: 138
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 0.857

---

### 179. InitialStates [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/initial_states.py:15`

**Metrics**:
- Lines of Code: 138
- Method Count: 30
- Attribute Count: 0
- Cyclomatic Complexity: 26
- LCOM (Lack of Cohesion): 0.419

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 47
  - Methods: `get_state, get_all_states, get_state_names, set_default_state, get_default_state, get_default_state_name`

---

### 180. ApplicationLifecycleService [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/lifecycle/application_lifecycle_service.py:19`

**Metrics**:
- Lines of Code: 137
- Method Count: 18
- Attribute Count: 1
- Cyclomatic Complexity: 20
- LCOM (Lack of Cohesion): 0.893

---

### 181. StateNavigationExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/state_management/state_navigation_executor.py:63`

**Metrics**:
- Lines of Code: 137
- Method Count: 12
- Attribute Count: 2
- Cyclomatic Complexity: 15
- LCOM (Lack of Cohesion): 0.900

---

### 182. TransitionExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/state_management/transition_executor.py:61`

**Metrics**:
- Lines of Code: 136
- Method Count: 14
- Attribute Count: 4
- Cyclomatic Complexity: 13
- LCOM (Lack of Cohesion): 0.867

---

### 183. StateMetricsManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/managers/state_metrics_manager.py:18`

**Metrics**:
- Lines of Code: 135
- Method Count: 38
- Attribute Count: 0
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 0.836

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 14
  - Estimated Lines: 81
  - Methods: `get_visit_count, set_probability_exists, get_probability_exists, set_probability_to_base_probability, set_base_mock_find_stochastic_modifier, get_base_mock_find_stochastic_modifier, set_path_score, get_path_score, set_is_initial, get_last_accessed`

---

### 184. TaskExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/scheduling/task_executor.py:17`

**Metrics**:
- Lines of Code: 133
- Method Count: 12
- Attribute Count: 6
- Cyclomatic Complexity: 23
- LCOM (Lack of Cohesion): 0.800

---

### 185. MapExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/collection_operations/map_executor.py:16`

**Metrics**:
- Lines of Code: 133
- Method Count: 12
- Attribute Count: 2
- Cyclomatic Complexity: 19
- LCOM (Lack of Cohesion): 0.900

**Detected Responsibilities**:

- Map Operations

---

### 186. Positions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/positions.py:26`

**Metrics**:
- Lines of Code: 130
- Method Count: 16
- Attribute Count: 0
- Cyclomatic Complexity: 11
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 24
  - Methods: `get_coordinates, get_x, get_y`

---

### 187. DiagnosticReporter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/diagnostics/diagnostic_reporter.py:14`

**Metrics**:
- Lines of Code: 129
- Method Count: 16
- Attribute Count: 0
- Cyclomatic Complexity: 29
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Print Operations

---

### 188. StateRegion [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state_region.py:20`

**Metrics**:
- Lines of Code: 129
- Method Count: 34
- Attribute Count: 0
- Cyclomatic Complexity: 23
- LCOM (Lack of Cohesion): 0.868

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 8
  - Estimated Lines: 57
  - Methods: `get_center, set_fixed, set_search_region, set_interaction_region, get_name, get_owner_state_name, get_search_region, set_times_acted_on`

---

### 189. ReportDataCollector [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/reporting/report_data_collector.py:18`

**Metrics**:
- Lines of Code: 122
- Method Count: 18
- Attribute Count: 2
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Extract Operations

---

### 190. FindColorOrchestrator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/color/find_color_orchestrator.py:22`

**Metrics**:
- Lines of Code: 121
- Method Count: 16
- Attribute Count: 3
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 1.000

---

### 191. RegionGeometry [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/region_geometry.py:15`

**Metrics**:
- Lines of Code: 120
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 22
- LCOM (Lack of Cohesion): 1.000

---

### 192. Anchors [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/element/anchors.py:12`

**Metrics**:
- Lines of Code: 116
- Method Count: 30
- Attribute Count: 0
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 0.562

---

### 193. StateVisibilityManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/managers/state_visibility_manager.py:13`

**Metrics**:
- Lines of Code: 114
- Method Count: 32
- Attribute Count: 0
- Cyclomatic Complexity: 18
- LCOM (Lack of Cohesion): 0.767

**Detected Responsibilities**:

- Add Operations

---

### 194. Highlight [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/highlight/highlight.py:17`

**Metrics**:
- Lines of Code: 113
- Method Count: 12
- Attribute Count: 1
- Cyclomatic Complexity: 23
- LCOM (Lack of Cohesion): 1.000

---

### 195. SemanticProcessor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/processors/base.py:224`

**Metrics**:
- Lines of Code: 113
- Method Count: 24
- Attribute Count: 3
- Cyclomatic Complexity: 19
- LCOM (Lack of Cohesion): 0.891

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 26
  - Methods: `get_configuration, get_supported_object_types, get_average_processing_time, set_max_processing_time`

---

### 196. ImagePreprocessor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/implementations/find_text/image_preprocessor.py:16`

**Metrics**:
- Lines of Code: 112
- Method Count: 16
- Attribute Count: 2
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 0.952

---

### 197. RetryPolicy [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/orchestration/retry_policy.py:26`

**Metrics**:
- Lines of Code: 109
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 17
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- With Operations

---

### 198. ImportSuggestionStrategy [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/strategies/import_suggestions.py:12`

**Metrics**:
- Lines of Code: 109
- Method Count: 14
- Attribute Count: 2
- Cyclomatic Complexity: 12
- LCOM (Lack of Cohesion): 1.000

---

### 199. Scroll [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/scroll/scroll.py:17`

**Metrics**:
- Lines of Code: 108
- Method Count: 10
- Attribute Count: 1
- Cyclomatic Complexity: 25
- LCOM (Lack of Cohesion): 1.000

---

### 200. PatternFindOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/pattern_find_options.py:43`

**Metrics**:
- Lines of Code: 107
- Method Count: 16
- Attribute Count: 3
- Cyclomatic Complexity: 14
- LCOM (Lack of Cohesion): 0.952

**Detected Responsibilities**:

- Data Access
- For Operations

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 24
  - Methods: `get_find_strategy, get_strategy, get_do_on_each, get_match_fusion_options`

---

### 201. IPatternMatcher [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/interfaces/pattern_matcher.py:51`

**Metrics**:
- Lines of Code: 107
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 62
  - Methods: `find_pattern, find_all_patterns, find_features, find_template_multiscale`

---

### 202. IOCREngine [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/interfaces/ocr_engine.py:42`

**Metrics**:
- Lines of Code: 106
- Method Count: 16
- Attribute Count: 0
- Cyclomatic Complexity: 10
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 44
  - Methods: `get_text_regions, find_text, find_all_text, get_supported_languages`

---

### 203. ResultExtractor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/result_extractors.py:15`

**Metrics**:
- Lines of Code: 102
- Method Count: 16
- Attribute Count: 0
- Cyclomatic Complexity: 24
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 66
  - Methods: `get_best_match, get_best_location, get_match_locations, get_success_symbol, get_summary`

---

### 204. OutputValidator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/validation_strategies/output_validator.py:19`

**Metrics**:
- Lines of Code: 102
- Method Count: 12
- Attribute Count: 2
- Cyclomatic Complexity: 25
- LCOM (Lack of Cohesion): 0.900

---

### 205. ColorFindOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/color/color_find_options.py:71`

**Metrics**:
- Lines of Code: 101
- Method Count: 18
- Attribute Count: 0
- Cyclomatic Complexity: 16
- LCOM (Lack of Cohesion): 0.889

**Detected Responsibilities**:

- With Operations

---

### 206. CollectionExecutor [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/data_operations/collection_operations/collection_executor.py:20`

**Metrics**:
- Lines of Code: 101
- Method Count: 10
- Attribute Count: 4
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 1.000

---

### 207. SuggestionScorer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/strategies/suggestion_scorer.py:11`

**Metrics**:
- Lines of Code: 101
- Method Count: 12
- Attribute Count: 1
- Cyclomatic Complexity: 10
- LCOM (Lack of Cohesion): 0.900

---

### 208. ClickWithModifiers [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/click_with_modifiers.py:15`

**Metrics**:
- Lines of Code: 100
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 19
- LCOM (Lack of Cohesion): 1.000

---

### 209. DescriptionGenerator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/semantic/description/base.py:11`

**Metrics**:
- Lines of Code: 99
- Method Count: 16
- Attribute Count: 1
- Cyclomatic Complexity: 16
- LCOM (Lack of Cohesion): 0.952

---

### 210. Match [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/match/match.py:56`

**Metrics**:
- Lines of Code: 97
- Method Count: 20
- Attribute Count: 0
- Cyclomatic Complexity: 19
- LCOM (Lack of Cohesion): 0.844

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 23
  - Methods: `get_target, get_region, set_region`

---

### 211. UnknownState [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/special/unknown_state.py:31`

**Metrics**:
- Lines of Code: 96
- Method Count: 20
- Attribute Count: 1
- Cyclomatic Complexity: 14
- LCOM (Lack of Cohesion): 0.833

---

### 212. PersistenceProvider [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/persistence/persistence_provider.py:55`

**Metrics**:
- Lines of Code: 95
- Method Count: 26
- Attribute Count: 0
- Cyclomatic Complexity: 15
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 20
  - Methods: `get_all_sessions, get_session_metadata, get_current_session_id`

---

### 213. PixelStabilityAnalyzer [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/discovery/pixel_analysis/analyzers/pixel_stability_analyzer.py:20`

**Metrics**:
- Lines of Code: 94
- Method Count: 10
- Attribute Count: 8
- Cyclomatic Complexity: 18
- LCOM (Lack of Cohesion): 0.833

---

### 214. ExecutionController [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/control/execution_controller.py:26`

**Metrics**:
- Lines of Code: 93
- Method Count: 20
- Attribute Count: 0
- Cyclomatic Complexity: 12
- LCOM (Lack of Cohesion): 1.000

---

### 215. ExceptionValidator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/validation_strategies/exception_validator.py:20`

**Metrics**:
- Lines of Code: 93
- Method Count: 10
- Attribute Count: 2
- Cyclomatic Complexity: 24
- LCOM (Lack of Cohesion): 0.833

---

### 216. ActionDefaults [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/config/action_defaults.py:75`

**Metrics**:
- Lines of Code: 92
- Method Count: 10
- Attribute Count: 4
- Cyclomatic Complexity: 24
- LCOM (Lack of Cohesion): 1.000

---

### 217. MockActionHistoryBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/mock_action_history_factory.py:222`

**Metrics**:
- Lines of Code: 92
- Method Count: 22
- Attribute Count: 9
- Cyclomatic Complexity: 16
- LCOM (Lack of Cohesion): 0.800

---

### 218. TransitionParser [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/json_executor/parsers/transition_parser.py:10`

**Metrics**:
- Lines of Code: 91
- Method Count: 12
- Attribute Count: 0
- Cyclomatic Complexity: 17
- LCOM (Lack of Cohesion): 1.000

---

### 219. StateTransition [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/enhanced_state_transition.py:66`

**Metrics**:
- Lines of Code: 91
- Method Count: 18
- Attribute Count: 0
- Cyclomatic Complexity: 13
- LCOM (Lack of Cohesion): 0.833

---

### 220. AssertionValidator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/validation_strategies/assertion_validator.py:31`

**Metrics**:
- Lines of Code: 90
- Method Count: 10
- Attribute Count: 1
- Cyclomatic Complexity: 21
- LCOM (Lack of Cohesion): 0.833

---

### 221. SuggestionFormatter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/strategies/suggestion_formatter.py:11`

**Metrics**:
- Lines of Code: 88
- Method Count: 10
- Attribute Count: 3
- Cyclomatic Complexity: 27
- LCOM (Lack of Cohesion): 1.000

---

### 222. MockModeManager [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/mock/mock_mode_manager.py:12`

**Metrics**:
- Lines of Code: 87
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 20
- LCOM (Lack of Cohesion): 1.000

---

### 223. SpecialStateType [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/special/special_state_type.py:9`

**Metrics**:
- Lines of Code: 87
- Method Count: 20
- Attribute Count: 0
- Cyclomatic Complexity: 14
- LCOM (Lack of Cohesion): 0.978

---

### 224. HighlightOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/highlight/highlight_options.py:52`

**Metrics**:
- Lines of Code: 81
- Method Count: 16
- Attribute Count: 5
- Cyclomatic Complexity: 11
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 5
  - Estimated Lines: 47
  - Methods: `set_highlight_duration, set_color, set_thickness, set_flash, set_flash_times`

---

### 225. MatchQueries [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/find/match_operations/match_queries.py:10`

**Metrics**:
- Lines of Code: 81
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 17
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 69
  - Methods: `get_at_index, get_first, get_last, get_best, get_worst, get_nearest_to, get_farthest_from`

---

### 226. EmptyMatch [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/match/empty_match.py:10`

**Metrics**:
- Lines of Code: 81
- Method Count: 16
- Attribute Count: 6
- Cyclomatic Complexity: 10
- LCOM (Lack of Cohesion): 0.857

---

### 227. DSLParser [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/runner/json/dsl_parser.py:18`

**Metrics**:
- Lines of Code: 80
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 20
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Parse Operations

---

### 228. QontinuiDSLParser [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/dsl/parser.py:450`

**Metrics**:
- Lines of Code: 79
- Method Count: 10
- Attribute Count: 1
- Cyclomatic Complexity: 16
- LCOM (Lack of Cohesion): 0.833

---

### 229. PerformanceValidator [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/validation/validation_strategies/performance_validator.py:41`

**Metrics**:
- Lines of Code: 79
- Method Count: 10
- Attribute Count: 1
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 0.833

---

### 230. TestTestMigrationConfig [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/tests/test_config.py:13`

**Metrics**:
- Lines of Code: 78
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 56
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Test Operations

---

### 231. MatchFilters [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/find/match_operations/match_filters.py:12`

**Metrics**:
- Lines of Code: 75
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 26
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- By Operations

---

### 232. IScreenCapture [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/hal/interfaces/screen_capture.py:32`

**Metrics**:
- Lines of Code: 74
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 28
  - Methods: `get_monitors, get_primary_monitor, get_screen_size, get_pixel_color`

---

### 233. ActionConfig [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_config.py:61`

**Metrics**:
- Lines of Code: 73
- Method Count: 16
- Attribute Count: 7
- Cyclomatic Complexity: 11
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 7
  - Estimated Lines: 42
  - Methods: `get_pause_before_begin, get_pause_after_end, get_success_criteria, get_illustrate, get_subsequent_actions, get_log_type, get_logging_options`

---

### 234. ClickOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/click/click_options.py:81`

**Metrics**:
- Lines of Code: 72
- Method Count: 14
- Attribute Count: 4
- Cyclomatic Complexity: 10
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 40
  - Methods: `set_number_of_clicks, set_press_options, set_verification, set_repetition`

---

### 235. TestMigrationConfig [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/test_migration/config.py:11`

**Metrics**:
- Lines of Code: 69
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 21
  - Methods: `get_dependency_mapping, get_brobot_mock_mappings, get_pytest_markers`

---

### 236. ScrollOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/scroll/scroll_options.py:58`

**Metrics**:
- Lines of Code: 68
- Method Count: 14
- Attribute Count: 4
- Cyclomatic Complexity: 10
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 36
  - Methods: `set_direction, set_clicks, set_smooth, set_delay_between_scrolls`

---

### 237. StateObject [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/state_object.py:25`

**Metrics**:
- Lines of Code: 68
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 36
  - Methods: `get_id_as_string, get_object_type, get_name, get_owner_state_name, get_owner_state_id, set_times_acted_on`

---

### 238. Direction [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/transition/direction.py:9`

**Metrics**:
- Lines of Code: 67
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

---

### 239. NullState [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/state/special/null_state.py:27`

**Metrics**:
- Lines of Code: 67
- Method Count: 14
- Attribute Count: 1
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 0.933

---

### 240. ExecutionState [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/control/execution_state.py:9`

**Metrics**:
- Lines of Code: 64
- Method Count: 16
- Attribute Count: 1
- Cyclomatic Complexity: 10
- LCOM (Lack of Cohesion): 1.000

---

### 241. MatchGeometry [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/match/match_geometry.py:16`

**Metrics**:
- Lines of Code: 64
- Method Count: 12
- Attribute Count: 0
- Cyclomatic Complexity: 16
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 56
  - Methods: `get_center, get_x, get_y, get_width, get_height, get_area`

---

### 242. PatternFindOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/pattern_find_options.py:174`

**Metrics**:
- Lines of Code: 62
- Method Count: 12
- Attribute Count: 3
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 29
  - Methods: `set_strategy, set_do_on_each, set_match_fusion`

---

### 243. TypeOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/type/type_action.py:27`

**Metrics**:
- Lines of Code: 62
- Method Count: 14
- Attribute Count: 0
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 0.857

---

### 244. HistogramRegion [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/analysis/histogram/histogram_region.py:11`

**Metrics**:
- Lines of Code: 62
- Method Count: 12
- Attribute Count: 0
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 0.800

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 36
  - Methods: `get_masks, set_masks, get_histograms, set_histograms, get_histogram, set_histogram`

---

### 245. DragOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/drag/drag_options.py:91`

**Metrics**:
- Lines of Code: 61
- Method Count: 12
- Attribute Count: 3
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 29
  - Methods: `set_mouse_press_options, set_delay_between_mouse_down_and_move, set_delay_after_drag`

---

### 246. DragOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/drag/drag_options.py:10`

**Metrics**:
- Lines of Code: 60
- Method Count: 20
- Attribute Count: 3
- Cyclomatic Complexity: 12
- LCOM (Lack of Cohesion): 0.917

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 9
  - Estimated Lines: 45
  - Methods: `get_mouse_press_options, get_delay_between_mouse_down_and_move, get_delay_after_drag, get_find_source_options, get_find_target_options, get_move_to_source_options, get_mouse_down_options, get_move_to_target_options, get_mouse_up_options`

---

### 247. RunProcessOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/process/run_process_options.py:61`

**Metrics**:
- Lines of Code: 59
- Method Count: 10
- Attribute Count: 2
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 0.833

---

### 248. FindOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_options.py:314`

**Metrics**:
- Lines of Code: 58
- Method Count: 18
- Attribute Count: 7
- Cyclomatic Complexity: 11
- LCOM (Lack of Cohesion): 1.000

---

### 249. BaseFindOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/find/base_find_options.py:21`

**Metrics**:
- Lines of Code: 57
- Method Count: 18
- Attribute Count: 7
- Cyclomatic Complexity: 11
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 8
  - Estimated Lines: 30
  - Methods: `get_find_strategy, get_similarity, get_search_regions, get_capture_image, get_use_defined_region, get_max_matches_to_act_on, get_match_adjustment_options, get_search_duration`

---

### 250. MouseButton [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/model/action/mouse_button.py:9`

**Metrics**:
- Lines of Code: 57
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

---

### 251. KeyUpOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/type/key_up_options.py:12`

**Metrics**:
- Lines of Code: 55
- Method Count: 10
- Attribute Count: 0
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 0.900

---

### 252. ClickOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/click/click_options.py:12`

**Metrics**:
- Lines of Code: 53
- Method Count: 14
- Attribute Count: 4
- Cyclomatic Complexity: 9
- LCOM (Lack of Cohesion): 0.800

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 6
  - Estimated Lines: 24
  - Methods: `get_number_of_clicks, get_mouse_press_options, get_verification_options, get_repetition_options, get_times_to_repeat_individual_action, get_pause_between_individual_actions`

---

### 253. KeyCombo [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/keys.py:216`

**Metrics**:
- Lines of Code: 49
- Method Count: 12
- Attribute Count: 3
- Cyclomatic Complexity: 17
- LCOM (Lack of Cohesion): 1.000

---

### 254. TypeOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/type/type_options.py:43`

**Metrics**:
- Lines of Code: 48
- Method Count: 10
- Attribute Count: 2
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

---

### 255. MergeStrategy [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/execution/merge_algorithms/merge_base.py:11`

**Metrics**:
- Lines of Code: 48
- Method Count: 10
- Attribute Count: 2
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 1.000

---

### 256. ScrollOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/mouse/scroll_options.py:54`

**Metrics**:
- Lines of Code: 47
- Method Count: 10
- Attribute Count: 2
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

---

### 257. VanishOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/vanish/vanish_options.py:43`

**Metrics**:
- Lines of Code: 46
- Method Count: 10
- Attribute Count: 2
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

---

### 258. ActionChainOptionsBuilder [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_chain_options.py:64`

**Metrics**:
- Lines of Code: 43
- Method Count: 10
- Attribute Count: 3
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 1.000

---

### 259. ProcessRepetitionOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/process/process_repetition_options.py:10`

**Metrics**:
- Lines of Code: 42
- Method Count: 12
- Attribute Count: 0
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 12
  - Methods: `get_enabled, get_max_repeats, get_delay, get_until_success`

---

### 260. RunProcessOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/composite/process/run_process_options.py:10`

**Metrics**:
- Lines of Code: 38
- Method Count: 10
- Attribute Count: 2
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 1.000

---

### 261. DragOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_options.py:89`

**Metrics**:
- Lines of Code: 34
- Method Count: 12
- Attribute Count: 6
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

---

### 262. GetTextOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_options.py:390`

**Metrics**:
- Lines of Code: 34
- Method Count: 12
- Attribute Count: 6
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

---

### 263. MouseAdapter [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/adapter_impl/mouse_adapter.py:11`

**Metrics**:
- Lines of Code: 32
- Method Count: 12
- Attribute Count: 0
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Mouse Operations

---

### 264. HighlightOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/highlight/highlight_options.py:9`

**Metrics**:
- Lines of Code: 32
- Method Count: 12
- Attribute Count: 5
- Cyclomatic Complexity: 8
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 4
  - Estimated Lines: 12
  - Methods: `get_highlight_duration, get_color, get_thickness, get_flash_times`

---

### 265. TypeOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_options.py:165`

**Metrics**:
- Lines of Code: 29
- Method Count: 10
- Attribute Count: 5
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 1.000

---

### 266. ScrollOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/action_options.py:246`

**Metrics**:
- Lines of Code: 29
- Method Count: 10
- Attribute Count: 5
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Scroll Operations

---

### 267. ScrollOptions [MEDIUM]

**File**: `/mnt/c/Users/jspin/Documents/qontinui_parent/qontinui/src/qontinui/actions/basic/scroll/scroll_options.py:20`

**Metrics**:
- Lines of Code: 28
- Method Count: 10
- Attribute Count: 4
- Cyclomatic Complexity: 7
- LCOM (Lack of Cohesion): 1.000

**Detected Responsibilities**:

- Data Access

**Extraction Suggestions**:

- **DataAccessor**
  - Responsibility: DataAccessor
  - Methods to Extract: 3
  - Estimated Lines: 9
  - Methods: `get_direction, get_clicks, get_delay_between_scrolls`

---

## Recommendations

1. **Refactor Critical Classes First**: Focus on classes with 'critical' severity.
2. **Extract Responsibilities**: Use the extraction suggestions to create new, focused classes.
3. **Apply Single Responsibility Principle**: Each class should have one reason to change.
4. **Improve Cohesion**: Methods in a class should work together on related data.
5. **Use Composition**: Break large classes into smaller, composable components.

## LCOM Interpretation

- **0.0 - 0.3**: Good cohesion (methods work together)
- **0.3 - 0.6**: Moderate cohesion (some refactoring may help)
- **0.6 - 0.8**: Poor cohesion (strong candidate for refactoring)
- **0.8 - 1.0**: Very poor cohesion (urgent refactoring needed)
