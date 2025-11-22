# tests/test_async_client.py
import pytest
import aiohttp
from aioresponses import aioresponses
from thordata_sdk import AsyncThordataClient

# 修复点：添加此行，标记整个模块的测试为异步模式
pytestmark = pytest.mark.asyncio

# 定义测试用的认证信息
TEST_USER = "async_test_user"
TEST_PASS = "async_test_pass"
TEST_HOST = "gate.thordata.com"
TEST_PORT = 22225

# ----------------------------------------------------
# 1. Fixture: 创建异步客户端实例
@pytest.fixture
# 🌟 关键修复点：移除 @pytest.mark.asyncio 标记
async def async_client():
    """创建一个 AsyncThordataClient 实例，并使用 async with 块管理生命周期"""
    async with AsyncThordataClient(api_key=TEST_USER) as client: 
        yield client
# ----------------------------------------------------

# 2. 测试初始化
@pytest.mark.asyncio
async def test_async_client_initialization(async_client):
    """测试异步客户端初始化和属性设置是否正确"""
    # 移除 client = await async_client.__anext__()
    expected_url = f"http://{TEST_HOST}:{TEST_PORT}"

    # 直接使用 async_client 变量
    assert async_client.proxy_url == expected_url
    assert isinstance(async_client.proxy_auth, aiohttp.BasicAuth)
    assert async_client.proxy_auth.login == TEST_USER

    # 检查 session 是否已创建
    assert isinstance(async_client._session, aiohttp.ClientSession)
    print("\n✅ Test: Async initialization successful.")
    # 移除 await async_client.aclose()


# 3. 测试成功请求
@pytest.mark.asyncio
async def test_async_successful_request(async_client):
    """测试异步客户端发送成功请求 (200)"""
    # 移除 client = await async_client.__anext__()
    
    mock_url = "http://example.com/async_test"
    mock_response_data = {"status": "async_ok", "proxy_check": True}

    with aioresponses() as m:
        m.get(mock_url, status=200, payload=mock_response_data)
        
        # 直接使用 async_client 调用 get 方法
        response = await async_client.get(mock_url)
        
        assert response.status == 200
        data = await response.json()
        assert data == mock_response_data
        print("\n✅ Test: Async successful request handled.")
    
    # 移除 await async_client.aclose()


# 4. 测试错误处理
@pytest.mark.asyncio
async def test_async_http_error_handling(async_client):
    """测试异步客户端处理 HTTP 错误 (如 401 Unauthorized)"""
    # 移除 client = await async_client.__anext__()
    
    error_url = "http://example.com/async_error"

    with aioresponses() as m:
        m.get(error_url, status=401)

        with pytest.raises(aiohttp.ClientResponseError):
            # 直接使用 async_client 调用 get 方法
            await async_client.get(error_url)

        print("\n✅ Test: Async HTTP error handling correct.")
    
    # 移除 await async_client.aclose()