#!/usr/bin/env python3
import os
import sys

import pytest

# Append to python path
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)
sys.path.insert(0, ".")

pytest.importorskip("Mykytea")


@pytest.mark.integration
def test_kytea_japanese_pos_tagger():
    from TMPosTagger.TMJapanesePosTagger import TMMyKyteaTagger

    sentences = [
        "太郎はこの本を二郎を見た女性に渡した。",
        "日本語のテストです。",
    ]
    tagger = TMMyKyteaTagger()
    tagged = tagger.tag_segments(sentences)

    assert isinstance(tagged, list)
    assert len(tagged) == len(sentences)

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
def test_kytea_tokenizer_process():
    from TMPosTagger.TMTokenizer import TMTokenizer

    tokenizer = TMTokenizer("JA").tokenizer
    output = tokenizer.process("太郎はこの本を二郎を見た女性に渡した。")

    assert isinstance(output, str)
    assert output

