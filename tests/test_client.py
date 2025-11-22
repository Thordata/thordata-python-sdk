# test_client.py
import requests
import requests_mock
import pytest
from thordata_sdk.client import ThordataClient

# 定义测试用的认证信息
TEST_USER = "test_user_ai"
TEST_PASS = "test_pass_secure"
TEST_HOST = "gate.thordata.com"
TEST_PORT = 22225

# 定义一个 Fixture：这是 pytest 中的术语，用于提供可重用的测试资源
@pytest.fixture
def client():
    """创建一个 ThordataClient 实例，供所有测试函数使用"""
    return ThordataClient(auth_user=TEST_USER, auth_pass=TEST_PASS)

def test_client_initialization(client):
    """测试客户端初始化时，代理URL是否正确构建"""
    
    # 预期的代理 URL 格式
    expected_url = f"http://{TEST_USER}:{TEST_PASS}@{TEST_HOST}:{TEST_PORT}"
    
    # 断言：检查 client 实例中的属性是否符合预期
    assert client.proxy_url == expected_url
    assert client.proxies['http'] == expected_url
    assert client.proxies['https'] == expected_url
    print("\n✅ Test: Initialization successful.")

def test_successful_request(client):
    """测试客户端发送成功请求 (状态码 200)"""
    mock_url = "http://example.com/test"
    mock_response_data = {"status": "ok", "proxy_check": True}

    # requests_mock 用于拦截 mock_url 的请求，并返回预设的响应
    with requests_mock.Mocker() as m:
        m.get(mock_url, status_code=200, json=mock_response_data)
        
        # 实际调用客户端的 GET 方法
        response = client.get(mock_url)
        
        # 断言：检查响应的状态码和返回的内容
        assert response.status_code == 200
        assert response.json() == mock_response_data
        print("\n✅ Test: Successful request handled correctly.")


def test_http_error_handling(client):
    """测试客户端处理 HTTP 错误 (如 403 Forbidden)"""
    error_url = "http://example.com/error"

    with requests_mock.Mocker() as m:
        m.get(error_url, status_code=403, text="Forbidden by Firewall")
        
        # 使用 pytest.raises 检查是否抛出了 requests.exceptions.HTTPError 异常
        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            client.get(error_url)
        
        # 可以选择性地检查错误信息
        assert '403 Forbidden' in str(excinfo.value)
        print("\n✅ Test: HTTP error handling correct.")