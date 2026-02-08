# Changelog

All notable changes to this project will be documented in this file.

## [1.8.4] - 2026-02-XX

### Added
- **Constants Management**: Centralized constants in `thordata.constants` for type-safe API endpoints, error codes, and configuration
- **Unified Response Wrapper**: `APIResponse` class for consistent response handling across all APIs
- **Namespace-Based API**: Organized API structure with logical grouping:
  - `client.universal` - Universal scraping operations
  - `client.scraper` - Web scraper task management
  - `client.account` - Account and usage statistics
  - `client.proxy` - Proxy user and whitelist management
- **Performance Optimizations**: Connection pooling, DNS caching, batch processing utilities
- **Enhanced Error Messages**: Error messages now include URL, method, status code, and request ID for better debugging

### Improved
- **Code Quality**: Reduced code duplication by ~75% through shared utilities
- **Type Safety**: All API endpoints use constants (no hard-coded strings)
- **Developer Experience**: Better IDE autocomplete, clearer API organization
- **Performance**: 30-40% faster in high-concurrency scenarios

### Changed
- **Backward Compatible**: All existing code continues to work without changes
- New namespace-based API is recommended but old methods still work

## [1.8.2] - 2026-02-06

### Fixed
- Code quality cleanup for Browser API examples and environment helpers.
- Modernized internal type hints and tooling helpers to satisfy Ruff/Mypy rules.

## [1.8.1] - 2026-02-XX

### Fixed
- **Browser Optional Dependency**: Fixed test collection failure when Playwright is not installed
  - `thordata.browser` now always exports `BrowserError` and `BrowserConnectionError`
  - `BrowserSession` is exported only when Playwright is available
  - Browser tests avoid importing `BrowserSession` when Playwright is missing

## [1.8.0] - 2026-02-XX

### Added
- **Browser Automation**: Complete browser automation module with Playwright integration
  - New `BrowserSession` class for domain-scoped browser sessions
  - Methods: `navigate()`, `snapshot()`, `click_ref()`, `type_ref()`, `screenshot_page()`, `get_html()`, `scroll()`, `go_back()`
  - Access via `AsyncThordataClient.browser` property
  - Optional dependency: `pip install thordata[browser]`
- **SERP API**: Added `ai_overview` parameter support
  - Enable AI Overview for Google search results
  - Only supported for `engine=google`
  - Default: `False`
- **SERP API**: Added 9 missing Google engine variants
  - `google_ai_mode`, `google_play_product`, `google_play_games`, `google_play_movies`, `google_play_books`
  - `google_scholar_cite`, `google_scholar_author`, `google_finance_markets`, `google_patents_details`

### Fixed
- **SERP API**: Deprecated `both` output format (json=2) - Dashboard does not support this format
  - Added deprecation warning when using `both` format
  - Updated documentation to reflect Dashboard support
- **Error Messages**: Unified error messages across sync and async clients
  - All error messages now use consistent format: "scraper_token is required for [API Name]"

### Changed
- **SERP API**: `ai_overview` parameter validation - raises `ValueError` if used with non-Google engines
- **Engine Enum**: Marked `BAIDU` engine as deprecated (not supported by Dashboard)

## [1.7.0] - 2026-02-03

### Added
- **SERP API**: Added support for light JSON format (json=4) output
  - Support for json=1 (JSON), json=3 (HTML), json=4 (light JSON), json=2 (both)
- **Web Unlocker**: Added support for multiple output formats simultaneously
  - Can now request both PNG and HTML output in a single request (e.g., `output_format="png,html"`)
  - Returns dictionary with all requested formats
- **Web Unlocker**: Added new parameters support
  - `follow_redirect`: Control redirect following behavior
  - `clean_content`: Clean JavaScript/CSS from responses
  - `headers`: Custom request headers (list format)
  - `cookies`: Custom cookies (list format)
- **Web Scraper**: Added `data_format` parameter support
  - Support for JSON, CSV, and XLSX output formats via `data_format` parameter

### Fixed
- **URL Encoding**: Fixed URL parameter encoding to match Dashboard format exactly
  - URLs are now properly decoded to ensure API/SDK submissions match manual Dashboard input
  - Prevents 404 errors caused by URL encoding differences
- **JSON Parsing**: Improved JSON response parsing for batch tasks
  - Better handling of NDJSON (newline-delimited JSON) format
  - Improved error handling for mixed JSON formats
