"""
Tests for batch task creation logic in ThordataClient.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from thordata import ThordataClient
from thordata.types import ScraperTaskConfig


class TestBatchCreation:
    """Test suite for verifying batch vs single task creation payloads."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="test_scraper_token",
            public_token="test_public_token",
            public_key="test_public_key",
        )

    def test_single_dict_parameter(self, client):
        """Verify that a single dict parameter is wrapped in a list [params]."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "data": {"task_id": "single_task_123"},
        }

        # Parameters as a single dict
        params = {"url": "https://example.com", "depth": 1}

        with patch.object(
            client, "_api_request_with_retry", return_value=mock_response
        ) as mock_req:
            task_id = client.create_scraper_task(
                file_name="test_single",
                spider_id="s1",
                spider_name="spider_1",
                parameters=params,
            )

            assert task_id == "single_task_123"

            # Verify payload
            mock_req.assert_called_once()
            args, kwargs = mock_req.call_args
            data = kwargs["data"]

            # spider_parameters should be a JSON string of a LIST containing the dict
            assert "spider_parameters" in data
            parsed_params = json.loads(data["spider_parameters"])
            assert isinstance(parsed_params, list)
            assert len(parsed_params) == 1
            assert parsed_params[0] == params

    def test_batch_list_parameter(self, client):
        """Verify that a list of parameters is sent as is (serialized)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "data": {"task_id": "batch_task_456"},
        }

        # Parameters as a list of dicts
        params = [
            {"url": "https://example.com/1", "depth": 1},
            {"url": "https://example.com/2", "depth": 2},
        ]

        with patch.object(
            client, "_api_request_with_retry", return_value=mock_response
        ) as mock_req:
            task_id = client.create_scraper_task(
                file_name="test_batch",
                spider_id="s1",
                spider_name="spider_1",
                parameters=params,
            )

            assert task_id == "batch_task_456"

            # Verify payload
            mock_req.assert_called_once()
            args, kwargs = mock_req.call_args
            data = kwargs["data"]

            assert "spider_parameters" in data
            parsed_params = json.loads(data["spider_parameters"])
            assert isinstance(parsed_params, list)
            assert len(parsed_params) == 2
            assert parsed_params == params

    def test_scraper_task_config_direct_serialization(self):
        """Test ScraperTaskConfig.to_payload directly."""
        # Single
        config_single = ScraperTaskConfig(
            file_name="f", spider_id="id", spider_name="name", parameters={"a": 1}
        )
        payload_single = config_single.to_payload()
        assert json.loads(payload_single["spider_parameters"]) == [{"a": 1}]

        # Batch
        config_batch = ScraperTaskConfig(
            file_name="f",
            spider_id="id",
            spider_name="name",
            parameters=[{"a": 1}, {"b": 2}],
        )
        payload_batch = config_batch.to_payload()
        assert json.loads(payload_batch["spider_parameters"]) == [{"a": 1}, {"b": 2}]
