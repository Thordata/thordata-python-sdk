import requests
from requests.exceptions import RequestException
import logging

# 配置日志（可选，用于调试）
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ThordataClient:
    """
    Thordata 代理同步客户端。
    用于封装代理认证信息，并简化 GET/POST 请求的发送。
    """
    def __init__(self, api_key: str, proxy_host: str = "proxy.thordata.com:8000"):
        """
        Thordata 同步客户端初始化。
        :param api_key: 你的 Thordata API 密钥。
        :param proxy_host: Thordata 代理主机地址（默认值）。
        """
        self.api_key = api_key
        self.proxy_host = proxy_host
        self.base_url = "https://api.thordata.com/v1"
        
        # 🌟 修复点 1：新增 proxy_url 属性，用于测试断言和内部代理 URL 构建
        # 格式为：http://{API_KEY}:@{代理主机} (密码为空)
        self.proxy_url = f"http://{self.api_key}:@{self.proxy_host}" 
        
        # 🌟 修复点 2：创建并配置 requests Session，以便复用连接和代理设置
        self.session = requests.Session()
        self._setup_proxy()

    def _setup_proxy(self):
        """配置 requests Session 使用 Thordata 的认证代理"""
        # 将代理配置应用到 Session
        self.session.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        通过 Thordata 代理发送 GET 请求。
        
        :param url: 目标 URL
        :param kwargs: 传递给 requests.get() 的额外参数（如 headers, timeout 等）
        :return: requests.Response 对象
        """
        print(f"DEBUG: Requesting {url} via {self.proxy_host}")

        try:
            # 🌟 修复点 3：直接使用 self.session，而不是在 get 方法内创建新 session
            response = self.session.get(
                url, 
                timeout=30, # 默认超时 30 秒
                **kwargs
            )
            # 检查响应状态码，如果 >=400 则抛出异常
            response.raise_for_status() 
            return response
        except RequestException as e:
            logger.error(f"Sync Request failed for {url}. Details: {e}")
            raise # 重新抛出异常，让调用方处理