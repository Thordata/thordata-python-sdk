# Changelog

All notable changes to the Thordata Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2024-12-11

### Added

- **Type-safe models**: New `ProxyConfig`, `SerpRequest`, `UniversalScrapeRequest`, `ScraperTaskConfig` dataclasses for better IDE support and parameter validation
- **Retry mechanism**: Configurable automatic retry with exponential backoff via `RetryConfig`
- **Comprehensive enums**: `Engine`, `ProxyType`, `ProxyProduct`, `Continent`, `Country`, `TaskStatus`, and more
- **Exception hierarchy**: Detailed exceptions (`ThordataAuthError`, `ThordataRateLimitError`, `ThordataServerError`, `ThordataTimeoutError`, etc.)
- **Sticky sessions**: `StickySession` class for maintaining the same IP across requests
- **Advanced methods**: `serp_search_advanced()`, `universal_scrape_advanced()`, `create_scraper_task_advanced()` for full parameter control
- **Wait for task**: `wait_for_task()` method to poll task status until completion
- **Async parity**: All sync methods now have async equivalents including `list_countries()`, `list_states()`, `list_cities()`, `list_asn()`
- **Web Unlocker enhancements**: Support for `headers`, `cookies`, `clean_content`, `wait`, `wait_for` parameters
- **Context manager support**: Both clients support `with` / `async with` syntax

### Changed

- **Breaking**: Minimum Python version is now 3.8
- **Breaking**: `ThordataClient` initialization parameters reorganized
- Improved error messages with more context
- Better logging throughout the SDK
- Code restructured for maintainability (new `_utils.py`, `retry.py` modules)

### Fixed

- Async client now has all location API methods (was missing in v0.3.x)
- Consistent error handling across sync and async clients
- Base64 image decoding edge cases
- Session management in async client

### Removed

- Deprecated `gate.thordata.com` as default proxy host (now uses `pr.thordata.net`)

## [0.3.1] 

### Fixed

- Fixed `get_task_result` using hardcoded file type

## [0.3.0] 

### Added

- Async client (`AsyncThordataClient`)
- Location APIs (`list_countries`, `list_states`, `list_cities`, `list_asn`)
- Basic exception types

### Changed

- Restructured package layout to `src/thordata/`

## [0.2.0] 

### Added

- SERP API support
- Universal Scraping API support
- Web Scraper API (task-based)

## [0.1.0] 

### Added

- Initial release
- Basic proxy network support
- Synchronous client