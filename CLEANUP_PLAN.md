# Test and Example Files Cleanup Plan

## Analysis of Redundancy

### 1. Test Files Analysis

#### Redundant/Similar Test Files:
1. **`test_examples.py`** vs **`test_client.py`** + **`test_async_client.py`**
   - `test_examples.py`: Tests example scripts execution (integration-style)
   - `test_client.py`/`test_async_client.py`: Unit tests for client methods
   - **Status**: NOT redundant - different purposes (integration vs unit tests)

2. **`test_tools.py`** vs **`test_tools_coverage.py`**
   - `test_tools.py`: Tests tool classes and serialization
   - `test_tools_coverage.py`: Tests all tool classes for contract compliance
   - **Status**: POTENTIALLY redundant - both test tool serialization
   - **Recommendation**: Merge into single comprehensive test file

3. **`test_client_errors.py`** vs **`test_async_client_errors.py`**
   - Both test error handling
   - **Status**: NOT redundant - sync vs async versions needed

4. **`test_task_status_and_wait.py`**
   - Tests task status and waiting logic
   - **Status**: Could be merged into `test_client.py` for better organization

### 2. Example Files Analysis

#### Redundant/Similar Example Files:
1. **`quick_start.py`** vs **`full_acceptance_test.py`**
   - `quick_start.py`: Quick validation of core features
   - `full_acceptance_test.py`: Comprehensive acceptance test suite
   - **Status**: NOT redundant - different scopes (quick vs comprehensive)

2. **`demo_web_scraper_api.py`** vs **`demo_web_scraper_multi_spider.py`**
   - `demo_web_scraper_api.py`: Single spider workflow demo
   - `demo_web_scraper_multi_spider.py`: Multiple spiders test
   - **Status**: NOT redundant - different use cases

3. **`demo_universal.py`** vs **`quick_start.py`** (Universal section)
   - Both demonstrate Universal API
   - **Status**: MINOR redundancy - `demo_universal.py` is more focused
   - **Recommendation**: Keep both (focused demo vs quick start)

4. **`validate_env.py`**
   - Validates environment variables
   - **Status**: Unique utility, keep

5. **`diagnose_network.py`**
   - Network diagnostics utility
   - **Status**: Unique utility, keep

### 3. Integration Test Files

#### Important Integration Tests:
1. **`test_integration_proxy_protocols.py`**
   - Tests proxy protocol connectivity (HTTPS, SOCKS5h)
   - **Status**: IMPORTANT - validates proxy network functionality
   - **Requires**: `THORDATA_INTEGRATION=true`, proxy credentials

2. **`test_tools_coverage.py`** (with integration flag)
   - Tests all tool classes with real API calls
   - **Status**: IMPORTANT - validates tool contracts
   - **Requires**: `THORDATA_INTEGRATION=true`

## Cleanup Recommendations

### High Priority (Remove/Merge)

1. **Merge `test_tools.py` into `test_tools_coverage.py`**
   - Both test tool serialization
   - `test_tools_coverage.py` is more comprehensive
   - **Action**: Merge functionality, remove `test_tools.py`

2. **Merge `test_task_status_and_wait.py` into `test_client.py`**
   - Task-related tests should be in main client test file
   - **Action**: Move tests, remove separate file

### Medium Priority (Review/Consolidate)

3. **Review example file organization**
   - Consider grouping by category:
     - `examples/basic/` - quick_start.py, validate_env.py
     - `examples/demos/` - demo_*.py files
     - `examples/tools/` - tool-specific examples (already exists)
   - **Action**: Reorganize for better discoverability

### Low Priority (Keep but Document)

4. **Keep all demo files**
   - Each serves a specific purpose
   - **Action**: Add clear docstrings explaining when to use each

## Integration Test Execution Plan

### Required Environment Variables:
```bash
THORDATA_INTEGRATION=true
THORDATA_SCRAPER_TOKEN=...
THORDATA_PUBLIC_TOKEN=...
THORDATA_PUBLIC_KEY=...
THORDATA_PROXY_HOST=pr.thordata.net
THORDATA_RESIDENTIAL_USERNAME=...
THORDATA_RESIDENTIAL_PASSWORD=...
THORDATA_INTEGRATION_HTTP=true  # Optional: test HTTP protocol too
THORDATA_INTEGRATION_STRICT=true  # Optional: fail on any error
```

### Test Execution:
1. Proxy Protocol Integration Test
2. Tools Coverage Integration Test (if enabled)
3. All other integration tests

## File Structure After Cleanup

```
tests/
├── test_client.py              # Main sync client tests (includes task tests)
├── test_async_client.py       # Main async client tests
├── test_client_errors.py       # Sync error handling
├── test_async_client_errors.py # Async error handling
├── test_tools_coverage.py      # All tool tests (merged from test_tools.py)
├── test_integration_proxy_protocols.py  # Proxy integration test
├── test_examples.py            # Example scripts integration test
├── test_browser.py             # Browser tests
├── test_unlimited.py           # Unlimited namespace tests
├── test_batch_creation.py      # Batch creation tests
├── test_models.py              # Model tests
├── test_exceptions.py          # Exception tests
├── test_retry.py               # Retry logic tests
├── test_utils.py               # Utility function tests
├── test_enums.py               # Enum tests
├── test_env.py                 # Environment tests
├── test_user_agent.py          # User agent tests
└── test_spec_parity.py         # Spec parity tests

examples/
├── quick_start.py              # Quick validation
├── full_acceptance_test.py     # Comprehensive acceptance
├── validate_env.py             # Environment validation
├── diagnose_network.py         # Network diagnostics
├── demo_serp_api.py            # SERP demo
├── demo_universal.py           # Universal demo
├── demo_web_scraper_api.py     # Web Scraper single workflow
├── demo_web_scraper_multi_spider.py  # Multi-spider test
├── demo_proxy_network.py       # Proxy demo
├── demo_browser_api.py         # Browser demo
├── demo_scraping_browser.py    # Scraping browser demo
├── demo_account_and_usage.py  # Account demo
├── async_high_concurrency.py   # Async concurrency demo
└── tools/                      # Tool-specific examples
    ├── amazon_scraper.py
    ├── google_maps_scraper.py
    ├── social_media_scraper.py
    └── youtube_downloader.py
```

## Implementation Steps

1. **Phase 1: Merge Test Files**
   - Merge `test_tools.py` into `test_tools_coverage.py`
   - Merge `test_task_status_and_wait.py` into `test_client.py`
   - Run full test suite to ensure nothing breaks

2. **Phase 2: Run Integration Tests**
   - Set up environment variables
   - Run `test_integration_proxy_protocols.py`
   - Run `test_tools_coverage.py` with integration flag
   - Verify 100% pass rate

3. **Phase 3: Reorganize Examples (Optional)**
   - Group examples by category
   - Update documentation references

4. **Phase 4: Documentation**
   - Add clear docstrings to all example files
   - Update README with file organization

## Notes

- All integration tests are IMPORTANT for validating real-world functionality
- Integration tests require real credentials and may consume quota
- Integration tests should be run before major releases
- Consider adding CI/CD integration test runs (with proper credential management)
