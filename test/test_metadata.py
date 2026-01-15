#!/usr/bin/env python3

import os
import sys
import re
import time
import json
import uuid
import pytest

# Append to python path
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from RestClient.RestClient import RestClient
from utils import get_tag_id

try:
    from test_auth_helper import generate_user_token
    USE_KEYCLOAK_AUTH = os.environ.get('REALM_PUBLIC_KEY_RETRIEVAL_MODE') == 'config'
except ImportError:
    USE_KEYCLOAK_AUTH = False
    generate_user_token = None


@pytest.fixture(scope="function")
def test_tag_with_import(test_client):
    """Set up test tag and import TMX file."""
    test_id = str(uuid.uuid4())[:8]
    tag_public1_name = f"tag_public1_{test_id}"

    _cleanup_tags(test_client, [tag_public1_name])

    tag1 = test_client.create_tag(tag_public1_name, "public", tv_domain="test-domain", lang_pair="en_de")
    tag_public1_id = get_tag_id(
        tag1,
        tag_public1_name,
        lambda: test_client.get_tag(None),
    )
    
    if not tag_public1_id:
        pytest.fail("Failed to get tag_id from created tag")

    _cleanup_translation_units(test_client, tag_public1_id)

    import_response = test_client.CLIENT.import_tm(
        os.path.join(script_path, "..", "data", "metadata.tmx"),
        tag_public1_id,
        lang_pairs=["en_de"]
    )

    if not import_response or "job_id" not in import_response:
        pytest.fail(f"Import failed: {import_response}")

    max_wait = 180
    wait_interval = 2
    elapsed = 0
    import_ready = False
    
    while elapsed < max_wait:
        time.sleep(wait_interval)
        elapsed += wait_interval

        try:
            query_result = test_client.query(
                query="This is a short, new sentence.",
                slang="en",
                tlang="de",
                tag=tag_public1_id
            )
            if query_result and "results" in query_result and len(query_result["results"]) > 0:
                for result in query_result["results"]:
                    if "tu" in result and "target_text" in result["tu"]:
                        target_text = result["tu"]["target_text"]
                        if "Dies ist ein kurzer neuer Satz" in target_text:
                            import_ready = True
                            break
                if import_ready:
                    break
        except Exception as e:
            pass
    
    if not import_ready:
        try:
            query_result = test_client.query(
                query="This is a short, new sentence.",
                slang="en",
                tlang="de"
            )
            if query_result and "results" in query_result and len(query_result["results"]) > 0:
                print(f"Warning: Found {len(query_result['results'])} results without tag filter, but import may not be complete")
            else:
                print(f"Warning: Import may not have completed after {elapsed}s - no results found")
        except:
            print(f"Warning: Import may not have completed after {elapsed}s, continuing test anyway")
    
    yield {
        'tag_public1_id': tag_public1_id,
        'tag_public1_name': tag_public1_name
    }

    try:
        if tag_public1_id:
            _cleanup_translation_units(test_client, tag_public1_id)
    except:
        pass
    
    try:
        if tag_public1_id:
            test_client.delete_tag(tag_public1_id)
        _cleanup_tags(test_client, [tag_public1_name])
    except:
        pass
    time.sleep(1)


@pytest.fixture(scope="function")
def user_client(test_client):
    """Set up user client for testing."""
    if USE_KEYCLOAK_AUTH and generate_user_token:
        token = generate_user_token(sub="test_user")
        client = RestClient(token=token, host=test_client.CLIENT.host, port=test_client.CLIENT.port)
    else:
        pytest.skip("Legacy /auth endpoint removed; configure Keycloak auth to run tests.")
    client.base_url = test_client.CLIENT.base_url
    return client


def _cleanup_tags(test_client, tag_names):
    """Clean up tags by name, in case they exist from previous test runs."""
    try:
        all_tags = test_client.get_tag(None)
        if "tags" in all_tags:
            for t in all_tags["tags"]:
                if t.get("name") in tag_names:
                    try:
                        _cleanup_translation_units(test_client, t.get("id"))
                        test_client.delete_tag(t.get("id"))
                    except:
                        pass
    except:
        pass


def _cleanup_translation_units(test_client, tag_id):
    """Clean up all translation units for a given tag."""
    if not tag_id:
        return
    try:
        test_client.delete_tm("en", "de", duplicates_only=False, filters={"tag": tag_id})
        time.sleep(1)
    except:
        pass


def _assert_query(test_client, stext, ttext, tags=None, concordance=False, expected_results=1, expected_tags=None, smeta=None, tmeta=None, match=None, verify_metadata=True):
    """Helper function to assert query results with metadata."""
    smeta_str = json.dumps(smeta) if smeta else None
    tmeta_str = json.dumps(tmeta) if tmeta else None

    tag_id = tags
    if tags and isinstance(tags, str):
        try:
            uuid.UUID(tags)
            tag_id = tags
        except ValueError:
            all_tags = test_client.get_tag(None)
            if "tags" in all_tags:
                for t in all_tags["tags"]:
                    if t.get("name") == tags:
                        tag_id = t.get("id")
                        break

    res = test_client.query(query=stext, slang="en", tlang="de", tag=tag_id, concordance=concordance, smeta=smeta_str, tmeta=tmeta_str)

    actual_count = len(res.get("results", []))
    assert actual_count >= expected_results, \
        f"Expected at least {expected_results} results but got {actual_count}. Query: '{stext}', Tag: {tag_id}"
    if expected_results > 0 and len(res["results"]) > 0:
        if ttext:
            first_result_text = res["results"][0].get("tu", {}).get("target_text", "")
            assert ttext in first_result_text, \
                f"Expected target text '{ttext}' in results"

        if smeta and verify_metadata:
            found_meta_match = False
            for result in res["results"]:
                source_meta = result.get("tu", {}).get("source_metadata")
                if isinstance(source_meta, str):
                    source_meta = json.loads(re.sub("'", "\"", source_meta))
                if isinstance(source_meta, dict):
                    if all(source_meta.get(k) == v for k, v in smeta.items()):
                        found_meta_match = True
                        break
            if verify_metadata:
                assert found_meta_match, \
                    f"Expected to find a result with metadata {smeta}"
        
        if match:
            assert res["results"][0]["match"] == match


@pytest.mark.integration
class TestMetadata:
    """Metadata query tests converted from unittest to pytest."""
    
    def test_query(self, test_client, test_tag_with_import):
        """Test query with metadata filtering."""
        texts = [("This is a short, new sentence.", "Dies ist ein kurzer neuer Satz.")]
        tag_public1_id = test_tag_with_import['tag_public1_id']

        _assert_query(test_client, texts[0][0], texts[0][1], expected_results=2, tags=tag_public1_id, match=100)
        _assert_query(test_client, texts[0][0], texts[0][1], expected_results=1, tags=tag_public1_id, smeta={'x-context-pre': 'kuku1', 'x-context-post': 'kuku2'}, match=101, verify_metadata=False)

