"""Browser automation exceptions."""

from __future__ import annotations

from ..exceptions import ThordataError


class BrowserError(ThordataError):
    """Base exception for browser automation errors."""

    pass


class BrowserConnectionError(BrowserError):
    """Raised when browser connection fails."""

    pass


class BrowserSessionError(BrowserError):
    """Raised when browser session operations fail."""

    pass
