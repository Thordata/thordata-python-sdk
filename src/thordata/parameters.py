# src/thordata/parameters.py

from typing import Any, Dict


def normalize_serp_params(engine: str, query: str, **kwargs) -> Dict[str, Any]:
    """
    Normalizes parameters across different search engines to ensure a unified API surface.

    Args:
        engine (str): The search engine to use (e.g., 'google', 'yandex').
        query (str): The search query string.
        **kwargs: Additional parameters to pass to the API.

    Returns:
        Dict[str, Any]: The constructed payload for the API request.
    """
    # 1. Base parameters
    payload = {
        "num": str(kwargs.get("num", 10)),  # Default to 10 results
        "json": "1",  # Force JSON response
        "engine": engine,
    }

    # 2. Handle Query Parameter Differences (Yandex uses 'text', others use 'q')
    if engine == "yandex":
        payload["text"] = query
        # Set default URL for Yandex if not provided
        if "url" not in kwargs:
            payload["url"] = "yandex.com"
    else:
        payload["q"] = query

        # 3. Handle Default URLs for other engines
        if "url" not in kwargs:
            defaults = {
                "google": "google.com",
                "bing": "bing.com",
                "duckduckgo": "duckduckgo.com",
                "baidu": "baidu.com",
            }
            if engine in defaults:
                payload["url"] = defaults[engine]

    # 4. Passthrough for all other user-provided arguments
    # This allows support for engine-specific parameters (e.g., tbm, uule, gl)
    # without explicitly defining them all.
    protected_keys = {"num", "engine", "q", "text"}
    for key, value in kwargs.items():
        if key not in protected_keys:
            payload[key] = value

    return payload
