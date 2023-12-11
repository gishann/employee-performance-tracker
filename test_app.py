import pytest
import requests_mock
from app2 import github_api_request

@pytest.fixture(scope="session")
def github_mock():
    # Create a requests_mock object to mock GitHub API responses
    with requests_mock.mock() as m:
        # Mock the GitHub API endpoint used in your app
        m.get('https://api.github.com/repos/bistecglobal/blockchain-certificates-issuer/contributors', json=[{'login': 'testuser'}])
        yield m

def test_github_api_status(github_mock):
    # Use the mocked GitHub API in your test
    with github_mock:
        # Call the GitHub API through your app's function
        response = github_api_request('repos/bistecglobal/blockchain-certificates-issuer/contributors')

        # Assert that the response is successful (HTTP status code 2xx)
        assert response.ok, f"GitHub API request failed with status code {response.status_code}"

        # Additional assertions based on your app's behavior
        if response.ok:
            assert len(response.json()) == 1
            assert response.json()[0]['login'] == 'testuser'
