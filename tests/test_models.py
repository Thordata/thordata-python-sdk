"""
Tests for thordata.models module.
"""

import pytest

from thordata.models import (
    ProxyConfig,
    ProxyProduct,
    ScraperTaskConfig,
    SerpRequest,
    StickySession,
    UniversalScrapeRequest,
)


class TestProxyConfig:
    """Tests for ProxyConfig dataclass."""

    def test_basic_creation(self):
        """Test basic ProxyConfig creation."""
        config = ProxyConfig(
            username="testuser",
            password="testpass",
        )
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.product == ProxyProduct.RESIDENTIAL

    def test_build_username_basic(self):
        """Test username building without options."""
        config = ProxyConfig(username="testuser", password="testpass")
        assert config.build_username() == "td-customer-testuser"

    def test_build_username_with_country(self):
        """Test username building with country."""
        config = ProxyConfig(
            username="testuser",
            password="testpass",
            country="us",
        )
        assert config.build_username() == "td-customer-testuser-country-us"

    def test_build_username_with_full_geo(self):
        """Test username building with full geo-targeting."""
        config = ProxyConfig(
            username="testuser",
            password="testpass",
            country="us",
            state="california",
            city="los_angeles",
        )
        expected = "td-customer-testuser-country-us-state-california-city-los_angeles"
        assert config.build_username() == expected

    def test_build_username_with_session(self):
        """Test username building with sticky session."""
        config = ProxyConfig(
            username="testuser",
            password="testpass",
            country="gb",
            session_id="mysession123",
            session_duration=10,
        )
        expected = "td-customer-testuser-country-gb-sessid-mysession123-sesstime-10"
        assert config.build_username() == expected

    def test_build_username_with_asn(self):
        """Test username building with ASN."""
        config = ProxyConfig(
            username="testuser",
            password="testpass",
            country="fr",
            asn="AS12322",
        )
        expected = "td-customer-testuser-country-fr-asn-AS12322"
        assert config.build_username() == expected

    def test_build_proxy_url(self):
        """Test full proxy URL building."""
        config = ProxyConfig(
            username="testuser",
            password="testpass",
            country="us",
        )
        url = config.build_proxy_url()
        assert "td-customer-testuser-country-us" in url
        assert ":testpass@" in url
        assert "pr.thordata.net" in url

    def test_to_proxies_dict(self):
        """Test conversion to proxies dict."""
        config = ProxyConfig(username="testuser", password="testpass")
        proxies = config.to_proxies_dict()
        assert "http" in proxies
        assert "https" in proxies
        assert proxies["http"] == proxies["https"]

    def test_invalid_protocol(self):
        """Test validation of protocol."""
        with pytest.raises(ValueError, match="Invalid protocol"):
            ProxyConfig(
                username="testuser",
                password="testpass",
                protocol="ftp",
            )

    def test_invalid_session_duration(self):
        """Test validation of session duration."""
        with pytest.raises(ValueError, match="session_duration must be between"):
            ProxyConfig(
                username="testuser",
                password="testpass",
                session_id="test",
                session_duration=100,  # Max is 90
            )

    def test_session_duration_requires_session_id(self):
        """Test that session_duration requires session_id."""
        with pytest.raises(ValueError, match="session_duration requires session_id"):
            ProxyConfig(
                username="testuser",
                password="testpass",
                session_duration=10,
            )

    def test_asn_requires_country(self):
        """Test that ASN requires country."""
        with pytest.raises(ValueError, match="ASN targeting requires country"):
            ProxyConfig(
                username="testuser",
                password="testpass",
                asn="AS12322",
            )

    def test_invalid_continent(self):
        """Test validation of continent code."""
        with pytest.raises(ValueError, match="Invalid continent code"):
            ProxyConfig(
                username="testuser",
                password="testpass",
                continent="xx",
            )

    def test_invalid_country_code(self):
        """Test validation of country code format."""
        with pytest.raises(ValueError, match="Invalid country code"):
            ProxyConfig(
                username="testuser",
                password="testpass",
                country="usa",  # Should be 2 letters
            )

    def test_proxy_product_ports(self):
        """Test that different products have different default ports."""
        residential = ProxyConfig(
            username="user", password="pass", product=ProxyProduct.RESIDENTIAL
        )
        assert residential.port == 9999

        mobile = ProxyConfig(
            username="user", password="pass", product=ProxyProduct.MOBILE
        )
        assert mobile.port == 5555

        datacenter = ProxyConfig(
            username="user", password="pass", product=ProxyProduct.DATACENTER
        )
        assert datacenter.port == 7777


