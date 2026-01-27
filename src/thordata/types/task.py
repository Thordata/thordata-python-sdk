"""
Web Scraper Task types.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

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


@dataclass
class ScraperTaskConfig(ThordataBaseConfig):
    file_name: str
    spider_id: str
    spider_name: str
    parameters: dict[str, Any] | list[dict[str, Any]]
    universal_params: dict[str, Any] | None = None
    include_errors: bool = True

    def to_payload(self) -> dict[str, Any]:
        # Handle batch parameters: if list, use as is; if dict, wrap in list
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
        }
        if self.universal_params:
            payload["spider_universal"] = json.dumps(self.universal_params)
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
        # Handle batch parameters
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
            # v2.0 Doc explicitly requires 'spider_universal' key for video tasks too sometimes,
            # but usually it's passed as 'common_settings' or 'spider_universal'.
            # Sticking to original models.py key logic for now to ensure stability.
            "spider_universal": self.common_settings.to_json(),
        }
        # Note: If API expects 'common_settings' key specifically, adjust here.
        # Based on v2 context, video builder often uses spider_universal.
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
