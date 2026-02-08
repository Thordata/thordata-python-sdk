"""
Unit tests for response wrapper.
"""

import pytest

from thordata import APIResponse


class TestAPIResponse:
    """Test APIResponse class."""

    def test_from_dict_success(self):
        data = {"code": 200, "data": {"key": "value"}, "request_id": "abc123"}
        response = APIResponse.from_dict(data)

        assert response.is_success
        assert response.code == 200
        assert response.request_id == "abc123"
        assert response.data == data

    def test_from_dict_error(self):
        data = {"code": 400, "message": "Bad request"}
        response = APIResponse.from_dict(data)

        assert response.is_error
        assert response.code == 400
        assert response.message == "Bad request"

    def test_get_method(self):
        data = {"code": 200, "data": {"key": "value"}}
        response = APIResponse.from_dict(data)

        assert response.get("code") == 200
        assert response.get("data") == {"key": "value"}
        assert response.get("nonexistent", "default") == "default"

    def test_getitem_method(self):
        data = {"code": 200, "data": {"key": "value"}}
        response = APIResponse.from_dict(data)

        assert response["code"] == 200
        assert response["data"] == {"key": "value"}

    def test_getitem_non_dict(self):
        response = APIResponse(data="string_data")

        with pytest.raises(TypeError):
            _ = response["key"]

    def test_repr(self):
        response = APIResponse(
            data={"test": "value"},
            status_code=200,
            code=200,
            request_id="abc123",
        )
        repr_str = repr(response)
        assert "status_code=200" in repr_str
        assert "code=200" in repr_str
        assert "request_id='abc123'" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
