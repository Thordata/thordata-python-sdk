"""
Constants for the Thordata Python SDK.

This module centralizes all API endpoints, error codes, status codes,
and other string constants to prevent typos and improve maintainability.
"""

from __future__ import annotations

# =============================================================================
# API Base URLs
# =============================================================================


class APIBaseURL:
    """Base URLs for Thordata API services."""

    SCRAPER_API = "https://scraperapi.thordata.com"
    UNIVERSAL_API = "https://webunlocker.thordata.com"
    WEB_SCRAPER_API = "https://openapi.thordata.com/api/web-scraper-api"
    LOCATIONS_API = "https://openapi.thordata.com/api/locations"
    GATEWAY_API = "https://openapi.thordata.com/api/gateway"
    CHILD_API = "https://openapi.thordata.com/api/child"
    WHITELIST_API = "https://openapi.thordata.com/api"
    PROXY_API = "https://openapi.thordata.com/api"
    IP_API = "https://get-ip.thordata.net"


# =============================================================================
# API Endpoints
# =============================================================================


class APIEndpoint:
    """API endpoint paths (relative to base URLs)."""

    # Scraper API endpoints
    SERP_REQUEST = "/request"
    SERP_BUILDER = "/builder"
    SERP_VIDEO_BUILDER = "/video_builder"

    # Universal API endpoints
    UNIVERSAL_REQUEST = "/request"

    # Web Scraper API endpoints
    TASKS_STATUS = "/tasks-status"
    TASKS_DOWNLOAD = "/tasks-download"
    TASKS_LIST = "/tasks-list"
    GET_LATEST_TASK_STATUS = "/api/web_scraper_api/get_latest_task_status"

    # Account Management endpoints
    USAGE_STATISTICS = "/account/usage-statistics"
    PROXY_USERS = "/proxy-users"
    PROXY_USERS_USAGE_STATISTICS = "/proxy-users/usage-statistics"
    PROXY_USERS_USAGE_STATISTICS_HOUR = "/proxy-users/usage-statistics-hour"
    PROXY_USERS_USER_LIST = "/proxy-users/user-list"
    PROXY_USERS_CREATE_USER = "/proxy-users/create-user"
    PROXY_USERS_UPDATE_USER = "/proxy-users/update-user"
    PROXY_USERS_DELETE_USER = "/proxy-users/delete-user"

    # Whitelist endpoints
    WHITELIST_IPS = "/whitelisted-ips"
    WHITELIST_ADD_IP = "/whitelisted-ips/add-ip"
    WHITELIST_DELETE_IP = "/whitelisted-ips/delete-ip"
    WHITELIST_IP_LIST = "/whitelisted-ips/ip-list"

    # Proxy endpoints
    PROXY_LIST = "/proxy/proxy-list"
    PROXY_EXPIRATION_TIME = "/proxy/expiration-time"

    # IP API endpoints
    IP_API_UNLIMITED = "/unlimited_api"
    IP_API_STANDARD = "/api"


# =============================================================================
# HTTP Status Codes
# =============================================================================


class HTTPStatus:
    """HTTP status codes used by Thordata APIs."""

    OK = 200
    NOT_COLLECTED = 300
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    PAYMENT_REQUIRED = 402
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


# =============================================================================
# API Error Codes
# =============================================================================


class APIErrorCode:
    """Application-level error codes returned by Thordata APIs."""

    SUCCESS = 200
    NOT_COLLECTED = 300
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    PAYMENT_REQUIRED = 402
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


# =============================================================================
# Error Messages
# =============================================================================


class ErrorMessage:
    """Standardized error messages."""

    # Configuration errors
    MISSING_CREDENTIALS = "Missing required credentials"
    SCRAPER_TOKEN_REQUIRED = "scraper_token is required for this operation"
    MISSING_PUBLIC_CREDENTIALS = (
        "public_token and public_key are required for this operation"
    )
    PUBLIC_CREDENTIALS_REQUIRED = (
        "public_token and public_key are required for this operation"
    )
    INVALID_AUTH_MODE = "Invalid auth_mode: {mode}. Must be 'bearer' or 'header_token'."

    # Network errors
    REQUEST_TIMEOUT = "Request timed out: {error}"
    REQUEST_FAILED = "Request failed: {error}"
    CONNECTION_ERROR = "Connection error: {error}"

    # API errors
    API_ERROR = "API error: {message}"
    AUTH_ERROR = "Authentication failed: {message}"
    RATE_LIMIT_ERROR = "Rate limit exceeded: {message}"
    SERVER_ERROR = "Server error: {message}"
    VALIDATION_ERROR = "Validation error: {message}"
    NOT_COLLECTED_ERROR = "Data not collected: {message}"

    # Proxy errors
    PROXY_ERROR = "Proxy error: {message}"
    INVALID_PROXY_CONFIG = "Invalid proxy configuration: {message}"

    # Task errors
    TASK_NOT_FOUND = "Task not found: {task_id}"
    TASK_FAILED = "Task failed: {task_id}"


# =============================================================================
# Environment Variable Names
# =============================================================================


