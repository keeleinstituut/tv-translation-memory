#!/usr/bin/env python3
"""
Query API tests - converted from query.yml and query_basic.yml
"""
import time
import pytest

from utils import get_tag_id, get_institution_id_from_token


def _get_nested_value(data, path):
    """Helper to get nested value from dict using dot notation (simple JSONPath)."""
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and key.isdigit():
            value = value[int(key)]
        else:
            return None
        if value is None:
            return None
    return value


@pytest.mark.integration
def test_query(api_client):
    """Test basic query endpoint."""
    params = {
        'slang': 'en',
        'tlang': 'es',
        'q': 'United Nations'
    }
    response = api_client.get("/api/v1/tm", params=params)
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    assert response.headers.get('content-type', '').startswith('application/json'), \
        "Response should be JSON"
    
    data = response.json()
    assert 'results' in data, "Response should contain 'results' key"
    assert isinstance(data['results'], list), "Results should be a list"


@pytest.mark.integration
def test_query_basic(api_client, auth_token):
    """Test basic query with expected translation."""
    # Create tag and add test data so the query has deterministic results.
    institution_id = get_institution_id_from_token(auth_token)

    tag_name = f"test_query_basic_{int(time.time())}"
    tag_data = {
        "name": tag_name,
        "type": "public",
        "tv_domain": "test-domain",
        "lang_pair": "en_es",
    }
    if institution_id:
        tag_data["institution_id"] = institution_id

    tag_response = api_client.post("/api/v1/tags", json=tag_data)
    assert tag_response.status_code == 200, \
        f"Failed to create tag: {tag_response.status_code} - {tag_response.text[:200]}"
    tag_result = tag_response.json()

    tag_id = get_tag_id(tag_result)
    assert tag_id, f"Failed to get tag_id from created tag. Response: {tag_result}"

    source_text = f"Test query basic {int(time.time())}"
    target_text = "Prueba de consulta básica"
    add_response = api_client.post(
        "/api/v1/tm",
        json={
            "stext": source_text,
            "ttext": target_text,
            "slang": "en",
            "tlang": "es",
            "tag": [tag_id],
        },
    )
    assert add_response.status_code == 200, \
        f"Expected status 200, got {add_response.status_code}: {add_response.text[:200]}"
    try:
        params = {
            'slang': 'en',
            'tlang': 'es',
            'q': source_text,
            'tag': tag_id,
        }
        max_wait = 180
        wait_interval = 3
        elapsed = 0
        data = None
        while elapsed < max_wait:
            time.sleep(wait_interval)
            elapsed += wait_interval
            response = api_client.get("/api/v1/tm", params=params)
            assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
            assert response.headers.get('content-type', '').startswith('application/json'), \
                "Response should be JSON"
            data = response.json()
            if data.get('results'):
                break

        assert data is not None and data.get('results'), \
            f"Expected imported data to be queryable after {elapsed}s"

        first_result = data['results'][0]
        assert 'tu' in first_result, "Result should contain 'tu' key"
        assert 'target_text' in first_result['tu'], "Translation unit should contain 'target_text'"
        assert first_result['tu']['target_text'], "Translation unit should have target_text"
        assert target_text in first_result['tu']['target_text'], "Translation unit should match expected target"
    finally:
        try:
            api_client.delete(f"/api/v1/tags/{tag_id}")
        except Exception:
            pass

