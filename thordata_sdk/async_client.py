# async_client.py
import aiohttp
import asyncio
from typing import Dict, Any, Optional

class AsyncThordataClient:
    """
    Thordata 代理异步客户端。
    使用 aiohttp 库，用于高并发、低延迟的 AI 和数据采集任务。
    
    使用示例：
    async with AsyncThordataClient(...) as client:
        response = await client.get(...)
    """
    
    def __init__(self, auth_user: str, auth_pass: str, proxy_host: str = "gate.thordata.com", port: int = 22225):
        """
        初始化异步客户端。
        
        :param auth_user: 账户的用户名
        :param auth_pass: 账户的密码
        :param proxy_host: Thordata 的代理网关地址
        :param port: 代理端口
        """
        # aiohttp 代理认证信息需要单独传递
        self.proxy_auth = aiohttp.BasicAuth(auth_user, auth_pass)
        self.proxy_url = f"http://{proxy_host}:{port}"
        
        # Session 用于复用 TCP 连接，提升性能
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """支持 async with 语法，进入时创建 Session"""
        if self._session is None or self._session.closed:
            # 创建一个 Session，可以设置默认的连接参数
            # 使用 trust_env=True 可以利用系统证书，更安全
            self._session = aiohttp.ClientSession(trust_env=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """支持 async with 语法，退出时关闭 Session，释放资源"""
        await self.close()
        
    async def close(self):
        """
        显式关闭客户端会话 (Session)。
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        通过 Thordata 代理发送异步 GET 请求。

        :param url: 目标 URL
        :param kwargs: 传递给 session.get() 的额外参数（如 headers, cookies, data 等）
        :return: aiohttp.ClientResponse 对象
        """
        if self._session is None:
             raise RuntimeError("Client session not initialized. Please use 'async with AsyncThordataClient(...)' or call '__aenter__' manually.")
             
        print(f"DEBUG: Async Requesting {url} via {self.proxy_url}")
        
        try:
            # 注意：await 是异步编程的关键，用于等待网络 I/O 完成
            response = await self._session.get(
                url, 
                proxy=self.proxy_url, 
                proxy_auth=self.proxy_auth,
                # 设置全局超时，避免长时间挂起
                timeout=aiohttp.ClientTimeout(total=15),
                **kwargs
            )
            # raise_for_status() 会在遇到 4xx/5xx 错误时抛出异常
            response.raise_for_status()
            
            return response

        except aiohttp.ClientError as e:
            # 捕获所有 aiohttp 相关的错误，如连接错误、DNS 查找失败等
            print(f"ERROR: Async Request failed for {url}. Details: {e}")
            raise