class EnvVar:
    """Environment variable names for configuration."""

    # Authentication
    SCRAPER_TOKEN = "THORDATA_SCRAPER_TOKEN"
    PUBLIC_TOKEN = "THORDATA_PUBLIC_TOKEN"
    PUBLIC_KEY = "THORDATA_PUBLIC_KEY"

    # Proxy credentials
    RESIDENTIAL_USERNAME = "THORDATA_RESIDENTIAL_USERNAME"
    RESIDENTIAL_PASSWORD = "THORDATA_RESIDENTIAL_PASSWORD"
    UNLIMITED_USERNAME = "THORDATA_UNLIMITED_USERNAME"
    UNLIMITED_PASSWORD = "THORDATA_UNLIMITED_PASSWORD"
    DATACENTER_USERNAME = "THORDATA_DATACENTER_USERNAME"
    DATACENTER_PASSWORD = "THORDATA_DATACENTER_PASSWORD"
    MOBILE_USERNAME = "THORDATA_MOBILE_USERNAME"
    MOBILE_PASSWORD = "THORDATA_MOBILE_PASSWORD"
    ISP_USERNAME = "THORDATA_ISP_USERNAME"
    ISP_PASSWORD = "THORDATA_ISP_PASSWORD"
    BROWSER_USERNAME = "THORDATA_BROWSER_USERNAME"
    BROWSER_PASSWORD = "THORDATA_BROWSER_PASSWORD"

    # Proxy configuration
    PROXY_HOST = "THORDATA_PROXY_HOST"
    PROXY_PORT = "THORDATA_PROXY_PORT"
    UPSTREAM_PROXY = "THORDATA_UPSTREAM_PROXY"

    # API base URLs
    SCRAPERAPI_BASE_URL = "THORDATA_SCRAPERAPI_BASE_URL"
    UNIVERSALAPI_BASE_URL = "THORDATA_UNIVERSALAPI_BASE_URL"
    WEB_SCRAPER_API_BASE_URL = "THORDATA_WEB_SCRAPER_API_BASE_URL"
    LOCATIONS_BASE_URL = "THORDATA_LOCATIONS_BASE_URL"
    GATEWAY_BASE_URL = "THORDATA_GATEWAY_BASE_URL"
    CHILD_BASE_URL = "THORDATA_CHILD_BASE_URL"
    WHITELIST_BASE_URL = "THORDATA_WHITELIST_BASE_URL"
    PROXY_API_BASE_URL = "THORDATA_PROXY_API_BASE_URL"

    # Testing
    INTEGRATION = "THORDATA_INTEGRATION"


# =============================================================================
# Request/Response Keys
# =============================================================================


class RequestKey:
    """Keys used in API request payloads."""

    # Common
    URL = "url"
    QUERY = "query"
    TASK_ID = "task_id"
    TASKS_IDS = "tasks_ids"
    FILE_NAME = "file_name"
    SPIDER_ID = "spider_id"
    SPIDER_NAME = "spider_name"
    SPIDER_PARAMETERS = "spider_parameters"
    SPIDER_ERRORS = "spider_errors"
    COMMON_SETTINGS = "common_settings"

    # SERP
    ENGINE = "engine"
    LOCATION = "location"
    NUM = "num"
    PAGE = "page"
    SEARCH_TYPE = "search_type"
    TIME_RANGE = "time_range"
    DEVICE = "device"
    TBM = "tbm"

    # Universal
    JS_RENDER = "js_render"
    COUNTRY = "country"
    WAIT_FOR = "wait_for"
    WAIT_TIME = "wait_time"

    # Proxy
    USERNAME = "username"
    PASSWORD = "password"
    PRODUCT = "product"
    SESSION_ID = "session_id"
    SESSION_DURATION = "session_duration"

    # Account
    START_TIME = "start_time"
    END_TIME = "end_time"
    DATE = "date"
    USERNAME_FILTER = "username"
    TRAFFIC_LIMIT = "traffic_limit"

    # Whitelist
    IP = "ip"
    IPS = "ips"


class ResponseKey:
    """Keys used in API response payloads."""

    # Common
    CODE = "code"
    MESSAGE = "message"
    DATA = "data"
    REQUEST_ID = "request_id"
    REQUEST_ID_ALT = "requestId"
    RETRY_AFTER = "retry_after"
    RETRY_AFTER_ALT = "retryAfter"

    # Task
    TASK_ID = "task_id"
    STATUS = "status"
    RESULT = "result"
    DOWNLOAD_URL = "download_url"
    ERROR = "error"

    # SERP
    ORGANIC = "organic"
    ADS = "ads"
    RELATED_QUERIES = "related_queries"

    # Usage
    USAGE = "usage"
    BALANCE = "balance"
    TOTAL = "total"


# =============================================================================
# Task Status Values
# =============================================================================


class TaskStatus:
    """Task status values."""

    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    READY = "ready"
    COLLECTING = "collecting"


# =============================================================================
# Auth Modes
# =============================================================================


class AuthMode:
    """Authentication modes."""

    BEARER = "bearer"
    HEADER_TOKEN = "header_token"


# =============================================================================
# HTTP Methods
# =============================================================================


class HTTPMethod:
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


# =============================================================================
# Content Types
# =============================================================================


class ContentType:
    """HTTP content types."""

    JSON = "application/json"
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"


__all__ = [
    "APIBaseURL",
    "APIEndpoint",
    "HTTPStatus",
    "APIErrorCode",
    "ErrorMessage",
    "EnvVar",
    "RequestKey",
    "ResponseKey",
    "TaskStatus",
    "AuthMode",
    "HTTPMethod",
    "ContentType",
]
