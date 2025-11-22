# test_client.py
import requests
import requests_mock
import pytest
from thordata_sdk.client import ThordataClient

# 定义测试用的认证信息
TEST_USER = "test_user_ai" 
TEST_HOST = "proxy.thordata.com" 
TEST_PORT = 8000 

# 定义一个 Fixture：用于创建客户端实例
@pytest.fixture
def client():
    """创建一个 ThordataClient 实例，供所有测试函数使用"""
    # 确保 ThordataClient 使用正确的参数
    proxy_host = f"{TEST_HOST}:{TEST_PORT}"
    return ThordataClient(api_key=TEST_USER, proxy_host=proxy_host)

def test_client_initialization(client):
    """测试客户端初始化时，代理URL和Session是否正确构建"""

    # 预期的代理 URL 格式
    expected_url = f"http://{TEST_USER}:@{client.proxy_host}" 

    # 断言：检查 client 实例中的属性是否符合预期
    assert client.proxy_url == expected_url 
    
    # 检查代理设置是否被正确注入到 Session 中
    expected_proxies = {
        "http": expected_url,
        "https": expected_url,
    }
    assert client.session.proxies == expected_proxies 
    print("\n✅ Test: Sync initialization successful.")

def test_successful_request(client):
    """测试客户端发送成功请求 (状态码 200)"""
    mock_url = "http://example.com/test"
    mock_response_data = {"status": "ok", "proxy_check": True}

    with requests_mock.Mocker() as m:
        m.get(mock_url, status_code=200, json=mock_response_data)
        
        response = client.get(mock_url)
        
        assert response.status_code == 200
        assert response.json() == mock_response_data
        print("\n✅ Test: Successful request handled correctly.")


def test_http_error_handling(client):
    """测试客户端处理 HTTP 错误 (如 403 Forbidden)"""
    error_url = "http://example.com/error"

    with requests_mock.Mocker() as m:
        m.get(error_url, status_code=403, text="Forbidden by Firewall")

        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            client.get(error_url)

        # 🌟 修复点 4：使用更宽松和健壮的断言，只检查状态码和 Client Error 文本
        # 避免因 requests 库版本或 mock 的细微差异导致断言失败
        assert '403' in str(excinfo.value)
        assert 'Client Error' in str(excinfo.value)
        print("\n✅ Test: HTTP error handling successful.")