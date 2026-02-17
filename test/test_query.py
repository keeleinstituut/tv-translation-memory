import os
import sys
import time
import uuid
import pytest

# Append to python path
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from RestClient.RestClient import RestClient
from utils import get_tag_id, get_institution_id_from_token

try:
    from test_auth_helper import generate_user_token
    USE_KEYCLOAK_AUTH = os.environ.get('REALM_PUBLIC_KEY_RETRIEVAL_MODE') == 'config'
except ImportError:
    USE_KEYCLOAK_AUTH = False
    generate_user_token = None


@pytest.fixture(scope="function")
def test_tags(test_client):
    """Set up test tags and clean up after test."""
    test_id = str(uuid.uuid4())[:8]
    tag_public1_name = f"tag_public1_{test_id}"
    tag_public2_name = f"tag_public2_{test_id}"

    _cleanup_tags(test_client, [tag_public1_name, tag_public2_name])
    
    tag1 = test_client.create_tag(
        name=tag_public1_name, 
        type="public", 
        lang_pair="en_sv",
        tv_domain=str(uuid.uuid4()),
        institution_id=get_institution_id_from_token(test_client.CLIENT.token)
    )
    tag_public1_id = get_tag_id(tag1)
    
    yield {
        'tag_public1_id': tag_public1_id,
        'tag_public1_name': tag_public1_name,
        'tag_public2_name': tag_public2_name
    }

    try:
        if tag_public1_id:
            test_client.delete_tm("en", "sv", duplicates_only=False, filters={"tag": tag_public1_id})
        time.sleep(1)
    except:
        pass
    
    try:
        if tag_public1_id:
            test_client.delete_tag(tag_public1_id)
        _cleanup_tags(test_client, [tag_public1_name, tag_public2_name])
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
                        # Clean up TUs first
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
        test_client.delete_tm("en", "sv", duplicates_only=False, filters={"tag": tag_id})
        time.sleep(1)
        for lang_pair in ["sv_en", "en_de", "de_en"]:
            try:
                test_client.delete_tm(lang_pair.split("_")[0], lang_pair.split("_")[1], duplicates_only=False, filters={"tag": tag_id})
            except:
                pass
        time.sleep(1)
    except:
        pass


def _assert_query(test_client, stext, ttext, tags=None, concordance=False, expected_results=1, expected_tags=None, exact_match=False, verify_exact_text=False):
    """Helper function to assert query results."""
    tag_id = tags
    expected_tag_ids = []
    if tags and isinstance(tags, list):
        tag_id = tags[0] if tags else None
        expected_tag_ids = tags
    elif tags and isinstance(tags, str):
        try:
            uuid.UUID(tags)
            tag_id = tags
            expected_tag_ids = [tags]
        except ValueError:
            all_tags = test_client.get_tag(None)
            if "tags" in all_tags:
                for t in all_tags["tags"]:
                    if t.get("name") == tags:
                        tag_id = t.get("id")
                        expected_tag_ids = [tag_id]
                        break
    
    res = test_client.query(query=stext, slang="en", tlang="sv", tag=tag_id, concordance=concordance)

    if expected_tag_ids and res.get("results"):
        filtered_results = []
        for result in res["results"]:
            result_tags = result.get("tag", [])
            if isinstance(result_tags, str):
                result_tags = [result_tags]
            if any(tag in result_tags for tag in expected_tag_ids):
                filtered_results.append(result)
        res["results"] = filtered_results
    
    actual_count = len(res["results"])

    if verify_exact_text and ttext:
        matching_results = [r for r in res["results"] if r.get("tu", {}).get("target_text") == ttext]
        assert len(matching_results) >= expected_results, \
            f"Expected at least {expected_results} results with target text '{ttext}' but got {len(matching_results)}. Query: '{stext}', Tag: {tag_id}"
        res["results"] = matching_results
        actual_count = len(matching_results)
    
    assert actual_count >= expected_results, \
        f"Expected at least {expected_results} results but got {actual_count}. Query: '{stext}', Tag: {tag_id}"
    if exact_match:
        assert actual_count == expected_results, \
            f"Expected exactly {expected_results} results but got {actual_count}. Query: '{stext}', Tag: {tag_id}"
    
    if expected_results > 0 and actual_count > 0:
        matching_result = None
        for result in res["results"]:
            if ttext and result.get("tu", {}).get("target_text") == ttext:
                matching_result = result
                break
        if not matching_result and res["results"] and not verify_exact_text:
            matching_result = res["results"][0]
        
        if matching_result:
            if ttext:
                assert matching_result["tu"]["target_text"] == ttext, \
                    f"Expected target text '{ttext}' but got '{matching_result['tu']['target_text']}'"
            if expected_tags:
                result_tags = matching_result.get("tag", [])
                if isinstance(result_tags, str):
                    result_tags = [result_tags]
                assert set(result_tags) == set(expected_tags), \
                    f"Expected tags {expected_tags} but got {result_tags}"


@pytest.mark.integration
class TestQuery:
    """Query API tests converted from unittest to pytest."""
    
    def test_query(self, test_client, test_tags):
        """Test query functionality with multiple tags."""
        test_id = str(uuid.uuid4())[:8]
        texts = [
            (f"This is my purple car {test_id}", f"Detta är min lila bil {test_id}"),
            (f"This is my red car {test_id}", f"Det här är min röda bil {test_id}"),
            (f"This is my yellow car {test_id}", f"Det här är min gula bil {test_id}"),
        ]
        
        tag_public1_id = test_tags['tag_public1_id']
        tag_public2_name = test_tags['tag_public2_name']

        tag2 = test_client.create_tag(
            name=tag_public2_name,
            lang_pair="en_sv",
            type="public",
            tv_domain=str(uuid.uuid4()),
            institution_id=get_institution_id_from_token(test_client.CLIENT.token)
        )
        tag_public2_id = get_tag_id(tag2)
        
        if not tag_public1_id or not tag_public2_id:
            pytest.fail("Failed to get tag IDs")

        # _cleanup_translation_units(test_client, tag_public1_id)
        # _cleanup_translation_units(test_client, tag_public2_id)
        
        test_client.CLIENT.add_tu(texts[0][0], texts[0][1], "en", "sv", tag_public1_id)
        test_client.CLIENT.add_tu(texts[1][0], texts[1][1], "en", "sv", tag_public2_id)
        time.sleep(3)

        test_client.query(query=texts[0][0], slang="en", tlang="sv")
        test_client.query(query=texts[0][0], slang="en", tlang="sv", tag=tag_public1_id)

        _assert_query(test_client, texts[0][0], texts[0][1], expected_results=1, tags=tag_public1_id, verify_exact_text=True)
        _assert_query(test_client, texts[1][0], texts[1][1], expected_results=1, tags=tag_public2_id, verify_exact_text=True)
        _assert_query(test_client, texts[0][0], texts[1][1], expected_results=1, tags=tag_public2_id, concordance=True)
        _assert_query(test_client, texts[1][0], texts[0][1], expected_results=1, tags=tag_public1_id, concordance=True)
        _assert_query(test_client, texts[2][0], None, expected_results=2, concordance=True, tags=[tag_public1_id, tag_public2_id])
        _assert_query(test_client, texts[2][0], None, expected_results=1, concordance=True, tags=tag_public1_id)

        try:
            test_client.delete_tm("en", "sv", duplicates_only=False, filters={"tag": tag_public2_id})
            time.sleep(1)
            test_client.delete_tag(tag_public2_id)
        except:
            pass

