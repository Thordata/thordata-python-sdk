# FILE: thordata-python-sdk/src/thordata/serp_engines.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import ThordataClient


class EngineBase:
    def __init__(self, client: ThordataClient):
        self._client = client


class GoogleEngine(EngineBase):
    """Namespaced interface for Google features."""

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Standard Google Web Search."""
        return self._client.serp_search(query, engine="google", **kwargs)

    def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Google News Search."""
        return self._client.serp_search(query, engine="google_news", **kwargs)

    def jobs(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Google Jobs Search."""
        return self._client.serp_search(query, engine="google_jobs", **kwargs)

    def shopping(
        self, query: str, product_id: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Google Shopping Search.
        If product_id is provided, it searches for that specific product details/offers.
        """
        if product_id:
            # Mapping specific product scraping logic
            kwargs["product_id"] = product_id
            return self._client.serp_search(query, engine="google_product", **kwargs)
        return self._client.serp_search(query, engine="google_shopping", **kwargs)

    def maps(
        self, query: str, coordinates: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Google Maps Search.
        Args:
            coordinates: Latitude,Longitude,Zoom (e.g. "@40.745,-74.008,14z")
        """
        if coordinates:
            kwargs["ll"] = coordinates
        return self._client.serp_search(query, engine="google_maps", **kwargs)

    def flights(
        self,
        query: str = "",  # Flights mostly relies on structured params, query is optional
        departure_id: str | None = None,
        arrival_id: str | None = None,
        outbound_date: str | None = None,
        return_date: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Google Flights Search.
        """
        if departure_id:
            kwargs["departure_id"] = departure_id
        if arrival_id:
            kwargs["arrival_id"] = arrival_id
        if outbound_date:
            kwargs["outbound_date"] = outbound_date
        if return_date:
            kwargs["return_date"] = return_date

        return self._client.serp_search(query, engine="google_flights", **kwargs)

    # Add other google sub-services here...
    def patents(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_patents", **kwargs)

    def trends(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_trends", **kwargs)


class BingEngine(EngineBase):
    """Namespaced interface for Bing features."""

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing", **kwargs)

    def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing_news", **kwargs)


# Wrapper for client.serp
class SerpNamespace:
    def __init__(self, client: ThordataClient):
        self.google = GoogleEngine(client)
        self.bing = BingEngine(client)
        # self.yandex = ...
        self._client = client

    def search(self, *args, **kwargs):
        """Pass-through to the original generic search."""
        return self._client.serp_search(*args, **kwargs)
