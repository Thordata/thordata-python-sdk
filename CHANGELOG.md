# Changelog

All notable changes to this project will be documented in this file.

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