#!/usr/bin/env python3
"""
Import TMX test - converted from import.yml
Fixed file upload handling.
"""
import os
import pytest
import time

from utils import get_tag_id, get_institution_id_from_token


@pytest.mark.integration
@pytest.mark.slow
def test_import_tmx(api_client, auth_token):
    """Test importing a TMX file."""
    script_path = os.path.dirname(os.path.realpath(__file__))
    data_path = os.path.join(script_path, "..", "..", "data", "un_short.tmx.import")

    if not os.path.exists(data_path):
        pytest.skip(f"Test file not found: {data_path}")
    
    # Step 1: Create a tag first (required before import)
    institution_id = get_institution_id_from_token(auth_token)
    
    tag_name = f"test_import_{int(time.time())}"
    tag_data = {
        "name": tag_name,
        "type": "public",
        "tv_domain": "test-domain",
        "lang_pair": "en_es"  # Based on the test file
    }
    if institution_id:
        tag_data["institution_id"] = institution_id
    
    tag_response = api_client.post("/api/v1/tags", json=tag_data)
    assert tag_response.status_code == 200, f"Failed to create tag: {tag_response.status_code} - {tag_response.text[:200]}"
    tag_result = tag_response.json()

    tag_id = get_tag_id(tag_result)
    
    assert tag_id is not None, f"Failed to get tag_id from created tag. Response: {tag_result}"
    
    # Step 2: Import TMX file using the tag ID
    import io
    with open(data_path, 'rb') as f:
        file_content = f.read()
    
    file_obj = io.BytesIO(file_content)
    upload_filename = "un_short.tmx"
    files = {'file': (upload_filename, file_obj, 'application/xml')}
    headers = {k: v for k, v in api_client.headers.items() if k.lower() != 'content-type'}
    data = {'tag': [tag_id]}

    _orig_ct = api_client.headers.pop("Content-Type", None)
    try:
        response = api_client.put(
            "/api/v1/tm/import",
            data=data,
            files=files,
            headers=headers,
        )
    finally:
        if _orig_ct is not None:
            api_client.headers["Content-Type"] = _orig_ct

    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text[:200]}"
    assert response.headers.get('content-type', '').startswith('application/json'), \
        "Response should be JSON"
    
    import_data = response.json()
    assert 'job_id' in import_data, "Response should contain 'job_id' key"
    assert import_data['job_id'], "Job ID should not be empty"

    try:
        api_client.delete(f"/api/v1/tags/{tag_id}")
    except:
        pass  # Ignore cleanup errors

