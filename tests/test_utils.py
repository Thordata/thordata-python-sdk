"""
Tests for thordata._utils module (internal utilities).
"""

import base64
from unittest.mock import patch

import pytest

from thordata import _utils


class TestParseJsonResponse:
    def test_returns_dict_unchanged(self):
        data = {"a": 1, "b": 2}
        assert _utils.parse_json_response(data) == data

    def test_parses_json_string(self):
        s = '{"code": 200, "data": []}'
        out = _utils.parse_json_response(s)
        assert out == {"code": 200, "data": []}

    def test_invalid_json_string_returned_as_is(self):
        s = "not json at all"
        assert _utils.parse_json_response(s) == s


class TestDecodeBase64Image:
    def test_decodes_plain_base64(self):
        raw = b"\x89PNG\r\n\x1a\n"
        enc = base64.b64encode(raw).decode("ascii")
        assert _utils.decode_base64_image(enc) == raw

    def test_strips_data_uri_prefix(self):
        raw = b"pngbytes"
        enc = base64.b64encode(raw).decode("ascii")
        data_uri = f"data:image/png;base64,{enc}"
        assert _utils.decode_base64_image(data_uri) == raw

    def test_fixes_padding(self):
        # "M" -> "M===" for valid base64
        padded = base64.b64encode(b"x").decode("ascii").rstrip("=")
        out = _utils.decode_base64_image(padded)
        assert out == b"x"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty PNG"):
            _utils.decode_base64_image("")

    def test_invalid_base64_raises(self):
        with pytest.raises(ValueError, match="Failed to decode"):
            _utils.decode_base64_image("not-valid-base64!!!")


class TestBuildAuthHeaders:
    def test_bearer_mode(self):
        h = _utils.build_auth_headers("my_token", mode="bearer")
        assert h["Authorization"] == "Bearer my_token"
        assert h["Content-Type"] == "application/x-www-form-urlencoded"

    def test_header_token_mode(self):
        h = _utils.build_auth_headers("my_token", mode="header_token")
        assert h["token"] == "my_token"
        assert "Authorization" not in h or h.get("Authorization") == "Bearer my_token"
        assert h["Content-Type"] == "application/x-www-form-urlencoded"

    def test_unknown_mode_fallback_to_bearer(self):
        h = _utils.build_auth_headers("tk", mode="other")
        assert h["Authorization"] == "Bearer tk"


class TestBuildBuilderHeaders:
    def test_contains_all_three_auth_fields(self):
        h = _utils.build_builder_headers(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )
        assert h["Authorization"] == "Bearer st"
        assert h["token"] == "pt"
        assert h["key"] == "pk"
        assert h["Content-Type"] == "application/x-www-form-urlencoded"


class TestBuildPublicApiHeaders:
    def test_contains_token_and_key(self):
        h = _utils.build_public_api_headers("pt", "pk")
        assert h["token"] == "pt"
        assert h["key"] == "pk"
        assert h["Content-Type"] == "application/x-www-form-urlencoded"


class TestExtractErrorMessage:
    def test_prefers_msg(self):
        assert _utils.extract_error_message({"msg": "error text"}) == "error text"

    def test_message_key(self):
        assert _utils.extract_error_message({"message": "msg text"}) == "msg text"

    def test_error_key(self):
        assert _utils.extract_error_message({"error": "err text"}) == "err text"

    def test_detail_key(self):
        assert _utils.extract_error_message({"detail": "detail text"}) == "detail text"

    def test_fallback_to_str_payload(self):
        payload = {"code": 500}
        out = _utils.extract_error_message(payload)
        assert "500" in out or "code" in out

    def test_non_dict_returns_str(self):
        assert _utils.extract_error_message("string") == "string"
        assert _utils.extract_error_message(123) == "123"


class TestBuildUserAgent:
    def test_contains_sdk_version_and_python(self):
        ua = _utils.build_user_agent("1.0.0", "requests")
        assert "thordata-python-sdk/1.0.0" in ua
        assert "python/" in ua
        assert "requests" in ua

    def test_semicolons_removed_from_system(self):
        with patch("thordata._utils.platform.system", return_value="Win;dows"):
            ua = _utils.build_user_agent("1.0.0", "aiohttp")
            assert "Win" in ua
