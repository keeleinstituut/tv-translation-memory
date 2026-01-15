#!/usr/bin/env python3
import pytest

from TMPosTagger.TMTokenizer import TMPragmatic


@pytest.mark.unit
def test_tm_pragmatic_tokenize_sent_splits_and_filters_empty(monkeypatch):
    captured = {}

    def fake_run(cmd, withexitstatus=False):
        captured["cmd"] = cmd
        captured["withexitstatus"] = withexitstatus
        return b"First sentence.\r\n\r\nSecond sentence.\r\n"

    monkeypatch.setattr("TMPosTagger.TMTokenizer.pexpect.run", fake_run)

    tokenizer = TMPragmatic("EN")
    result = tokenizer.tokenize_sent("ignored input")

    assert result == ["First sentence.", "Second sentence."]
    assert captured["withexitstatus"] is False
    assert "segmenter.rb en" in captured["cmd"]
    assert '"ignored input"' in captured["cmd"]


@pytest.mark.unit
def test_tm_pragmatic_tokenize_sent_handles_single_line(monkeypatch):
    def fake_run(cmd, withexitstatus=False):
        return b"Only one sentence.\r\n"

    monkeypatch.setattr("TMPosTagger.TMTokenizer.pexpect.run", fake_run)

    tokenizer = TMPragmatic("En")
    result = tokenizer.tokenize_sent("text")

    assert result == ["Only one sentence."]

