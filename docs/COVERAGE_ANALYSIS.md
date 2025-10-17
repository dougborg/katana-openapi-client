# Code Coverage Analysis

## TL;DR

**Overall Coverage: 23.1%** sounds low, but this is misleading!

**Core Logic Coverage: 74.8%** ✅ - This is what actually matters.

The 23% overall number includes ~30,000 lines of generated API and model code that don't
need comprehensive test coverage.

______________________________________________________________________

## Understanding the Numbers

### What Coverage Really Means

```
Overall Coverage: 23.1%
├── Generated API (197 files, 10,517 lines): 0.6% ❌ Don't worry about this!
├── Generated Models (337 files, 19,911 lines): 33.5% ❌ Don't worry about this!
└── Core Logic (5 files, 524 lines): 74.8% ✅ This is what matters!
```

### Why Generated Code Has Low Coverage

1. **API Modules** (197 files in `api/`):

   - Auto-generated from OpenAPI spec
   - Mostly boilerplate request building
   - Tested indirectly through integration tests
   - **Not a priority for direct unit tests**

1. **Model Classes** (337 files in `models/`):

   - Auto-generated data classes
   - Simple serialization/deserialization
   - Tested by using them in actual API calls
   - **Not a priority for direct unit tests**

1. **Why This is OK**:

   - The code generator (openapi-python-client) is well-tested
   - We test the generator's output works correctly via integration tests
   - Direct unit testing of generated boilerplate is low value

______________________________________________________________________

## Core Logic Breakdown

### Files and Current Coverage

| File               | Coverage | Status       | Priority                  |
| ------------------ | -------- | ------------ | ------------------------- |
| `utils.py`         | 98.1%    | ✅ Excellent | Maintain                  |
| `katana_client.py` | 85.3%    | ✅ Good      | Maintain, improve to 90%+ |
| `__init__.py`      | 100.0%   | ✅ Perfect   | Maintain                  |
| `client.py`        | 51.3%    | ⚠️ Moderate  | Improve to 70%+           |
| `log_setup.py`     | 0.0%     | ❌ None      | Add basic tests           |

### What Each File Does

#### ✅ `utils.py` (98.1% coverage, 31 tests)

**Purpose**: Response unwrapping and error handling utilities

**Well Tested:**

- `unwrap()` - extract parsed data from responses
- `unwrap_data()` - extract `.data` field with type overloads
- `is_success()`, `is_error()` - status checking
- Custom exceptions (APIError, ValidationError, etc.)

**Why Coverage is High:**

- Recently added with TDD approach
- Comprehensive test suite in `tests/test_utils.py`
- Edge cases well covered

**Action**: ✅ Maintain current excellent coverage

______________________________________________________________________

#### ✅ `katana_client.py` (85.3% coverage, 27 tests)

**Purpose**: Enhanced client with transport-layer resilience

**Well Tested:**

- Basic client initialization
- Configuration loading from environment
- Context manager behavior
- Some transport scenarios

**Missing Coverage (15%):**

- Edge cases in `RateLimitAwareRetry`
  - Unknown HTTP methods
  - Method preservation across retry attempts
- Edge cases in `ErrorLoggingTransport`
  - Deeply nested error responses
  - UNSET field handling
- `AutoPaginationTransport` edge cases
  - Max pages limit
  - Malformed pagination headers

**Why Coverage is Good:**

- Core resilience logic is tested
- Main use cases covered
- Integration tests exercise transport layer