class TestStickySession:
    """Tests for StickySession dataclass."""

    def test_auto_session_id(self):
        """Test automatic session ID generation."""
        session = StickySession(
            username="testuser",
            password="testpass",
            duration_minutes=15,
        )
        assert session.session_id is not None
        assert len(session.session_id) == 12

    def test_custom_session_id(self):
        """Test using a custom session ID."""
        session = StickySession(
            username="testuser",
            password="testpass",
            session_id="mycustomid",
            duration_minutes=10,
            auto_session_id=False,
        )
        assert session.session_id == "mycustomid"


class TestSerpRequest:
    """Tests for SerpRequest dataclass."""

    def test_basic_payload(self):
        """Test basic SERP request payload."""
        request = SerpRequest(query="test query")
        payload = request.to_payload()

        assert payload["q"] == "test query"
        assert payload["engine"] == "google"
        assert payload["num"] == "10"
        assert payload["json"] == "1"

    def test_yandex_uses_text_param(self):
        """Test that Yandex uses 'text' instead of 'q'."""
        request = SerpRequest(query="test query", engine="yandex")
        payload = request.to_payload()

        assert "text" in payload
        assert payload["text"] == "test query"
        assert "q" not in payload

    def test_search_type_mapping(self):
        """Test search type parameter mapping."""
        request = SerpRequest(
            query="test",
            search_type="shopping",
        )
        payload = request.to_payload()
        assert payload["tbm"] == "shop"

    def test_time_filter_mapping(self):
        """Test time filter parameter mapping."""
        request = SerpRequest(
            query="test",
            time_filter="week",
        )
        payload = request.to_payload()
        assert payload["tbs"] == "qdr:w"

    def test_localization_params(self):
        """Test localization parameters."""
        request = SerpRequest(
            query="test",
            country="us",
            language="en",
        )
        payload = request.to_payload()
        assert payload["gl"] == "us"
        assert payload["hl"] == "en"

    def test_pagination(self):
        """Test pagination parameters."""
        request = SerpRequest(
            query="test",
            num=20,
            start=40,
        )
        payload = request.to_payload()
        assert payload["num"] == "20"
        assert payload["start"] == "40"


class TestUniversalScrapeRequest:
    """Tests for UniversalScrapeRequest dataclass."""

    def test_basic_payload(self):
        """Test basic Universal scrape request payload."""
        request = UniversalScrapeRequest(url="https://example.com")
        payload = request.to_payload()

        assert payload["url"] == "https://example.com"
        assert payload["js_render"] == "False"
        assert payload["type"] == "html"

    def test_js_render_enabled(self):
        """Test JS rendering option."""
        request = UniversalScrapeRequest(
            url="https://example.com",
            js_render=True,
        )
        payload = request.to_payload()
        assert payload["js_render"] == "True"

    def test_wait_params(self):
        """Test wait parameters."""
        request = UniversalScrapeRequest(
            url="https://example.com",
            wait=5000,
            wait_for=".content",
        )
        payload = request.to_payload()
        assert payload["wait"] == "5000"
        assert payload["wait_for"] == ".content"

    def test_invalid_output_format(self):
        """Test validation of output format."""
        with pytest.raises(ValueError, match="Invalid output_format"):
            UniversalScrapeRequest(
                url="https://example.com",
                output_format="pdf",  # Only html/png supported
            )

    def test_invalid_wait_value(self):
        """Test validation of wait value."""
        with pytest.raises(ValueError, match="wait must be between"):
            UniversalScrapeRequest(
                url="https://example.com",
                wait=200000,  # Max is 100000
            )


class TestScraperTaskConfig:
    """Tests for ScraperTaskConfig dataclass."""

    def test_basic_payload(self):
        """Test basic task config payload."""
        config = ScraperTaskConfig(
            file_name="test_output",
            spider_id="test_spider",
            spider_name="example.com",
            parameters={"url": "https://example.com"},
        )
        payload = config.to_payload()

        assert payload["file_name"] == "test_output"
        assert payload["spider_id"] == "test_spider"
        assert payload["spider_name"] == "example.com"
        assert "spider_parameters" in payload
        assert payload["spider_errors"] == "true"
