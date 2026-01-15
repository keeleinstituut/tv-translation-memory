#!/usr/bin/env python3
import os
import sys

import pytest

# Append to python path
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)
sys.path.insert(0, ".")


def _require_model_files(language):
    from TMPosTagger.TMRDRPOSTagger import TMRDRPOSTagger, multilingual_posTagger_home

    model_rel = TMRDRPOSTagger.models.get(language)
    dict_rel = TMRDRPOSTagger.dicts.get(language)
    if not model_rel or not dict_rel:
        pytest.skip(f"No RDRPOSTagger model/dict configured for {language}")

    model_path = os.path.join(multilingual_posTagger_home, model_rel)
    dict_path = os.path.join(multilingual_posTagger_home, dict_rel)

    if not os.path.exists(model_path) or not os.path.exists(dict_path):
        pytest.skip(
            f"RDRPOSTagger model/dict not found for {language}: "
            f"{model_path}, {dict_path}"
        )


def _assert_tagged_shape(tagged, expected_sentences):
    assert isinstance(tagged, list)
    assert len(tagged) == expected_sentences

    for sentence in tagged:
        assert isinstance(sentence, list)
        assert sentence, "Expected at least one token for each sentence"
        for token_tag in sentence:
            assert isinstance(token_tag, list)
            assert len(token_tag) == 2
            token, tag = token_tag
            assert token
            assert tag


@pytest.mark.integration
def test_tmrdrpostagger_tag_segments_en():
    from TMPosTagger.TMRDRPOSTagger import TMRDRPOSTagger

    _require_model_files("EN")
    tagger = TMRDRPOSTagger("EN")
    sentences = ["There is a big problem."]
    tagged = tagger.tag_segments(sentences)

    _assert_tagged_shape(tagged, len(sentences))


@pytest.mark.integration
def test_tmrdrpostagger_only_tag_segments_en():
    from TMPosTagger.TMRDRPOSTagger import TMRDRPOSTagger

    _require_model_files("EN")
    tagger = TMRDRPOSTagger("EN")
    sentences = ["This is a short test."]
    tagged = tagger.only_tag_segments(sentences)

    _assert_tagged_shape(tagged, len(sentences))


@pytest.mark.integration
def test_tmpos_tagger_multilingual_selection_de():
    from TMPosTagger.TMPosTagger import TMPosTagger
    from TMPosTagger.TMRDRPOSTagger import TMRDRPOSTagger

    _require_model_files("DE")
    tm_tagger = TMPosTagger("DE")
    assert isinstance(tm_tagger.tagger, TMRDRPOSTagger)

    tagged = tm_tagger.tag_segments(["Das ist ein kurzer Test."])
    _assert_tagged_shape(tagged, 1)

