"""Browser automation module for Thordata Scraping Browser.

This module provides high-level browser automation capabilities using Playwright.
Requires optional dependency: pip install thordata[browser]
"""

from __future__ import annotations

from .exceptions import BrowserConnectionError, BrowserError

try:
    from .session import BrowserSession

    __all__ = ["BrowserSession", "BrowserError", "BrowserConnectionError"]
except ImportError:
    # Playwright not installed - BrowserSession not available
    __all__ = ["BrowserError", "BrowserConnectionError"]
