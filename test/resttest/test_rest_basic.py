#!/usr/bin/env python3
"""
Basic API tests - converted from basic.yml
"""
import pytest


@pytest.mark.integration
def test_get_stats(api_client):
    """Test getting stats from the API."""
    response = api_client.get("/api/v1/tm/stats")
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    assert response.headers.get('content-type', '').startswith('application/json'), \
        "Response should be JSON"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"

