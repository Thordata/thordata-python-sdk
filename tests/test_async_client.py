# test_async_client.py
import pytest
import aiohttp
from aioresponses import aioresponses
from thordata_sdk import AsyncThordataClient

# 定义测试用的认证信息
TEST_USER = "async_test_user"
TEST_PASS = "async_test_pass"
TEST_HOST = "gate.thordata.com"
TEST_PORT = 22225

# ----------------------------------------------------
# 1. Fixture: 创建异步客户端实例
# 使用 pytest.fixture 和 @pytest.mark.asyncio 确保它在异步环境中运行
@pytest.fixture
async def async_client():
    """创建一个 AsyncThordataClient 实例，并使用 async with 块管理生命周期"""
    # 使用 async with 确保 session 在测试结束后被安全关闭
    async with AsyncThordataClient(auth_user=TEST_USER, auth_pass=TEST_PASS) as client:
        yield client
# ----------------------------------------------------

# 2. 测试初始化
@pytest.mark.asyncio
async def test_async_client_initialization(async_client):
    """测试异步客户端初始化和属性设置是否正确"""
    expected_url = f"http://{TEST_HOST}:{TEST_PORT}"
    
    assert async_client.proxy_url == expected_url
    assert isinstance(async_client.proxy_auth, aiohttp.BasicAuth)
    assert async_client.proxy_auth.login == TEST_USER
    
    # 检查 session 是否已创建（进入 async with 块后）
    assert isinstance(async_client._session, aiohttp.ClientSession)
    print("\n✅ Test: Async initialization successful.")


# 3. 测试成功请求
@pytest.mark.asyncio
async def test_async_successful_request(async_client):
    """测试异步客户端发送成功请求 (200)"""
    mock_url = "http://example.com/async_test"
    mock_response_data = {"status": "async_ok", "proxy_check": True}
    
    # aioresponses 用于拦截 aiohttp 的请求，返回模拟响应
    with aioresponses() as m:
        # 模拟对 mock_url 的 GET 请求，返回 200 状态码和 JSON 数据
        m.get(mock_url, status=200, payload=mock_response_data)
        
        # 实际调用异步客户端的 GET 方法
        response = await async_client.get(mock_url)
        
        # 断言：检查响应的状态码和返回的内容
        assert response.status == 200
        # 异步客户端需要 await response.json()
        data = await response.json()
        assert data == mock_response_data
        print("\n✅ Test: Async successful request handled.")

# 4. 测试错误处理
@pytest.mark.asyncio
async def test_async_http_error_handling(async_client):
    """测试异步客户端处理 HTTP 错误 (如 401 Unauthorized)"""
    error_url = "http://example.com/async_error"

    with aioresponses() as m:
        # 模拟返回 401 错误
        m.get(error_url, status=401)
        
        # 使用 pytest.raises 检查是否抛出了 aiohttp.ClientResponseError 异常
        with pytest.raises(aiohttp.ClientResponseError):
            await async_client.get(error_url)
            
        print("\n✅ Test: Async HTTP error handling correct.")