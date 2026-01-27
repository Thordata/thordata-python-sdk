"""
Tests for thordata.retry module.
"""

from unittest.mock import MagicMock, patch

import pytest

from thordata.exceptions import (
    ThordataNetworkError,
    ThordataRateLimitError,
    ThordataServerError,
    ThordataValidationError,
)
from thordata.retry import (
    RetryableRequest,
    RetryConfig,
    with_retry,
)

# -----------------------------------------------------------------------------
# RetryConfig.calculate_delay
# -----------------------------------------------------------------------------


class TestRetryConfigCalculateDelay:
    def test_exponential_backoff_no_jitter(self):
        config = RetryConfig(backoff_factor=1.0, max_backoff=100, jitter=False)
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 8.0

    def test_max_backoff_cap(self):
        config = RetryConfig(backoff_factor=10.0, max_backoff=50, jitter=False)
        assert config.calculate_delay(0) == 10.0
        assert config.calculate_delay(3) == 50.0  # 80 capped to 50
        assert config.calculate_delay(10) == 50.0

    def test_jitter_keeps_delay_positive(self):
        config = RetryConfig(backoff_factor=0.5, jitter=True, jitter_factor=0.5)
        for _ in range(20):
            d = config.calculate_delay(0)
            assert d >= 0.1


# -----------------------------------------------------------------------------
# RetryConfig.should_retry
# -----------------------------------------------------------------------------


class TestRetryConfigShouldRetry:
    def test_no_retry_when_attempt_exceeds_max(self):
        config = RetryConfig(max_retries=2)
        assert (
            config.should_retry(ThordataNetworkError("x"), attempt=2, status_code=None)
            is False
        )
        assert (
            config.should_retry(ThordataNetworkError("x"), attempt=3, status_code=None)
            is False
        )

    def test_retry_on_status_code(self):
        config = RetryConfig(max_retries=5)
        assert config.should_retry(Exception("x"), attempt=0, status_code=503) is True
        assert config.should_retry(Exception("x"), attempt=0, status_code=429) is True
        assert config.should_retry(Exception("x"), attempt=0, status_code=500) is True
        assert config.should_retry(Exception("x"), attempt=0, status_code=400) is False

    def test_retry_on_network_error(self):
        config = RetryConfig(max_retries=5)
        assert config.should_retry(ThordataNetworkError("err"), attempt=0) is True

    def test_retry_on_server_error(self):
        config = RetryConfig(max_retries=5)
        assert (
            config.should_retry(ThordataServerError("err", code=500), attempt=0) is True
        )

    def test_retry_on_rate_limit_error(self):
        config = RetryConfig(max_retries=5)
        assert (
            config.should_retry(ThordataRateLimitError("limit", code=429), attempt=0)
            is True
        )

    def test_no_retry_on_validation_error(self):
        config = RetryConfig(max_retries=5)
        err = ThordataValidationError("bad", code=400)
        assert config.should_retry(err, attempt=0, status_code=400) is False


# -----------------------------------------------------------------------------
# _extract_status_code (via behavior in should_retry / with_retry)
# We test extraction by checking that with_retry retries on exceptions that have status.
# Direct unit test would require importing _extract_status_code (private).
# -----------------------------------------------------------------------------


class TestExtractStatusCode:
    """Test status code extraction by importing the private helper."""

    def test_from_thordata_api_error(self):
        from thordata.exceptions import ThordataServerError
        from thordata.retry import _extract_status_code

        e = ThordataServerError("x", status_code=503, code=503)
        assert _extract_status_code(e) == 503

    def test_from_original_error(self):
        import requests

        from thordata.retry import _extract_status_code

        inner = requests.exceptions.HTTPError()
        inner.response = MagicMock(status_code=502)
        e = ThordataNetworkError("wrap", original_error=inner)
        assert _extract_status_code(e) == 502

    def test_from_response_attribute(self):
        import requests

        from thordata.retry import _extract_status_code

        e = requests.exceptions.HTTPError()
        e.response = MagicMock(status_code=503)
        assert _extract_status_code(e) == 503

    def test_from_status_attribute(self):
        from thordata.retry import _extract_status_code

        e = MagicMock(spec=[], status=429)
        e.status = 429
        assert _extract_status_code(e) == 429

    def test_none_when_no_code(self):
        from thordata.retry import _extract_status_code

        assert _extract_status_code(ValueError("x")) is None


# -----------------------------------------------------------------------------
# with_retry sync
# -----------------------------------------------------------------------------


