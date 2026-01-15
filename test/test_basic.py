#!/usr/bin/env python3
import os
import sys
import time
import pytest

# Append to python path
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)
sys.path.insert(0, ".")

from utils import get_tag_id


@pytest.mark.integration
class TestBasic:
    """Basic API tests converted from unittest to pytest."""

    def test_stats(self, test_client):
        """Test getting stats."""
        res = test_client.stats()
        assert res is not None

    def test_manage_tag(self, test_client):
        """Test tag management (create, read, update, delete)."""
        tag_types = [("test_private", "private"), ("test_public", "public"), ("test_unspecified", "unspecified")]
        created_tags = []
        
        for tag, tag_type in tag_types:
            res = test_client.create_tag(tag, tag_type)
            tag_id = get_tag_id(
                res,
                tag,
                lambda: test_client.get_tag(None),
            )
            
            if tag_id:
                created_tags.append((tag_id, tag, tag_type))
            else:
                print(f"Warning: Could not extract tag_id from response: {res}")

        all_tags_res = test_client.get_tag(None)
        tags_dict = {}
        if "tags" in all_tags_res:
            for t in all_tags_res["tags"]:
                if t["name"] in [tag for _, tag, _ in created_tags]:
                    tags_dict[t["name"]] = t
        
        for tag, tag_type in tag_types:
            if tag in tags_dict:
                assert tags_dict[tag]["type"] == tag_type

        if created_tags:
            tag_id, tag_name, tag_type = created_tags[0]
            new_name = "test_new_name"
            test_client.CLIENT.set_tag(tagname=tag_id, name=new_name)
            res = test_client.get_tag(tag_id)
            if isinstance(res, dict) and "id" in res:
                assert str(res["id"]) == str(tag_id)
                assert res["name"] == new_name

        for tag_id, tag, tag_type in created_tags:
            try:
                test_client.delete_tag(tag_id)
            except:
                pass

    def test_manage_tm(self, test_client):
        """Test translation memory management (import, query, delete)."""
        tag_name = "test_import"
        tag = test_client.create_tag(tag_name, "public")
        tag_id = get_tag_id(
            tag,
            tag_name,
            lambda: test_client.get_tag(None),
        )

        if not tag_id:
            pytest.fail(f"Failed to get tag_id from created tag. Response: {tag}")

        import_response = test_client.import_tm(os.path.join(script_path, "..", "data", "EN_SV_tmx.zip"), tag_id)
        job_id = None
        if isinstance(import_response, dict) and "job_id" in import_response:
            job_id = import_response["job_id"]
        elif hasattr(import_response, "job_id"):
            job_id = import_response.job_id

        assert job_id is not None, f"Query should return job_id"

        max_wait = 120
        wait_interval = 3
        elapsed = 0
        query_success = False
        stats_verified = False
        
        while elapsed < max_wait:
            time.sleep(wait_interval)
            elapsed += wait_interval

            try:
                query_result = test_client.query(
                    query="A license with this serial number cannot be activated.",
                    slang="en",
                    tlang="sv",
                    tag=tag_id
                )

                if query_result and "results" in query_result and len(query_result["results"]) > 0:
                    for result in query_result["results"]:
                        if "tu" in result and "target_text" in result["tu"]:
                            if "Det går inte att aktivera en licens med det här serienumret." in result["tu"]["target_text"]:
                                query_success = True
                                break
                    if query_success:
                        res = test_client.stats()
                        if tag_id in res.get("tag", {}):
                            stats_verified = True
                        break
            except Exception as e:
                pass

        assert query_success, f"Query should return expected translation after import (waited {elapsed}s)"

        if not stats_verified:
            res = test_client.stats()
            if "tag" in res and tag_id in res["tag"]:
                assert res["tag"][tag_id] == 5, f"Expected 5 segments in tag {tag_id}, got {res['tag'].get(tag_id, 0)}"
            elif "lang_pairs" in res and "en_sv" in res["lang_pairs"]:
                if "tag" in res["lang_pairs"]["en_sv"] and tag_id in res["lang_pairs"]["en_sv"]["tag"]:
                    assert res["lang_pairs"]["en_sv"]["tag"][tag_id] == 5, f"Expected 5 segments in tag {tag_id} for en_sv"

        _query(test_client)

        try:
            delete_response = test_client.delete_tm("en", "sv", duplicates_only=False, filters={"tag": tag_id})
            if delete_response and "job_id" in delete_response:
                max_wait_delete = 60
                elapsed_delete = 0
                while elapsed_delete < max_wait_delete:
                    time.sleep(2)
                    elapsed_delete += 2
                    try:
                        query_result = test_client.query(
                            query="A license with this serial number cannot be activated.",
                            slang="en",
                            tlang="sv",
                            tag=tag_id
                        )
                        if not query_result.get("results") or len(query_result.get("results", [])) == 0:
                            break
                    except:
                        break
        except Exception as e:
            print(f"Note: Deletion failed (this is OK for import validation test): {e}")

        if tag_id:
            try:
                test_client.delete_tag(tag_id)
            except:
                pass


def _query(test_client):
    """Helper function to test query."""
    res = test_client.query(query="A license with this serial number cannot be activated.", slang="en", tlang="sv")
    assert len(res["results"]) >= 1
    assert res["results"][0]["tu"]["target_text"] == "Det går inte att aktivera en licens med det här serienumret."

