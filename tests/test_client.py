import requests
import requests_mock
import pytest
from thordata.client import ThordataClient

# Mock Credentials
TEST_SCRAPER = "mock_scraper_token"
TEST_PUB_TOKEN = "mock_public_token"
TEST_PUB_KEY = "mock_public_key"
TEST_HOST = "gate.thordata.com" 
TEST_PORT = 22225

@pytest.fixture
def client():
    """Fixture to create a ThordataClient instance."""
    return ThordataClient(
        scraper_token=TEST_SCRAPER, 
        public_token=TEST_PUB_TOKEN, 
        public_key=TEST_PUB_KEY,
        proxy_host=TEST_HOST,
        proxy_port=TEST_PORT
    )

def test_client_initialization(client):
    """Test client initialization and proxy URL construction."""
    expected_url = f"http://{TEST_SCRAPER}:@{TEST_HOST}:{TEST_PORT}" 
    
    # Verify proxy configuration in session
    assert client.session.proxies["http"] == expected_url
    assert client.session.proxies["https"] == expected_url

def test_successful_request(client):
    """Test a successful proxy request (200 OK)."""
    mock_url = "http://example.com/test"
    mock_data = {"status": "ok"}

    with requests_mock.Mocker() as m:
        m.get(mock_url, status_code=200, json=mock_data)
        
        response = client.get(mock_url)
        
        assert response.status_code == 200
        assert response.json() == mock_data

def test_http_error_handling(client):
    """Test handling of HTTP errors (e.g., 403 Forbidden)."""
    error_url = "http://example.com/error"
    
    with requests_mock.Mocker() as m:
        m.get(error_url, status_code=403)
        
        response = client.get(error_url)
        assert response.status_code == 403