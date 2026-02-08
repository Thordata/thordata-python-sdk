"""
Internal helpers for response wrapper integration.

These utilities help integrate APIResponse into client methods
while maintaining backward compatibility.
"""

from __future__ import annotations

from typing import Any

from .response import APIResponse


def wrap_response(
    response: Any,  # requests.Response or aiohttp.ClientResponse
    *,
    parse_json: bool = True,
    return_wrapper: bool = False,
) -> APIResponse[dict[str, Any] | str] | dict[str, Any] | str:
    """
    Wrap a response in APIResponse, with optional backward compatibility.

    Args:
        response: The HTTP response object.
        parse_json: Whether to parse as JSON.
        return_wrapper: If True, return APIResponse; if False, return data directly
                        (for backward compatibility).

    Returns:
        APIResponse if return_wrapper=True, else the response data.
    """
    if hasattr(response, "json"):  # requests.Response
        api_response = APIResponse.from_requests_response(
            response, parse_json=parse_json
        )
    else:  # aiohttp.ClientResponse
        import asyncio

        if asyncio.iscoroutinefunction(response.json):
            # This is async, but we can't await here
            # For async, the caller should use from_aiohttp_response directly
            raise ValueError(
                "For async responses, use APIResponse.from_aiohttp_response() directly"
            )
        api_response = APIResponse.from_requests_response(
            response, parse_json=parse_json
        )

    if return_wrapper:
        return api_response
    return api_response.data


def extract_response_data(
    response: APIResponse[dict[str, Any] | str] | dict[str, Any] | str,
) -> dict[str, Any] | str:
    """
    Extract data from response, handling both APIResponse and raw data.

    Args:
        response: Either APIResponse or raw data.

    Returns:
        The response data.
    """
    if isinstance(response, APIResponse):
        return response.data
    return response


def check_response_error(
    response: APIResponse[dict[str, Any] | str],
    *,
    raise_on_error: bool = True,
) -> None:
    """
    Check if response indicates an error and optionally raise.

    Args:
        response: The APIResponse to check.
        raise_on_error: Whether to raise an exception on error.

    Raises:
        ThordataAPIError: If raise_on_error=True and response indicates error.
    """
    if response.is_error and raise_on_error:
        from .exceptions import raise_for_code

        message = response.message or "API request failed"
        raise_for_code(
            message,
            status_code=response.status_code,
            code=response.code,
            payload=response.data if isinstance(response.data, dict) else None,
            request_id=response.request_id,
        )


__all__ = ["wrap_response", "extract_response_data", "check_response_error"]
