# Changelog

All notable changes to this project will be documented in this file.

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