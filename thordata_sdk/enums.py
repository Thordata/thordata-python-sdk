# thordata_sdk/enums.py
from enum import Enum

class Engine(str, Enum):
    """SERP 核心支持的四大引擎"""
    GOOGLE = "google"
    BING = "bing"
    YANDEX = "yandex"
    DUCKDUCKGO = "duckduckgo"
    BAIDU = "baidu"

class GoogleSearchType(str, Enum):
    """Google 搜索的常见子类型 (参考你的截图)"""
    SEARCH = "search"      # 默认网页搜索
    MAPS = "maps"          # 地图
    SHOPPING = "shopping"  # 购物
    NEWS = "news"          # 新闻
    IMAGES = "images"      # 图片
    VIDEOS = "videos"      # 视频
    # 其他冷门的先不写，用户可以通过字符串传参