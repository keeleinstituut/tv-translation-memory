#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for test suite.
"""
import os
import sys
import pytest
import requests

# Add src to path for imports
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from RestClient.RestClient import RestClient
from client import TestClient

try:
    from test_auth_helper import generate_admin_token, generate_user_token
    USE_KEYCLOAK_AUTH = os.environ.get('REALM_PUBLIC_KEY_RETRIEVAL_MODE') == 'config'
except ImportError:
    USE_KEYCLOAK_AUTH = False
    generate_admin_token = None
    generate_user_token = None


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    config.addinivalue_line(
        "markers", "integration: Integration tests that require API server"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "rest: REST API tests"
    )


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API from environment variables."""
    host = os.environ.get('TEST_HOST', 'http://localhost')
    port = int(os.environ.get('TEST_PORT', '8000'))
    return f"{host}:{port}"


@pytest.fixture(scope="session")
def api_base_path():
    """Base API path."""
    return "/api/v1"


@pytest.fixture(scope="function")
def auth_token(api_base_url, api_base_path):
    """
    Get JWT token via authentication.
    Supports both Keycloak config mode and legacy username/password.
    """
    if USE_KEYCLOAK_AUTH and generate_admin_token:
        # Use Keycloak config mode - generate token directly
        return generate_admin_token(sub='admin-user')

    pytest.skip("Legacy /auth endpoint removed; configure Keycloak auth to run tests.")


@pytest.fixture(scope="function")
def user_auth_token(api_base_url, api_base_path):
    """
    Get JWT token for a regular user.
    Supports both Keycloak config mode and legacy username/password.
    """
    if USE_KEYCLOAK_AUTH and generate_user_token:
        # Use Keycloak config mode - generate token directly
        return generate_user_token(sub='test-user')

    pytest.skip("Legacy /auth endpoint removed; configure Keycloak auth to run tests.")


@pytest.fixture(scope="function")
def api_client(api_base_url, api_base_path, auth_token):
    """
    Configured requests.Session with authentication headers.
    Automatically handles relative URLs by prepending base URL.
    """
    session = requests.Session()
    session.base_url = api_base_url
    session.base_path = api_base_path
    
    # Set default headers
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })

    def build_url(path):
        """Build full URL from API path."""
        if path.startswith('http://') or path.startswith('https://'):
            return path
        if path.startswith('/'):
            return f"{api_base_url}{path}"
        return f"{api_base_url}{api_base_path}/{path.lstrip('/')}"

    original_request = session.request
    
    def request_with_base_url(method, url, *args, **kwargs):
        """Wrapper to automatically prepend base URL for relative paths."""
        if not (url.startswith('http://') or url.startswith('https://')):
            url = build_url(url)
        return original_request(method, url, *args, **kwargs)
    
    session.request = request_with_base_url
    session.get = lambda url, *args, **kwargs: request_with_base_url('GET', url, *args, **kwargs)
    session.post = lambda url, *args, **kwargs: request_with_base_url('POST', url, *args, **kwargs)
    session.put = lambda url, *args, **kwargs: request_with_base_url('PUT', url, *args, **kwargs)
    session.delete = lambda url, *args, **kwargs: request_with_base_url('DELETE', url, *args, **kwargs)
    session.patch = lambda url, *args, **kwargs: request_with_base_url('PATCH', url, *args, **kwargs)
    session.build_url = build_url
    
    yield session
    
    # Cleanup
    session.close()


@pytest.fixture(scope="function")
def user_api_client(api_base_url, api_base_path, user_auth_token):
    """
    Configured requests.Session for regular user with authentication headers.
    Automatically handles relative URLs by prepending base URL.
    """
    session = requests.Session()
    session.base_url = api_base_url
    session.base_path = api_base_path

    session.headers.update({
        "Authorization": f"Bearer {user_auth_token}",
        "Content-Type": "application/json"
    })

    def build_url(path):
        """Build full URL from API path."""
        if path.startswith('http://') or path.startswith('https://'):
            return path
        if path.startswith('/'):
            return f"{api_base_url}{path}"
        return f"{api_base_url}{api_base_path}/{path.lstrip('/')}"

    original_request = session.request
    
    def request_with_base_url(method, url, *args, **kwargs):
        """Wrapper to automatically prepend base URL for relative paths."""
        if not (url.startswith('http://') or url.startswith('https://')):
            url = build_url(url)
        return original_request(method, url, *args, **kwargs)
    
    session.request = request_with_base_url
    session.get = lambda url, *args, **kwargs: request_with_base_url('GET', url, *args, **kwargs)
    session.post = lambda url, *args, **kwargs: request_with_base_url('POST', url, *args, **kwargs)
    session.put = lambda url, *args, **kwargs: request_with_base_url('PUT', url, *args, **kwargs)
    session.delete = lambda url, *args, **kwargs: request_with_base_url('DELETE', url, *args, **kwargs)
    session.patch = lambda url, *args, **kwargs: request_with_base_url('PATCH', url, *args, **kwargs)
    session.build_url = build_url
    
    yield session

    session.close()


@pytest.fixture(scope="class")
def test_client():
    """Set up test client with authentication."""
    host = os.environ.get('TEST_HOST', 'http://localhost')
    port = int(os.environ.get('TEST_PORT', '8000'))

    client = TestClient()
    if USE_KEYCLOAK_AUTH and generate_admin_token:
        token = generate_admin_token(sub='admin-user')
        client.CLIENT.token = token
        client.CLIENT.host = host
        client.CLIENT.port = port
        client.CLIENT.set_url(host, port, '1')
    else:
        pytest.skip("Legacy /auth endpoint removed; configure Keycloak auth to run tests.")

    return client

