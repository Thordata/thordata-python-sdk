"""
Unified response wrapper for Thordata API responses.

This module provides a consistent interface for handling API responses,
making it easier to work with different response types across the SDK.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from .constants import ResponseKey

T = TypeVar("T")


class APIResponse(Generic[T]):
    """
    Unified response wrapper for Thordata API responses.

    This class provides a consistent interface for accessing response data,
    status codes, error messages, and metadata across all API endpoints.

    Attributes:
        data: The response data (parsed JSON or raw content).
        status_code: HTTP status code.
        code: Application-level error code (if present).
        message: Error or success message (if present).
        request_id: Request ID for debugging (if present).
        raw_response: The raw response object (requests.Response or aiohttp.ClientResponse).
        is_success: Whether the request was successful.
        is_error: Whether the request resulted in an error.
    """

    def __init__(
        self,
        data: T,
        *,
        status_code: int | None = None,
        code: int | None = None,
        message: str | None = None,
        request_id: str | None = None,
        raw_response: Any = None,
    ) -> None:
        """
        Initialize an APIResponse.

        Args:
            data: The response data.
            status_code: HTTP status code.
            code: Application-level error code.
            message: Error or success message.
            request_id: Request ID for debugging.
            raw_response: The raw response object.
        """
        self.data = data
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id
        self.raw_response = raw_response

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        if self.code is not None:
            return self.code == 200
        if self.status_code is not None:
            return 200 <= self.status_code < 300
        return True

    @property
    def is_error(self) -> bool:
        """Check if the response indicates an error."""
        return not self.is_success

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        status_code: int | None = None,
        raw_response: Any = None,
    ) -> APIResponse[dict[str, Any]]:
        """
        Create an APIResponse from a dictionary.

        This method extracts common response fields (code, message, request_id)
        from the dictionary and wraps the data appropriately.

        Args:
            data: The response dictionary.
            status_code: HTTP status code.
            raw_response: The raw response object.

        Returns:
            An APIResponse instance.
        """
        # Extract common fields
        code = data.get(ResponseKey.CODE) or data.get("code")
        message = data.get(ResponseKey.MESSAGE) or data.get("message")
        request_id = (
            data.get(ResponseKey.REQUEST_ID)
            or data.get(ResponseKey.REQUEST_ID_ALT)
            or data.get("request_id")
            or data.get("requestId")
        )

        # If code is present and indicates an error, extract error message
        if code is not None and code != 200 and message is None:
            message = data.get("error") or data.get("error_message") or "Unknown error"

        # Type ignore needed because mypy doesn't support indexing Generic class constructors
        # and has issues with Generic[T] when T is dict[str, Any]
        # The data parameter is dict[str, Any] but mypy expects T, which is correct at runtime
        return cls(  # type: ignore[return-value,arg-type]
            data=data,  # type: ignore[arg-type]
            status_code=status_code,
            code=code,
            message=message,
            request_id=request_id,
            raw_response=raw_response,
        )

    @classmethod
    def from_requests_response(
        cls,
        response: Any,  # requests.Response
        *,
        parse_json: bool = True,
    ) -> APIResponse[dict[str, Any] | str]:
        """
        Create an APIResponse from a requests.Response object.

        Args:
            response: The requests.Response object.
            parse_json: Whether to parse the response as JSON.

        Returns:
            An APIResponse instance.
        """
        status_code = response.status_code

        if parse_json:
            try:
                data = response.json()
                if isinstance(data, dict):
                    # from_dict returns APIResponse[dict[str, Any]], but we need APIResponse[dict[str, Any] | str]
                    result = cls.from_dict(
                        data, status_code=status_code, raw_response=response
                    )
                    return result  # type: ignore[return-value]
                # Type ignore needed because mypy doesn't support indexing Generic class constructors
                return cls(  # type: ignore[return-value]
                    data=data,
                    status_code=status_code,
                    raw_response=response,
                )
            except (ValueError, TypeError):
                # Not JSON, return as text
                pass

        # Type ignore needed because mypy doesn't support indexing Generic class constructors
        return cls(  # type: ignore[return-value]
            data=response.text,
            status_code=status_code,
            raw_response=response,
        )

    @classmethod
    async def from_aiohttp_response(
        cls,
        response: Any,  # aiohttp.ClientResponse
        *,
        parse_json: bool = True,
    ) -> APIResponse[dict[str, Any] | str]:
        """
        Create an APIResponse from an aiohttp.ClientResponse object.

        Args:
            response: The aiohttp.ClientResponse object.
            parse_json: Whether to parse the response as JSON.

        Returns:
            An APIResponse instance.
        """
        status_code = response.status

        if parse_json:
            try:
                data = await response.json()
                if isinstance(data, dict):
                    # from_dict returns APIResponse[dict[str, Any]], but we need APIResponse[dict[str, Any] | str]
                    result = cls.from_dict(
                        data, status_code=status_code, raw_response=response
                    )
                    return result  # type: ignore[return-value]
                # Type ignore needed because mypy doesn't support indexing Generic class constructors
                return cls(  # type: ignore[return-value]
                    data=data,
                    status_code=status_code,
                    raw_response=response,
                )
            except (ValueError, TypeError):
                # Not JSON, return as text
                pass

        text = await response.text()
        # Type ignore needed because mypy doesn't support indexing Generic class constructors
        return cls(  # type: ignore[return-value]
            data=text,
            status_code=status_code,
            raw_response=response,
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the response data (if it's a dictionary).

        Args:
            key: The key to look up.
            default: Default value if key is not found.

        Returns:
            The value associated with the key, or default.
        """
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        return default

    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-style access to response data.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key.

        Raises:
            TypeError: If data is not a dictionary.
            KeyError: If key is not found.
        """
        if isinstance(self.data, dict):
            return self.data[key]
        raise TypeError("Response data is not a dictionary")

    def __repr__(self) -> str:
        """String representation of the response."""
        parts = [f"status_code={self.status_code}"]
        if self.code is not None:
            parts.append(f"code={self.code}")
        if self.message:
            parts.append(f"message={self.message!r}")
        if self.request_id:
            parts.append(f"request_id={self.request_id!r}")
        return f"APIResponse({', '.join(parts)})"


__all__ = ["APIResponse"]
