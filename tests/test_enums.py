"""
Tests for thordata.enums module.
"""

import pytest

from thordata.enums import (
    Continent,
    Country,
    Engine,
    GoogleSearchType,
    ProxyType,
    TaskStatus,
    normalize_enum_value,
)
from thordata.models import ProxyProduct  # ProxyProduct 在 models.py 中


class TestEngine:
    """Tests for Engine enum."""

    def test_engine_values(self):
        """Test that engine values are lowercase strings."""
        assert Engine.GOOGLE.value == "google"
        assert Engine.BING.value == "bing"
        assert Engine.YANDEX.value == "yandex"

    def test_engine_is_str(self):
        """Test that Engine inherits from str."""
        assert isinstance(Engine.GOOGLE, str)
        assert Engine.GOOGLE == "google"


class TestGoogleSearchType:
    """Tests for GoogleSearchType enum."""

    def test_search_types(self):
        """Test Google search type values."""
        assert GoogleSearchType.SEARCH.value == "search"
        assert GoogleSearchType.SHOPPING.value == "shopping"
        assert GoogleSearchType.NEWS.value == "news"
        assert GoogleSearchType.IMAGES.value == "images"


class TestProxyType:
    """Tests for ProxyType enum."""

    def test_proxy_type_values(self):
        """Test proxy type integer values."""
        assert ProxyType.RESIDENTIAL == 1
        assert ProxyType.UNLIMITED == 2
        assert ProxyType.DATACENTER == 3


class TestProxyProduct:
    """Tests for ProxyProduct enum."""

    def test_default_ports(self):
        """Test default ports for each product."""
        assert ProxyProduct.RESIDENTIAL.default_port == 9999
        assert ProxyProduct.MOBILE.default_port == 5555
        assert ProxyProduct.DATACENTER.default_port == 7777
        assert ProxyProduct.ISP.default_port == 6666


class TestContinent:
    """Tests for Continent enum."""

    def test_continent_codes(self):
        """Test continent codes."""
        assert Continent.ASIA.value == "as"
        assert Continent.EUROPE.value == "eu"
        assert Continent.NORTH_AMERICA.value == "na"


class TestCountry:
    """Tests for Country enum."""

    def test_country_codes(self):
        """Test country codes are lowercase."""
        assert Country.US.value == "us"
        assert Country.GB.value == "gb"
        assert Country.JP.value == "jp"


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_is_terminal(self):
        """Test is_terminal method."""
        assert TaskStatus.is_terminal(TaskStatus.READY) is True
        assert TaskStatus.is_terminal(TaskStatus.SUCCESS) is True
        assert TaskStatus.is_terminal(TaskStatus.FAILED) is True
        assert TaskStatus.is_terminal(TaskStatus.RUNNING) is False
        assert TaskStatus.is_terminal(TaskStatus.PENDING) is False

    def test_is_success(self):
        """Test is_success method."""
        assert TaskStatus.is_success(TaskStatus.READY) is True
        assert TaskStatus.is_success(TaskStatus.SUCCESS) is True
        assert TaskStatus.is_success(TaskStatus.FAILED) is False

    def test_is_failure(self):
        """Test is_failure method."""
        assert TaskStatus.is_failure(TaskStatus.FAILED) is True
        assert TaskStatus.is_failure(TaskStatus.ERROR) is True
        assert TaskStatus.is_failure(TaskStatus.SUCCESS) is False


class TestNormalizeEnumValue:
    """Tests for normalize_enum_value function."""

    def test_with_enum(self):
        """Test with enum value."""
        result = normalize_enum_value(Engine.GOOGLE, Engine)
        assert result == "google"

    def test_with_string(self):
        """Test with string value."""
        result = normalize_enum_value("GOOGLE", Engine)
        assert result == "google"

    def test_with_invalid_type(self):
        """Test with invalid type."""
        with pytest.raises(TypeError, match="Expected Engine or str"):
            normalize_enum_value(123, Engine)
