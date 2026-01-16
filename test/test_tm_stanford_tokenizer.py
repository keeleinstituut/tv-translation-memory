#!/usr/bin/env python3
import os
import sys
import shutil

import pytest

script_path = os.path.dirname(os.path.realpath(__file__))
repo_root = os.path.abspath(os.path.join(script_path, ".."))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, repo_root)
sys.path.insert(0, script_path)
sys.path.insert(0, ".")

from TMPosTagger.TMTokenizer import TMStanfordTokenizer


STANFORD_HOME = os.path.join(repo_root, "tools", "stanford-segmenter-2015-12-09")
STANFORD_DATA = os.path.join(STANFORD_HOME, "data")
STANFORD_JAR = os.path.join(STANFORD_HOME, "stanford-segmenter-3.6.0.jar")
SLF4J_JAR = os.path.join(STANFORD_HOME, "slf4j-api.jar")


def require_stanford_segmenter(model_filename, dict_filename=None):
    if shutil.which("java") is None:
        pytest.skip("Java not available; skipping Stanford Segmenter integration test")
    if not os.path.exists(STANFORD_JAR):
        pytest.skip("Stanford Segmenter JAR not found")
    if not os.path.exists(SLF4J_JAR):
        pytest.skip("SLF4J JAR not found")

    model_path = os.path.join(STANFORD_DATA, model_filename)
    if not os.path.exists(model_path):
        pytest.skip(f"Stanford Segmenter model not found: {model_filename}")

    if dict_filename:
        dict_path = os.path.join(STANFORD_DATA, dict_filename)
        if not os.path.exists(dict_path):
            pytest.skip(f"Stanford Segmenter dictionary not found: {dict_filename}")


@pytest.mark.integration
def test_tmstanfordtokenizer_zh_process():
    require_stanford_segmenter("ctb.gz", dict_filename="dict-chris6.ser.gz")
    tokenizer = TMStanfordTokenizer("ZH")

    output = tokenizer.process("斯坦福中文分词器测试。")

    assert isinstance(output, str)
    assert output.strip()


@pytest.mark.integration
def test_tmstanfordtokenizer_zh_tokenize_sent():
    require_stanford_segmenter("ctb.gz", dict_filename="dict-chris6.ser.gz")
    tokenizer = TMStanfordTokenizer("ZH")

    sentences = tokenizer.tokenize_sent("你好。再见。")

    assert sentences == ["你好。", "再见。"]

