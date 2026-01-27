# Changelog

All notable changes to this project will be documented in this file.

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