class TestWithRetrySync:
    def test_success_on_first_call(self):
        config = RetryConfig(max_retries=2)
        call_count = 0

        @with_retry(config)
        def fn():
            nonlocal call_count
            call_count += 1
            return 42

        assert fn() == 42
        assert call_count == 1

    def test_success_on_second_call(self):
        config = RetryConfig(max_retries=3, backoff_factor=0.01, jitter=False)
        call_count = 0

        @with_retry(config)
        def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ThordataNetworkError("tmp")
            return 99

        assert fn() == 99
        assert call_count == 2

    def test_raises_after_exhausting_retries(self):
        config = RetryConfig(max_retries=2, backoff_factor=0.01, jitter=False)
        call_count = 0

        @with_retry(config)
        def fn():
            nonlocal call_count
            call_count += 1
            raise ThordataNetworkError("fail")

        with pytest.raises(ThordataNetworkError, match="fail"):
            fn()
        assert call_count == 3  # initial + 2 retries

    def test_no_retry_on_non_retryable_exception(self):
        config = RetryConfig(max_retries=3, backoff_factor=0.01, jitter=False)
        call_count = 0

        @with_retry(config)
        def fn():
            nonlocal call_count
            call_count += 1
            raise ThordataValidationError("bad", code=400)

        with pytest.raises(ThordataValidationError):
            fn()
        assert call_count == 1

    def test_on_retry_callback_called(self):
        config = RetryConfig(max_retries=2, backoff_factor=0.01, jitter=False)
        retries_seen = []

        def on_retry(attempt: int, exc: Exception, delay: float) -> None:
            retries_seen.append((attempt, type(exc).__name__, delay))

        call_count = 0

        @with_retry(config, on_retry=on_retry)
        def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ThordataNetworkError("tmp")
            return 1

        fn()
        assert len(retries_seen) == 1
        assert retries_seen[0][0] == 0
        assert retries_seen[0][1] == "ThordataNetworkError"


# -----------------------------------------------------------------------------
# with_retry async
# -----------------------------------------------------------------------------


class TestWithRetryAsync:
    @pytest.mark.asyncio
    async def test_async_success_on_first_call(self):
        config = RetryConfig(max_retries=2)
        call_count = 0

        @with_retry(config)
        async def fn():
            nonlocal call_count
            call_count += 1
            return 42

        result = await fn()
        assert result == 42
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_success_on_second_call(self):
        config = RetryConfig(max_retries=3, backoff_factor=0.01, jitter=False)
        call_count = 0

        @with_retry(config)
        async def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ThordataNetworkError("tmp")
            return 99

        result = await fn()
        assert result == 99
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_raises_after_exhausting_retries(self):
        config = RetryConfig(max_retries=1, backoff_factor=0.01, jitter=False)
        call_count = 0

        @with_retry(config)
        async def fn():
            nonlocal call_count
            call_count += 1
            raise ThordataNetworkError("fail")

        with pytest.raises(ThordataNetworkError):
            await fn()
        assert call_count == 2


# -----------------------------------------------------------------------------
# RetryableRequest
# -----------------------------------------------------------------------------


class TestRetryableRequest:
    def test_should_continue_increments_attempt(self):
        config = RetryConfig(max_retries=3)
        with RetryableRequest(config) as retry:
            assert retry.should_continue(ThordataNetworkError("x")) is True
            assert retry.attempt == 1
            assert retry.should_continue(ThordataNetworkError("x")) is True
            assert retry.attempt == 2
            assert retry.should_continue(ThordataNetworkError("x")) is True
            assert retry.attempt == 3
            assert retry.should_continue(ThordataNetworkError("x")) is False

    def test_wait_uses_calculate_delay(self):
        config = RetryConfig(max_retries=2, backoff_factor=0.05, jitter=False)
        with RetryableRequest(config) as retry:
            retry.should_continue(ThordataNetworkError("x"))
            with patch("thordata.retry.time.sleep") as mock_sleep:
                delay = retry.wait()
                assert delay == 0.05
                mock_sleep.assert_called_once_with(0.05)

    def test_wait_respects_retry_after_for_rate_limit(self):
        config = RetryConfig(max_retries=2, backoff_factor=0.01, jitter=False)
        with RetryableRequest(config) as retry:
            retry.should_continue(
                ThordataRateLimitError("limit", code=429, retry_after=5.0)
            )
            with patch("thordata.retry.time.sleep") as mock_sleep:
                delay = retry.wait()
                assert delay == 5.0
                mock_sleep.assert_called_once_with(5.0)
