#!/usr/bin/env python3
import os
import sys

import pytest

script_path = os.path.dirname(os.path.realpath(__file__))
repo_root = os.path.abspath(os.path.join(script_path, ".."))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, repo_root)
sys.path.insert(0, script_path)
sys.path.insert(0, ".")

try:
    import pyter  # noqa: F401
except ModuleNotFoundError:
    from tools import pyter as tools_pyter

    sys.modules["pyter"] = tools_pyter

from TM_TestSet.TMMatching import TMMatching


@pytest.mark.unit
def test_ter_score_returns_zero_for_identical_text():
    matcher = TMMatching("hello world", "en", "es", "Automotive", 0.5)

    score = matcher.ter_score("hello world", "hello world")

    assert score == 0.0


@pytest.mark.unit
def test_adjust_match_penalizes_domain_mismatch():
    matcher = TMMatching("hello world", "en", "es", "Automotive", 0.5)
    segment = {"domain": ["Medical"]}

    adjusted = matcher._adjust_match(segment, {"domain": ["Automotive"]}, 0.2)

    assert adjusted == 75.0


@pytest.mark.unit
def test_cen_p_match_returns_match_for_perfect_hit():
    matcher = TMMatching("hello world", "en", "es", "Automotive", 0.5)
    segment = {
        "source_text": "hello world",
        "target_text": "hola mundo",
        "domain": ["Automotive"],
    }
    l_best_segments = [(segment, 100)]

    result = matcher._cen_p_match(l_best_segments)

    assert result["tm_src"] == "hello world"
    assert result["tm_tgt"] == "hola mundo"
    assert result["match"] == 100.0


@pytest.mark.unit
def test_execute_uses_fuzzy_match_when_no_perfect_match(monkeypatch):
    matcher = TMMatching("hello world", "en", "es", "Automotive", 0.5)
    l_best_segments = [
        ({"source_text": "hello there", "target_text": "hola", "domain": ["Automotive"]}, 80)
    ]
    expected = {"tm_src": "hello there", "tm_tgt": "hola", "match": 80}

    monkeypatch.setattr(matcher, "query", lambda: l_best_segments)
    monkeypatch.setattr(matcher, "fuzzy_match", lambda segments: expected)

    matcher.execute()

    assert matcher.dic_match == expected

