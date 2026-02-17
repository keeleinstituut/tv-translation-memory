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


@pytest.fixture
def sample_segment():
    """Create a sample TMTranslationUnit for testing."""
    from TMDbApi.TMTranslationUnit import TMTranslationUnit
    return TMTranslationUnit({
        "source_text": "Hello world",
        "source_language": "en-GB",
        "target_text": "Hola mundo",
        "target_language": "es-ES"
    })


@pytest.fixture
def sample_segment_with_tags():
    """Create a sample segment with XML tags."""
    from TMDbApi.TMTranslationUnit import TMTranslationUnit
    return TMTranslationUnit({
        "source_text": "Hello <b>world</b>",
        "source_language": "en-GB",
        "target_text": "Hola <i>mundo</i>",
        "target_language": "es-ES"
    })


@pytest.fixture
def sample_segment_with_metadata():
    """Create a sample segment with metadata."""
    from TMDbApi.TMTranslationUnit import TMTranslationUnit
    return TMTranslationUnit({
        "source_text": "Hello world",
        "source_language": "en-GB",
        "target_text": "Hola mundo",
        "target_language": "es-ES",
        "industry": ["Automotive Manufacturing"],
        "type": ["Instructions for Use"],
        "organization": ["Pangeanic"],
        "tm_creation_date": "20090914T114332Z",
        "tm_change_date": "20090914T114332Z",
        "tuid": "test-123",
        "username": "testuser"
    })


@pytest.fixture
def temp_tmx_file(tmp_path):
    """Create a temporary TMX file for testing."""
    def _create(content, filename="test.tmx"):
        tmx_file = tmp_path / filename
        tmx_file.write_text(content, encoding='utf-8')
        return str(tmx_file)
    return _create


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for file operations."""
    return tmp_path


def create_minimal_tmx(content=None):
    """Generate minimal valid TMX XML."""
    if content is None:
        content = """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z" changedate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>Hello world</seg>
</tuv>
<tuv xml:lang="es-ES">
<seg>Hola mundo</seg>
</tuv>
</tu>
</body>
</tmx>"""
    return content


def create_tmx_with_tags():
    """Generate TMX with XML tags in segments."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>Hello <b>world</b></seg>
</tuv>
<tuv xml:lang="es-ES">
<seg>Hola <i>mundo</i></seg>
</tuv>
</tu>
</body>
</tmx>"""


def create_tmx_with_metadata():
    """Generate TMX with metadata properties."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z" changedate="20090914T114332Z" tuid="test-123">
<prop type="tda-industry">Automotive Manufacturing</prop>
<prop type="tda-type">Instructions for Use</prop>
<prop type="tda-org">Pangeanic</prop>
<prop type="custom-prop">Custom Value</prop>
<tuv xml:lang="en-GB">
<prop type="tuv-prop">Source Metadata</prop>
<seg>Hello world</seg>
</tuv>
<tuv xml:lang="es-ES">
<prop type="tuv-prop">Target Metadata</prop>
<seg>Hola mundo</seg>
</tuv>
</tu>
</body>
</tmx>"""


@pytest.fixture(scope="session")
def nltk_data_available():
    """Check if NLTK data is available, skip tests if not."""
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('taggers/universal_tagset')
        return True
    except LookupError:
        return False


@pytest.fixture
def sample_texts():
    """Sample texts for testing in multiple languages."""
    return {
        'EN': "Hello world. This is a test. How are you?",
        'ES': "Hola mundo. Esta es una prueba. ¿Cómo estás?",
        'FR': "Bonjour le monde. Ceci est un test. Comment allez-vous?",
        'DE': "Hallo Welt. Das ist ein Test. Wie geht es dir?"
    }


@pytest.fixture
def sample_pos_tagged():
    """Sample POS tagged sentences for testing."""
    return [
        [('Hello', 'UH'), ('world', 'NN'), ('.', '.')],
        [('This', 'DT'), ('is', 'VBZ'), ('a', 'DT'), ('test', 'NN'), ('.', '.')]
    ]