**Action**: ⚠️ Add tests for edge cases to reach 90%+ (see issue #31)

______________________________________________________________________

#### ⚠️ `client.py` (51.3% coverage)

**Purpose**: Base generated client classes

**Partially Tested:**

- Basic client initialization
- Some request building

**Missing Coverage (49%):**

- Advanced authentication patterns
- Client configuration edge cases
- Error path scenarios
- Context manager edge cases

**Why Coverage is Moderate:**

- Generated code, tested indirectly
- Core paths are covered
- Advanced features less commonly used

**Action**: ⚠️ Add tests for commonly used patterns, target 70%

______________________________________________________________________

#### ❌ `log_setup.py` (0% coverage)

**Purpose**: Logging configuration utilities

**No Tests:**

- Logger initialization
- Log level configuration
- Handler setup

**Why No Coverage:**

- Simple utility module
- Used automatically at import
- Low complexity code

**Action**: ❌ Add basic smoke tests, target 60%+

______________________________________________________________________

## How to View Coverage Analysis

### Run Coverage Report

```bash
# Generate coverage data
poetry run pytest --cov=katana_public_api_client --cov-report=json -m 'not docs'

# Analyze by category
poetry run poe analyze-coverage
```

### Output Example

```
================================================================================
COVERAGE ANALYSIS - Generated vs. Core Logic
================================================================================

📊 Overall Coverage: 23.1%
   Total Files: 541
   Total Statements: 30,984
   Covered: 7,159
   Missing: 23,825

📁 Coverage by Category:

🤖 Generated Api:
   Files: 197
   Statements: 10,517
   Coverage: 0.6% (low coverage OK - generated code)

⚙️ Core Logic:
   Files: 5
   Statements: 524
   Coverage: 74.8% (target: 70%+)

--------------------------------------------------------------------------------
⚙️  CORE LOGIC DETAIL (Target: 70%+)
--------------------------------------------------------------------------------

❌ log_setup.py                     0.0% (0/34)
⚠️ client.py                       51.3% (60/117)
✅ katana_client.py                85.3% (226/265)
✅ utils.py                        98.1% (102/104)
✅ __init__.py                    100.0% (4/4)
```

______________________________________________________________________

## Improving Coverage

### Priority 1: `katana_client.py` (85% → 90%+)

Add tests for edge cases:

```python
# tests/test_rate_limit_retry_edge_cases.py

def test_unknown_http_method():
    """Test handling of non-standard HTTP methods."""
    retry = RateLimitAwareRetry(...)
    assert retry.is_retryable_method("CUSTOM") == False

def test_method_preserved_across_retries():
    """Test that method is preserved when incrementing retry count."""
    retry = RateLimitAwareRetry(...)
    retry._current_method = "POST"
    new_retry = retry.increment()
    assert new_retry._current_method == "POST"

def test_error_logging_with_deeply_nested_errors():
    """Test error logging handles deeply nested error structures."""
    # Test with nested DetailedErrorResponse
    pass
```

### Priority 2: `client.py` (51% → 70%)

Add tests for common patterns:

```python
# tests/test_base_client.py

def test_authenticated_client_initialization():
    """Test AuthenticatedClient initializes correctly."""
    client = AuthenticatedClient(base_url="...", token="...")
    assert client.token == "..."

def test_client_context_manager():
    """Test client context manager lifecycle."""
    with AuthenticatedClient(...) as client:
        assert client._client is not None
    # Verify cleanup after exit
```

### Priority 3: `log_setup.py` (0% → 60%)

Add basic tests:

```python
# tests/test_log_setup.py

def test_logger_initialization():
    """Test that logger can be initialized."""
    from katana_public_api_client.log_setup import setup_logger
    logger = setup_logger()
    assert logger is not None

def test_log_level_configuration():
    """Test log level can be configured."""
    # Test different log levels
    pass
```

______________________________________________________________________

## CI Integration

### Current CI

The CI runs standard coverage reporting:

```yaml
- name: Run tests
  run: poetry run poe test-coverage
```

### Proposed Enhancement

Add coverage analysis to CI:

```yaml
- name: Run tests with coverage
  run: |
    poetry run pytest --cov=katana_public_api_client --cov-report=json -m 'not docs'
    poetry run poe analyze-coverage

- name: Check core logic coverage
  run: |
    # Fail if core logic coverage < 70%
    poetry run python scripts/analyze_coverage.py
```

The `analyze_coverage.py` script exits with code 1 if core coverage < 50%.

______________________________________________________________________

## Key Takeaways

### ✅ What's Good

1. **Core logic has solid coverage** (74.8%)
1. **Critical components well tested**:
   - `utils.py`: 98% - recently added utilities
   - `katana_client.py`: 85% - resilience layer
1. **Generated code is appropriately untested** (0.6% is fine!)
1. **Test quality is high** (not just quantity)

### ⚠️ What Needs Work

1. **Edge cases in retry logic** (katana_client.py)
1. **Base client patterns** (client.py)
1. **Logging setup** (log_setup.py)

### 💡 Philosophy

**Test what you write, not what's generated.**

- Generated code (248 API modules, 337 models): Low coverage OK
- Core logic (5 files, 524 lines): High coverage essential
- Focus testing effort where bugs are likely to occur

______________________________________________________________________

## Related Resources

- **Issue #31**:
  [Improve Test Coverage for Core Logic](https://github.com/dougborg/katana-openapi-client/issues/31)
- **Script**: `scripts/analyze_coverage.py` - Coverage analysis tool
- **Task**: `poetry run poe analyze-coverage` - Run coverage analysis
- **Tests**: `tests/test_utils.py` - Example of comprehensive test suite (31 tests)

______________________________________________________________________

## FAQ

### Q: Why is overall coverage only 23%?

**A**: Because it includes ~30,000 lines of auto-generated code (API modules and models)
that don't need comprehensive unit testing. When you look at just the core logic we
wrote, coverage is 74.8%.

### Q: Should we test the generated API modules?

**A**: Not directly with unit tests. They're tested indirectly through:

1. Integration tests that make real API calls
1. Example scripts that use the API
1. The openapi-python-client generator itself (which has its own tests)

### Q: What's a good coverage target?

**A**:

- Overall: Don't worry about it (it's mostly generated code)
- Core logic: 70%+ (currently at 74.8% ✅)
- Individual core files: 80%+ ideal

### Q: How do I see detailed coverage for a specific file?

```bash
# Generate HTML coverage report
poetry run pytest --cov=katana_public_api_client --cov-report=html -m 'not docs'

# Open in browser
open htmlcov/index.html
```

Then navigate to the file you want to inspect.

### Q: How often should coverage be checked?

**A**:

- **Every PR**: CI checks overall tests pass
- **Weekly**: Manual review of core logic coverage
- **After adding core features**: Ensure new code is well tested
- **Before releases**: Verify no coverage regressions
