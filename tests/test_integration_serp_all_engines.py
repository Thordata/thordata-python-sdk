"""
Live integration smoke tests for SERP API.

These tests are intentionally light-weight and only validate that:
- each engine/mode can be called with a minimal valid parameter set
- API returns a JSON payload without an application error code

They are gated by THORDATA_INTEGRATION=true and require real credentials.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

from thordata import ThordataClient
from thordata.env import load_env_file


def _integration_enabled() -> bool:
    return str(os.getenv("THORDATA_INTEGRATION", "")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@pytest.mark.integration
def test_serp_all_engines_and_modes_smoke() -> None:
    if not _integration_enabled():
        pytest.skip("Set THORDATA_INTEGRATION=true to run live integration tests")

    # Load .env (no override). Allow specifying an explicit env file path.
    env_file = os.getenv("THORDATA_ENV_FILE", "").strip()
    if env_file:
        load_env_file(env_file)
    else:
        load_env_file()

    token = os.getenv("THORDATA_SCRAPER_TOKEN")
    if not token:
        pytest.skip("Missing THORDATA_SCRAPER_TOKEN for live SERP tests")

    client = ThordataClient(scraper_token=token)

    # --- Minimal requests per engine/mode (based on `.ai/SERP API参数`) ---
    today = date.today()
    outbound = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    cases: list[tuple[str, dict]] = [
        # Google (17 modes in the params folder)
        ("google", {"query": "pizza"}),
        ("google_shopping", {"query": "pizza"}),
        ("google_local", {"query": "pizza"}),
        ("google_videos", {"query": "pizza"}),
        ("google_news", {"query": "pizza"}),
        ("google_product", {"query": "pizza", "product_id": "B08N5WRWNW"}),
        (
            "google_flights",
            {
                "query": "",
                "departure_id": "CDG",
                "arrival_id": "AUS",
                "outbound_date": outbound,
            },
        ),
        ("google_images", {"query": "pizza"}),
        ("google_lens", {"query": "", "url": "https://i.imgur.com/HBrB8p0.png"}),
        ("google_trends", {"query": "pizza"}),
        ("google_hotels", {"query": "Bali Resorts"}),
        # Some Google verticals are more sensitive to geo/language; provide stable defaults.
        (
            "google_play",
            {"query": "pizza", "country": "us", "language": "en", "no_cache": True},
        ),
        (
            "google_jobs",
            {"query": "pizza", "country": "us", "language": "en", "no_cache": True},
        ),
        ("google_scholar", {"query": "transformer attention"}),
        ("google_maps", {"query": "pizza", "ll": "@40.7455096,-74.0083012,14z"}),
        ("google_finance", {"query": "AAPL"}),
        ("google_patents", {"query": "battery technology"}),
        # Bing (6 modes)
        ("bing", {"query": "pizza"}),
        ("bing_news", {"query": "pizza"}),
        ("bing_shopping", {"query": "laptop"}),
        ("bing_maps", {"query": "pizza", "cp": "40.7455096~-74.0083012"}),
        ("bing_images", {"query": "pizza"}),
        ("bing_videos", {"query": "pizza"}),
        # DuckDuckGo / Yandex
        ("duckduckgo", {"query": "pizza"}),
        ("yandex", {"query": "pizza"}),
    ]

    failures: list[str] = []
    for engine, params in cases:
        try:
            out = client.serp_search(engine=engine, output_format="json", **params)
            assert isinstance(out, dict)
        except Exception as e:  # noqa: BLE001 - show all failing engines at once
            failures.append(f"{engine}: {type(e).__name__}: {e}")

    if failures:
        raise AssertionError("SERP smoke failures:\n" + "\n".join(failures))
