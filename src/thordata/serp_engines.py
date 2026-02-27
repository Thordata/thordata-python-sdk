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

    def images(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_images", **kwargs)

    def videos(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_videos", **kwargs)

    def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_news", **kwargs)

    def jobs(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_jobs", **kwargs)

    def play(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_play", **kwargs)

    def shopping(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_shopping", **kwargs)

    def product(self, product_id: str, **kwargs: Any) -> dict[str, Any]:
        """Google Product: requires product_id."""
        pid = str(product_id).strip()
        if not pid:
            raise ValueError("product_id is required for google_product")
        kwargs["product_id"] = pid
        return self._client.serp_search("", engine="google_product", **kwargs)

    def local(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_local", **kwargs)

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
        if not departure_id or not arrival_id:
            raise ValueError(
                "google_flights requires departure_id and arrival_id (see docs: `.ai/SERP API参数/Google/7Goole Flights.md`)"
            )
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

    def finance(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_finance", **kwargs)

    def hotels(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_hotels", **kwargs)

    def lens(self, query: str, **kwargs: Any) -> dict[str, Any]:
        raise TypeError(
            "google_lens requires an image URL. Use google.lens_by_url(url=..., query=..., type=...)"
        )

    def lens_by_url(
        self,
        *,
        url: str,
        query: str | None = None,
        type: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        u = str(url).strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            raise ValueError("url must start with http:// or https:// for google_lens")
        kwargs["url"] = u
        if query:
            kwargs["q"] = query
        if type:
            kwargs["type"] = type
        return self._client.serp_search("", engine="google_lens", **kwargs)

    def scholar(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="google_scholar", **kwargs)


class BingEngine(EngineBase):
    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing", **kwargs)

    def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing_news", **kwargs)

    def shopping(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing_shopping", **kwargs)

    def maps(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing_maps", **kwargs)

    def images(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing_images", **kwargs)

    def videos(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="bing_videos", **kwargs)


class DuckDuckGoEngine(EngineBase):
    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="duckduckgo", **kwargs)


class YandexEngine(EngineBase):
    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._client.serp_search(query, engine="yandex", **kwargs)


class SerpNamespace:
    def __init__(self, client: ThordataClient):
        self.google = GoogleEngine(client)
        self.bing = BingEngine(client)
        self.duckduckgo = DuckDuckGoEngine(client)
        self.yandex = YandexEngine(client)
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

    async def images(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_images", **kwargs)

    async def videos(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_videos", **kwargs)

    async def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_news", **kwargs)

    async def jobs(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_jobs", **kwargs)

    async def play(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_play", **kwargs)

    async def shopping(
        self, query: str, product_id: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        # Backward-compatible: if product_id is provided, use google_product.
        if product_id:
            kwargs["product_id"] = str(product_id).strip()
            return await self._client.serp_search("", engine="google_product", **kwargs)
        return await self._client.serp_search(query, engine="google_shopping", **kwargs)

    async def product(self, product_id: str, **kwargs: Any) -> dict[str, Any]:
        pid = str(product_id).strip()
        if not pid:
            raise ValueError("product_id is required for google_product")
        kwargs["product_id"] = pid
        return await self._client.serp_search("", engine="google_product", **kwargs)

    async def local(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_local", **kwargs)

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
        if not departure_id or not arrival_id:
            raise ValueError(
                "google_flights requires departure_id and arrival_id (see docs: `.ai/SERP API参数/Google/7Goole Flights.md`)"
            )
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

    async def finance(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_finance", **kwargs)

    async def hotels(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_hotels", **kwargs)

    async def lens(self, query: str, **kwargs: Any) -> dict[str, Any]:
        raise TypeError(
            "google_lens requires an image URL. Use google.lens_by_url(url=..., query=..., type=...)"
        )

    async def lens_by_url(
        self,
        *,
        url: str,
        query: str | None = None,
        type: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        u = str(url).strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            raise ValueError("url must start with http:// or https:// for google_lens")
        kwargs["url"] = u
        if query:
            kwargs["q"] = query
        if type:
            kwargs["type"] = type
        return await self._client.serp_search("", engine="google_lens", **kwargs)

    async def scholar(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="google_scholar", **kwargs)


class AsyncBingEngine(AsyncEngineBase):
    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing", **kwargs)

    async def news(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing_news", **kwargs)

    async def shopping(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing_shopping", **kwargs)

    async def maps(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing_maps", **kwargs)

    async def images(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing_images", **kwargs)

    async def videos(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="bing_videos", **kwargs)


class AsyncDuckDuckGoEngine(AsyncEngineBase):
    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="duckduckgo", **kwargs)


class AsyncYandexEngine(AsyncEngineBase):
    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return await self._client.serp_search(query, engine="yandex", **kwargs)


class AsyncSerpNamespace:
    def __init__(self, client: AsyncThordataClient):
        self.google = AsyncGoogleEngine(client)
        self.bing = AsyncBingEngine(client)
        self.duckduckgo = AsyncDuckDuckGoEngine(client)
        self.yandex = AsyncYandexEngine(client)
        self._client = client

    async def search(self, *args, **kwargs):
        return await self._client.serp_search(*args, **kwargs)