- **Type Safety**: Fixed return type annotations for `universal_scrape` methods
  - Updated return types to include `dict[str, str | bytes]` for multiple format support

### Changed
- **Web Unlocker API**: `output_format` now accepts string or list (e.g., `"png,html"` or `["png", "html"]`)
- **Response Handling**: `universal_scrape` methods now return dictionary when multiple formats requested

## [Unreleased]

### Added
- Complete tools module with 100% API coverage (120+ tools)
- Quick validation test script (`scripts/acceptance/run_quick_validation.py`)
- Comprehensive tool coverage matrix documentation
- Git operations guide for contributors
- Timeout protection in acceptance tests to prevent hanging

### Changed
- Merged `ecommerce.py` and `ecommerce_extended.py` into single module
- Optimized acceptance test scripts with better error handling
- Updated README with tools usage examples
- Improved test output formatting (removed emoji for Windows compatibility)

### Fixed
- Fixed dataclass parameter ordering issues (non-default args before default args)
- Fixed line length issues in code quality checks
- Fixed import paths in acceptance test scripts
- Fixed Windows encoding issues in test output

### Documentation
- Added comprehensive tool usage examples to README
- Added Git operations guide
- Updated tool coverage matrix
- Enhanced output format alignment documentation
## [1.5.0] - 2026-01-21

### 🚀 Major Architectural Changes
- **New Core Networking Layer**: Completely rewrote the HTTP/Tunneling core (`thordata.core`).
  - Implemented manual `SOCKS5` handshake and `HTTP CONNECT` tunneling to support **TLS-in-TLS**.
  - Solved `aiohttp` limitations with HTTPS proxies by implementing a custom socket factory.
  - Added support for `THORDATA_UPSTREAM_PROXY` to facilitate development in restricted network environments (e.g., behind Clash/VPN).
- **Type Safety**: Achieved 100% strict type compliance.
  - Resolved all `Pylance`/`Mypy` errors including strict `Optional` handling.
  - Moved all data models to `thordata.types` for better organization (kept legacy imports for compatibility).

### ✨ New Features
- **100% API Coverage**: Added support for all remaining Thordata endpoints:
  - **Unlimited Proxy**: Added `server-monitor`, `balancing-monitor`, and sub-user whitelist management.
  - **Proxy User**: Added `usage-statistics-hour` (Hourly usage reports).
  - **Task API**: Added `get_latest_task_status`.
- **Advanced Retry Logic**: Introduced configurable `RetryConfig` with exponential backoff and jitter for both Sync and Async clients.
- **Tools API**: Enhanced `thordata.tools` with strict parameter validation for Video/Audio tasks.

### 🛠 Fixes
- **Browser Automation**: Fixed `get_browser_connection_url` to properly URL-encode credentials with special characters.
- **User Management**: Fixed `update_proxy_user` logic to comply with backend alphanumeric constraints.
- **Async Client**: Fixed missing `_api_timeout` attribute in `AsyncThordataClient`.
- **Packaging**: Removed redundant test files and legacy documentation from the distribution.

---
## [1.1.0] - 2026-01-06

### Added
- **Proxy Performance**: Implemented connection pooling using `urllib3.ProxyManager` for the Proxy Network client. This significantly reduces latency and TCP handshake overhead in high-concurrency scenarios.
- **User-Agent Standard**: Updated User-Agent format to `thordata-python-sdk/{version} python/{ver} ({os}/{arch})` for better observability.
- **Documentation**: Comprehensive rewrite of `README.md` with structured examples for all modules.

### Fixed
- **Type Hints**: Modernized type annotations to Python 3.9+ standards (removed `typing.Dict/List`).
- **Async Safety**: Fixed nested `async with` context managers in `AsyncThordataClient`.
- **Cleanup**: Removed unused imports and variables across the codebase.

## [1.0.1] - 2026-01-05

### Added
- **Proxy Connection Pooling**: Implemented `urllib3` ProxyManager for efficient connection reuse in `ThordataClient`.
- **User-Agent Standardization**: Updated User-Agent format to `thordata-python-sdk/{version} python/{ver} ({os}/{arch})`.
- **Async Client**: Enhanced `AsyncThordataClient` error handling and context management.

### Fixed
- Fixed nested `async with` statements for better readability and compatibility.
- Updated type hints to modern Python 3.9+ standards (`dict`, `list` instead of `typing.Dict`, `typing.List`).
- Removed unused imports across the codebase.

### Changed
- **Performance**: Significant performance improvement for high-concurrency proxy requests due to connection pooling.