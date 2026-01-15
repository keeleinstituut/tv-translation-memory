#!/usr/bin/env python3
import pytest

from TMDbApi.TMUtils import TMUtils


@pytest.mark.unit
def test_detect_lang_returns_expected_lang_for_english():
    text = (
        "This is a simple English sentence. "
        "Language identification should recognize it."
    )
    lang, prob = TMUtils.detect_lang(text, ["en", "es"])

    assert lang == "en"
    assert 0.0 <= prob <= 1.0


@pytest.mark.unit
def test_detect_lang_respects_language_restriction():
    text = (
        "Este es un texto en español. "
        "La detección debe identificarlo."
    )
    lang, prob = TMUtils.detect_lang(text, ["en", "es"])
    assert lang == "es"
    assert 0.0 <= prob <= 1.0

    # When restricted to English only, the classifier must return English.
    restricted_lang, restricted_prob = TMUtils.detect_lang(text, ["en"])
    assert restricted_lang == "en"
    assert 0.0 <= restricted_prob <= 1.0

