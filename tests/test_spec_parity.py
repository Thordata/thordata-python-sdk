import json
import os
from pathlib import Path

import pytest

from thordata.exceptions import raise_for_code
from thordata.models import ProxyProduct, SerpRequest


def _load_spec() -> dict:
    spec_path = os.getenv("THORDATA_SDK_SPEC_PATH")
    if spec_path:
        return json.loads(Path(spec_path).read_text(encoding="utf-8"))

    default = Path(__file__).resolve().parent.parent / "sdk-spec" / "v1.json"
    if not default.exists():
        pytest.skip(f"Spec file not found: {default}")
    return json.loads(default.read_text(encoding="utf-8"))


def test_spec_proxy_ports_match_python() -> None:
    spec = _load_spec()
    proxy = spec["proxy"]["products"]

    assert ProxyProduct.RESIDENTIAL.default_port == int(proxy["residential"]["port"])
    assert ProxyProduct.MOBILE.default_port == int(proxy["mobile"]["port"])
    assert ProxyProduct.DATACENTER.default_port == int(proxy["datacenter"]["port"])
    assert ProxyProduct.ISP.default_port == int(proxy["isp"]["port"])


def test_spec_serp_search_type_mapping_matches_python() -> None:
    spec = _load_spec()
    mapping = spec["serp"]["mappings"]["searchTypeToTbm"]

    assert SerpRequest.SEARCH_TYPE_MAP["news"] == mapping["news"]
    assert SerpRequest.SEARCH_TYPE_MAP["images"] == mapping["images"]
    assert SerpRequest.SEARCH_TYPE_MAP["shopping"] == mapping["shopping"]
    assert SerpRequest.SEARCH_TYPE_MAP["videos"] == mapping["videos"]


def test_spec_serp_time_filter_mapping_matches_python() -> None:
    spec = _load_spec()
    mapping = spec["serp"]["mappings"]["timeFilterToTbs"]

    assert SerpRequest.TIME_FILTER_MAP["week"] == mapping["week"]
    assert SerpRequest.TIME_FILTER_MAP["day"] == mapping["day"]
    assert SerpRequest.TIME_FILTER_MAP["month"] == mapping["month"]
    assert SerpRequest.TIME_FILTER_MAP["year"] == mapping["year"]


def test_spec_webunlocker_base_url_aliases() -> None:
    spec = _load_spec()
    base_urls = spec["env"]["baseUrls"]

    webunlocker = base_urls["webunlocker"]
    universalapi = base_urls["universalapi"]

    assert webunlocker["default"] == "https://webunlocker.thordata.com"
    assert "https://universalapi.thordata.com" in webunlocker.get("aliases", [])

    assert universalapi["default"] == "https://universalapi.thordata.com"
    assert "https://webunlocker.thordata.com" in universalapi.get("aliases", [])


def test_spec_tasks_paths_match_python_sdk_conventions() -> None:
    spec = _load_spec()

    # endpoints.yaml
    endpoints = spec["endpoints"]
    assert endpoints["serp"]["requestPath"] == "/request"
    assert endpoints["serp"]["builderPath"] == "/builder"
    assert endpoints["serp"]["videoBuilderPath"] == "/video_builder"

    assert endpoints["webScraper"]["statusPath"] == "/tasks-status"
    assert endpoints["webScraper"]["downloadPath"] == "/tasks-download"
    assert endpoints["webScraper"]["listPath"] == "/tasks-list"

    # tasks.yaml
    tasks = spec["tasks"]
    assert tasks["builder"]["endpoint"] == "/builder"
    assert tasks["videoBuilder"]["endpoint"] == "/video_builder"
    assert tasks["status"]["endpoint"] == "/tasks-status"
    assert tasks["download"]["endpoint"] == "/tasks-download"
    assert tasks["list"]["endpoint"] == "/tasks-list"


def test_raise_for_code_precedence_payload_code_over_http_status() -> None:
    payload = {"code": 300, "msg": "Not collected"}
    with pytest.raises(Exception) as excinfo:
        raise_for_code("Error", status_code=200, code=300, payload=payload)
    assert "NotCollected" in excinfo.value.__class__.__name__
