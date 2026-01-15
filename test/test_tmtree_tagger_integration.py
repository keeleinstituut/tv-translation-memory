#!/usr/bin/env python3
import gzip
import os
import sys
import tarfile
from pathlib import Path
import shutil

import pytest

# Append to python path
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)
sys.path.insert(0, ".")

def _prepare_treetagger_home(tmp_path: Path) -> Path:
    repo_root = os.path.abspath(os.path.join(__file__, "../.."))
    tools_dir = os.path.join(repo_root, "tools", "tree-tagger-linux-3.2")

    scripts_tar = os.path.join(tools_dir, "tagger-scripts.tar.gz")
    if not os.path.exists(scripts_tar):
        raise RuntimeError("tagger-scripts.tar.gz not found in tools")

    with tarfile.open(scripts_tar, "r:gz") as tar:
        tar.extractall(tmp_path)

    bin_src = os.path.join(tools_dir, "bin")
    bin_dst = tmp_path / "bin"
    shutil.copytree(bin_src, bin_dst, dirs_exist_ok=True)

    lib_dir = tmp_path / "lib"
    lib_dir.mkdir(exist_ok=True)

    english_par = os.path.join(tools_dir, "english-par-linux-3.2-utf8.bin.gz")
    if not os.path.exists(english_par):
        raise RuntimeError("english-par-linux-3.2-utf8.bin.gz not found in tools")

    with gzip.open(english_par, "rb") as fin, (lib_dir / "english-utf8.par").open("wb") as fout:
        shutil.copyfileobj(fin, fout)

    abbr_path = lib_dir / "english-abbreviations"
    if not abbr_path.exists():
        for path in tmp_path.rglob("english-abbreviations"):
            shutil.copy(path, abbr_path)
            break
    if not abbr_path.exists():
        raise RuntimeError("english-abbreviations not found in tagger scripts")

    cmd_dir = tmp_path / "cmd"
    cmd_dir.mkdir(exist_ok=True)
    cmd_script = cmd_dir / "tree-tagger-english"
    cmd_script.write_text(
        "\n".join(
            [
                "#!/bin/sh",
                "",
                f"BIN={bin_dst}",
                f"CMD={cmd_dir}",
                f"LIB={lib_dir}",
                "",
                'OPTIONS="-token -lemma -sgml"',
                "",
                "TOKENIZER=${CMD}/utf8-tokenize.perl",
                "TAGGER=${BIN}/tree-tagger",
                "ABBR_LIST=${LIB}/english-abbreviations",
                "PARFILE=${LIB}/english-utf8.par",
                "",
                "$TOKENIZER -e -a $ABBR_LIST $* |",
                "grep -v '^$' |",
                "$TAGGER $OPTIONS $PARFILE |",
                "perl -pe 's/\\tV[BDHV]/\\tVB/;s/\\tIN\\/that/\\tIN/;'",
                "",
            ]
        )
    )
    os.chmod(cmd_script, 0o755)

    return tmp_path


@pytest.mark.integration
def test_tmtree_tagger_pos_tags_en(tmp_path, monkeypatch):
    from TMPosTagger import TMTreeTagger as tmtreetagger_module
    from TMPosTagger.TMTreeTagger import TMTreeTagger

    treetagger_home = _prepare_treetagger_home(tmp_path)
    monkeypatch.setattr(
        tmtreetagger_module, "treetagger_posTagger_home", str(treetagger_home)
    )

    sentences = ["There is a big problem.", "This is a short test."]
    tagger = TMTreeTagger("EN")
    tagged = tagger.only_tag_segments(sentences)

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

