from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .async_client import AsyncThordataClient
    from .client import ThordataClient

# --- Sync Engines ---


class EngineBase:
    def __init__(self, client: ThordataClient):
        self._client = client


class GoogleEngine(EngineBase):
    """Namespaced interface for Google features (Sync)."""

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google", **kwargs)

    def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_news", **kwargs)

    def jobs(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_jobs", **kwargs)

    def shopping(
        self, query: str, product_id: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        if product_id:
            kwargs["product_id"] = product_id
            return self._client.serp_search(query, engine="google_product", **kwargs)
        return self._client.serp_search(query, engine="google_shopping", **kwargs)

    def maps(
        self, query: str, coordinates: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        if coordinates:
            kwargs["ll"] = coordinates
        return self._client.serp_search(query, engine="google_maps", **kwargs)

    def flights(
        self,
        query: str = "",
        departure_id: str | None = None,
        arrival_id: str | None = None,
        outbound_date: str | None = None,
        return_date: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if departure_id:
            kwargs["departure_id"] = departure_id
        if arrival_id:
            kwargs["arrival_id"] = arrival_id
        if outbound_date:
            kwargs["outbound_date"] = outbound_date
        if return_date:
            kwargs["return_date"] = return_date
        return self._client.serp_search(query, engine="google_flights", **kwargs)

    def patents(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_patents", **kwargs)

    def trends(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_trends", **kwargs)


class BingEngine(EngineBase):
    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing", **kwargs)

    def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing_news", **kwargs)


class SerpNamespace:
    def __init__(self, client: ThordataClient):
        self.google = GoogleEngine(client)
        self.bing = BingEngine(client)
        self._client = client

    def search(self, *args, **kwargs):
        return self._client.serp_search(*args, **kwargs)


# --- Async Engines ---


class AsyncEngineBase:
    def __init__(self, client: AsyncThordataClient):
        self._client = client


class AsyncGoogleEngine(AsyncEngineBase):
    """Namespaced interface for Google features (Async)."""

    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google", **kwargs)

    async def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_news", **kwargs)

    async def jobs(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_jobs", **kwargs)

    async def shopping(
        self, query: str, product_id: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        if product_id:
            kwargs["product_id"] = product_id
            return await self._client.serp_search(
                query, engine="google_product", **kwargs
            )
        return await self._client.serp_search(query, engine="google_shopping", **kwargs)

    async def maps(
        self, query: str, coordinates: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        if coordinates:
            kwargs["ll"] = coordinates
        return await self._client.serp_search(query, engine="google_maps", **kwargs)

    async def flights(
        self,
        query: str = "",
        departure_id: str | None = None,
        arrival_id: str | None = None,
        outbound_date: str | None = None,
        return_date: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if departure_id:
            kwargs["departure_id"] = departure_id
        if arrival_id:
            kwargs["arrival_id"] = arrival_id
        if outbound_date:
            kwargs["outbound_date"] = outbound_date
        if return_date:
            kwargs["return_date"] = return_date
        return await self._client.serp_search(query, engine="google_flights", **kwargs)

    async def patents(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_patents", **kwargs)

    async def trends(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_trends", **kwargs)


class AsyncBingEngine(AsyncEngineBase):
    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing", **kwargs)

    async def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing_news", **kwargs)


class AsyncSerpNamespace:
    def __init__(self, client: AsyncThordataClient):
        self.google = AsyncGoogleEngine(client)
        self.bing = AsyncBingEngine(client)
        self._client = client

    async def search(self, *args, **kwargs):
        return await self._client.serp_search(*args, **kwargs)
