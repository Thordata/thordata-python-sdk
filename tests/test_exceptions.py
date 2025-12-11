"""
Tests for thordata.exceptions module.
"""

import pytest

from thordata.exceptions import (
    ThordataAPIError,
    ThordataAuthError,
    ThordataConfigError,
    ThordataError,
    ThordataNetworkError,
    ThordataRateLimitError,
    ThordataServerError,
    ThordataTimeoutError,
    ThordataValidationError,
    is_retryable_exception,
    raise_for_code,
)


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_base_error(self):
        """Test base ThordataError."""
        err = ThordataError("test message")
        assert str(err) == "test message"
        assert err.message == "test message"

    def test_config_error(self):
        """Test ThordataConfigError."""
        err = ThordataConfigError("missing token")
        assert isinstance(err, ThordataError)

    def test_network_error(self):
        """Test ThordataNetworkError."""
        original = ConnectionError("connection refused")
        err = ThordataNetworkError("network failed", original_error=original)
        assert isinstance(err, ThordataError)
        assert err.original_error is original

    def test_timeout_error(self):
        """Test ThordataTimeoutError."""
        err = ThordataTimeoutError("request timed out")
        assert isinstance(err, ThordataNetworkError)

    def test_api_error(self):
        """Test ThordataAPIError."""
        err = ThordataAPIError(
            "api error",
            status_code=400,
            code=400,
            payload={"error": "bad request"},
        )
        assert isinstance(err, ThordataError)
        assert err.status_code == 400
        assert err.code == 400
        assert err.payload == {"error": "bad request"}

    def test_auth_error(self):
        """Test ThordataAuthError."""
        err = ThordataAuthError("unauthorized", status_code=401)
        assert isinstance(err, ThordataAPIError)
        assert err.is_retryable is False

    def test_rate_limit_error(self):
        """Test ThordataRateLimitError."""
        err = ThordataRateLimitError(
            "rate limited",
            status_code=429,
            retry_after=60,
        )
        assert isinstance(err, ThordataAPIError)
        assert err.retry_after == 60
        assert err.is_retryable is True

    def test_server_error(self):
        """Test ThordataServerError."""
        err = ThordataServerError("internal error", status_code=500)
        assert isinstance(err, ThordataAPIError)
        assert err.is_retryable is True

    def test_validation_error(self):
        """Test ThordataValidationError."""
        err = ThordataValidationError("invalid params", status_code=400)
        assert isinstance(err, ThordataAPIError)
        assert err.is_retryable is False


class TestRaiseForCode:
    """Tests for raise_for_code function."""

    def test_raises_auth_error_for_401(self):
        """Test that 401 raises ThordataAuthError."""
        with pytest.raises(ThordataAuthError):
            raise_for_code("auth failed", status_code=401)

    def test_raises_auth_error_for_403(self):
        """Test that 403 raises ThordataAuthError."""
        with pytest.raises(ThordataAuthError):
            raise_for_code("forbidden", status_code=403)

    def test_raises_rate_limit_error_for_429(self):
        """Test that 429 raises ThordataRateLimitError."""
        with pytest.raises(ThordataRateLimitError):
            raise_for_code("rate limited", status_code=429)

    def test_raises_rate_limit_error_for_402(self):
        """Test that 402 raises ThordataRateLimitError."""
        with pytest.raises(ThordataRateLimitError):
            raise_for_code("payment required", status_code=402)

    def test_raises_server_error_for_500(self):
        """Test that 500 raises ThordataServerError."""
        with pytest.raises(ThordataServerError):
            raise_for_code("server error", status_code=500)

    def test_raises_server_error_for_503(self):
        """Test that 503 raises ThordataServerError."""
        with pytest.raises(ThordataServerError):
            raise_for_code("service unavailable", status_code=503)

    def test_raises_validation_error_for_400(self):
        """Test that 400 raises ThordataValidationError."""
        with pytest.raises(ThordataValidationError):
            raise_for_code("bad request", status_code=400)

    def test_raises_generic_api_error(self):
        """Test that unknown codes raise ThordataAPIError."""
        with pytest.raises(ThordataAPIError):
            raise_for_code("unknown error", status_code=418)


class TestIsRetryableException:
    """Tests for is_retryable_exception function."""

    def test_network_error_is_retryable(self):
        """Test that network errors are retryable."""
        err = ThordataNetworkError("connection failed")
        assert is_retryable_exception(err) is True

    def test_timeout_error_is_retryable(self):
        """Test that timeout errors are retryable."""
        err = ThordataTimeoutError("timed out")
        assert is_retryable_exception(err) is True

    def test_server_error_is_retryable(self):
        """Test that server errors are retryable."""
        err = ThordataServerError("internal error", status_code=500)
        assert is_retryable_exception(err) is True

    def test_rate_limit_error_is_retryable(self):
        """Test that rate limit errors are retryable."""
        err = ThordataRateLimitError("rate limited", status_code=429)
        assert is_retryable_exception(err) is True

    def test_auth_error_is_not_retryable(self):
        """Test that auth errors are not retryable."""
        err = ThordataAuthError("unauthorized", status_code=401)
        assert is_retryable_exception(err) is False

    def test_validation_error_is_not_retryable(self):
        """Test that validation errors are not retryable."""
        err = ThordataValidationError("bad request", status_code=400)
        assert is_retryable_exception(err) is False
