#!/usr/bin/env python3
"""
Export TMX test - converted from export.yml
"""
import io
import time
import zipfile
import pytest

from utils import get_tag_id, get_institution_id_from_token


@pytest.mark.integration
@pytest.mark.slow
def test_export_tmx(api_client, auth_token):
    """Test exporting a TMX file."""
    slang, tlang = "en", "es"

    institution_id = get_institution_id_from_token(auth_token)

    tag_name = f"test_export_{int(time.time())}"
    tag_data = {
        "name": tag_name,
        "type": "public",
        "tv_domain": "test-domain",
        "lang_pair": f"{slang}_{tlang}",
    }
    if institution_id:
        tag_data["institution_id"] = institution_id

    tag_response = api_client.post("/api/v1/tags", json=tag_data)
    assert tag_response.status_code == 200, \
        f"Failed to create tag: {tag_response.status_code} - {tag_response.text[:200]}"
    tag_result = tag_response.json()

    def _list_tags():
        tags_response = api_client.get("/api/v1/tags")
        if tags_response.status_code == 200:
            return tags_response.json()
        return {}

    tag_id = get_tag_id(tag_result, tag_name, _list_tags)
    assert tag_id, f"Failed to get tag_id from created tag. Response: {tag_result}"

    # Add one translation unit so the language pair exists for export.
    source_text = f"Test export {int(time.time())}"
    target_text = "Prueba de exportación"
    add_response = api_client.post(
        "/api/v1/tm",
        json={
            "stext": source_text,
            "ttext": target_text,
            "slang": slang,
            "tlang": tlang,
            "tag": [tag_id],
        },
    )
    assert add_response.status_code == 200, \
        f"Expected status 200, got {add_response.status_code}: {add_response.text[:200]}"

    # Export expects JSON body (RequestParser reads JSON by default).
    payload = {
        "slang": slang,
        "tlang": tlang,
        "tag": [tag_id],
    }
    response = api_client.post("/api/v1/tm/export", json=payload)
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}: {response.text[:200]}"
    assert response.headers.get("content-type", "").startswith("application/json"), \
        "Response should be JSON"
    data = response.json()
    assert "job_id" in data and data["job_id"], "Response should contain non-empty 'job_id'"
    job_id = data["job_id"]

    # Wait for export file to be ready and verify it can be downloaded.
    max_wait = 180
    wait_interval = 3
    elapsed = 0
    download_response = None
    while elapsed < max_wait:
        time.sleep(wait_interval)
        elapsed += wait_interval
        download_response = api_client.get(f"/api/v1/tm/export/file/{job_id}")
        if download_response.status_code == 200:
            break

    assert download_response is not None and download_response.status_code == 200, \
        f"Export file not ready after {elapsed}s (status {getattr(download_response, 'status_code', 'n/a')})"
    assert download_response.headers.get("content-type", "").startswith("application/zip"), \
        "Export download should be a zip file"

    # Validate zip contains a TMX file (tag name is used as filename).
    with zipfile.ZipFile(io.BytesIO(download_response.content)) as zf:
        tmx_files = [name for name in zf.namelist() if name.endswith(".tmx")]
        assert tmx_files, "Export zip should contain at least one TMX file"
        assert f"{tag_name}.tmx" in tmx_files, \
            f"Expected TMX file named {tag_name}.tmx, got {tmx_files}"
        tmx_bytes = zf.read(f"{tag_name}.tmx")
        assert b"<tmx" in tmx_bytes, "TMX file should contain TMX header"

    try:
        api_client.delete(f"/api/v1/tm/export/file/{job_id}")
    except Exception:
        pass

    try:
        api_client.delete(f"/api/v1/tags/{tag_id}")
    except Exception:
        pass

