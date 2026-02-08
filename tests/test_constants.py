"""
Unit tests for constants module.
"""

import pytest

from thordata import (
    APIBaseURL,
    APIEndpoint,
    APIErrorCode,
    EnvVar,
    HTTPStatus,
)


class TestAPIBaseURL:
    """Test API base URL constants."""

    def test_scraper_api(self):
        assert APIBaseURL.SCRAPER_API == "https://scraperapi.thordata.com"

    def test_universal_api(self):
        assert APIBaseURL.UNIVERSAL_API == "https://webunlocker.thordata.com"

    def test_web_scraper_api(self):
        assert (
            APIBaseURL.WEB_SCRAPER_API
            == "https://openapi.thordata.com/api/web-scraper-api"
        )

    def test_locations_api(self):
        assert APIBaseURL.LOCATIONS_API == "https://openapi.thordata.com/api/locations"


class TestAPIEndpoint:
    """Test API endpoint constants."""

    def test_serp_request(self):
        assert APIEndpoint.SERP_REQUEST == "/request"

    def test_tasks_status(self):
        assert APIEndpoint.TASKS_STATUS == "/tasks-status"

    def test_universal_request(self):
        assert APIEndpoint.UNIVERSAL_REQUEST == "/request"


class TestHTTPStatus:
    """Test HTTP status code constants."""

    def test_ok(self):
        assert HTTPStatus.OK == 200

    def test_bad_request(self):
        assert HTTPStatus.BAD_REQUEST == 400

    def test_unauthorized(self):
        assert HTTPStatus.UNAUTHORIZED == 401


class TestAPIErrorCode:
    """Test API error code constants."""

    def test_success(self):
        assert APIErrorCode.SUCCESS == 200

    def test_not_collected(self):
        assert APIErrorCode.NOT_COLLECTED == 300


class TestEnvVar:
    """Test environment variable name constants."""

    def test_scraper_token(self):
        assert EnvVar.SCRAPER_TOKEN == "THORDATA_SCRAPER_TOKEN"

    def test_public_token(self):
        assert EnvVar.PUBLIC_TOKEN == "THORDATA_PUBLIC_TOKEN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
