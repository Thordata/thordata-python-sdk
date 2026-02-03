"""
Web Scraper Task types.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import unquote

from .common import CommonSettings, ThordataBaseConfig


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    READY = "ready"
    SUCCESS = "success"
    FINISHED = "finished"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

    @classmethod
    def is_terminal(cls, status: TaskStatus) -> bool:
        return status in {
            cls.READY,
            cls.SUCCESS,
            cls.FINISHED,
            cls.FAILED,
            cls.ERROR,
            cls.CANCELLED,
        }

    @classmethod
    def is_success(cls, status: TaskStatus) -> bool:
        return status in {cls.READY, cls.SUCCESS, cls.FINISHED}

    @classmethod
    def is_failure(cls, status: TaskStatus) -> bool:
        return status in {cls.FAILED, cls.ERROR}


class DataFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


def _normalize_url_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    # Decode all percent-encoded characters to match Dashboard format
    # Dashboard expects URLs in their raw/decoded form, not URL-encoded
    # This ensures API/SDK submissions match manual Dashboard input exactly
    try:
        # Check if URL contains any percent-encoded characters
        if "%" in value:
            # Fully decode the URL to match Dashboard format
            decoded = unquote(value)
            # If decoding changed the value, use decoded version
            # This handles cases like %26 -> &, %3A -> :, %2F -> /, etc.
            if decoded != value:
                return decoded
    except Exception:
        # If decoding fails, return original value
        pass
    return value


def _normalize_parameters(params: dict[str, Any]) -> dict[str, Any]:
    # All parameter keys that contain URLs and should be normalized
    # This ensures API/SDK submissions match Dashboard format exactly
    url_keys = {
        "url",
        "domain",
        "profileurl",
        "posturl",
        "seller_url",
        # Additional URL-related keys that may be used
        "link",
        "href",
        "page_url",
        "product_url",
        "category_url",
    }
    out: dict[str, Any] = {}
    for k, v in params.items():
        if k in url_keys:
            out[k] = _normalize_url_value(v)
        else:
            out[k] = v
    return out


@dataclass
class ScraperTaskConfig(ThordataBaseConfig):
    file_name: str
    spider_id: str
    spider_name: str
    parameters: dict[str, Any] | list[dict[str, Any]]
    universal_params: dict[str, Any] | None = None
    include_errors: bool = True
    data_format: DataFormat | str | None = (
        None  # Support json, csv, xlsx output formats
    )

    def to_payload(self) -> dict[str, Any]:
        # Normalize parameters: decode percent-encoded URLs to reduce API/Dashboard divergence
        if isinstance(self.parameters, list):
            normalized_list = [_normalize_parameters(p) for p in self.parameters]
            params_json = json.dumps(normalized_list)
        else:
            normalized_one = _normalize_parameters(self.parameters)
            params_json = json.dumps([normalized_one])

        payload: dict[str, Any] = {
            "file_name": self.file_name,
            "spider_id": self.spider_id,
            "spider_name": self.spider_name,
            "spider_parameters": params_json,
            "spider_errors": "true" if self.include_errors else "false",
        }
        if self.universal_params:
            payload["spider_universal"] = json.dumps(self.universal_params)
        # Add data_format if specified (for json/csv/xlsx output)
        if self.data_format:
            fmt = (
                self.data_format.value
                if isinstance(self.data_format, DataFormat)
                else str(self.data_format).lower()
            )
            payload["data_format"] = fmt
        return payload


@dataclass
class VideoTaskConfig(ThordataBaseConfig):
    file_name: str
    spider_id: str
    spider_name: str
    parameters: dict[str, Any] | list[dict[str, Any]]
    common_settings: CommonSettings
    include_errors: bool = True

    def to_payload(self) -> dict[str, Any]:
        if isinstance(self.parameters, list):
            params_json = json.dumps(self.parameters)
        else:
            params_json = json.dumps([self.parameters])

        payload: dict[str, Any] = {
            "file_name": self.file_name,
            "spider_id": self.spider_id,
            "spider_name": self.spider_name,
            "spider_parameters": params_json,
            "spider_errors": "true" if self.include_errors else "false",
            "spider_universal": self.common_settings.to_json(),
        }
        return payload


@dataclass
class TaskStatusResponse:
    task_id: str
    status: str
    progress: int | None = None
    message: str | None = None

    def is_complete(self) -> bool:
        terminal_statuses = {
            "ready",
            "success",
            "finished",
            "failed",
            "error",
            "cancelled",
        }
        return self.status.lower() in terminal_statuses

    def is_success(self) -> bool:
        return self.status.lower() in {"ready", "success", "finished"}


@dataclass
class UsageStatistics:
    total_usage_traffic: float
    traffic_balance: float
    query_days: int
    range_usage_traffic: float
    data: list[dict[str, Any]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UsageStatistics:
        return cls(
            total_usage_traffic=float(data.get("total_usage_traffic", 0)),
            traffic_balance=float(data.get("traffic_balance", 0)),
            query_days=int(data.get("query_days", 0)),
            range_usage_traffic=float(data.get("range_usage_traffic", 0)),
            data=data.get("data", []),
        )

    def total_usage_gb(self) -> float:
        return self.total_usage_traffic / (1024 * 1024)

    def balance_gb(self) -> float:
        return self.traffic_balance / (1024 * 1024)
