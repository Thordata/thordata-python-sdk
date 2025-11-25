# thordata_sdk/parameters.py
from typing import Dict, Any

def normalize_serp_params(engine: str, query: str, **kwargs) -> Dict[str, Any]:
    """
    统一不同搜索引擎的参数差异。
    """
    # 1. 基础参数
    payload = {
        "num": str(kwargs.get("num", 10)),
        "json": "1",
        "engine": engine,
    }

    # 2. 处理查询关键词 (Yandex 用 text，其他用 q)
    if engine == "yandex":
        payload["text"] = query
        # 如果用户没传 url，给个默认的
        if "url" not in kwargs:
            payload["url"] = "yandex.com"
    else:
        payload["q"] = query
        
        # 3. 处理默认 URL (如果用户没传)
        if "url" not in kwargs:
            defaults = {
                "google": "google.com",
                "bing": "bing.com",
                "duckduckgo": "duckduckgo.com",
                "baidu": "baidu.com"
            }
            if engine in defaults:
                payload["url"] = defaults[engine]

    # 4. 把用户传入的其他所有参数（比如 type="shopping", google_domain="google.co.uk"）都透传进去
    # 这样你就不用去定义那几十种类型了，用户传啥就是啥
    for k, v in kwargs.items():
        if k not in ["num", "engine", "q", "text"]: # 避免覆盖
            payload[k] = v

    return payload