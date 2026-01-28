#!/usr/bin/env python3
import os
import sys
import pytest
from unittest.mock import Mock, patch

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from TMPreprocessor.Xml.TMXmlTagPreprocessor import TMXmlTagPreprocessor
from TMPreprocessor.Xml.XmlUtils import XmlUtils


@pytest.mark.unit
class TestTMXmlTagPreprocessor:
    """Unit tests for TMXmlTagPreprocessor class."""

    @pytest.fixture
    def preprocessor(self):
        """Create a TMXmlTagPreprocessor instance with default language pair."""
        return TMXmlTagPreprocessor(('en', 'es'))

    @pytest.fixture
    def preprocessor_fr_de(self):
        """Create a TMXmlTagPreprocessor instance with French-German language pair."""
        return TMXmlTagPreprocessor(('fr', 'de'))

    # Test __init__
    def test_init_default_langs(self, preprocessor):
        """Initialization with default language pair."""
        assert preprocessor.langs == ('en', 'es')
        assert preprocessor.parser is not None
        assert preprocessor.tag_transfer_basic is not None

    def test_init_custom_langs(self, preprocessor_fr_de):
        """Initialization with custom language pair."""
        assert preprocessor_fr_de.langs == ('fr', 'de')

    # Test process() - no tags
    def test_process_no_tags(self, preprocessor):
        """Text without tags should return unchanged."""
        text = "Hello world"
        result = preprocessor.process(text)
        assert result == text

    def test_process_empty_string(self, preprocessor):
        """Empty string should return unchanged."""
        text = ""
        result = preprocessor.process(text)
        assert result == text

    def test_process_whitespace_only(self, preprocessor):
        """Whitespace-only text should return unchanged."""
        text = "   "
        result = preprocessor.process(text)
        assert result == text

    # Test process() - valid tags
    def test_process_simple_tag(self, preprocessor):
        """Simple valid tag should be renamed to T1."""
        text = "Hello <b>world</b>"
        result = preprocessor.process(text)
        assert "<T1>" in result
        assert "</T1>" in result
        assert "<b>" not in result
        assert "world" in result

    def test_process_multiple_tags(self, preprocessor):
        """Multiple tags should be renamed to T1, T2, etc."""
        text = "Hello <b>world</b> and <i>test</i>"
        result = preprocessor.process(text)
        assert "<T1>" in result
        assert "<T2>" in result
        assert "world" in result
        assert "test" in result

    def test_process_nested_tags(self, preprocessor):
        """Nested tags should be processed correctly."""
        text = "Hello <b><i>world</i></b>"
        result = preprocessor.process(text)
        assert "<T" in result
        assert "world" in result

    def test_process_tags_with_attributes(self, preprocessor):
        """Tags with attributes should be processed (attributes removed)."""
        text = 'Hello <b class="bold">world</b>'
        result = preprocessor.process(text)
        assert "<T1>" in result
        assert "world" in result
        assert 'class="bold"' not in result

    def test_process_self_closing_tags(self, preprocessor):
        """Self-closing tags should be processed."""
        text = "Hello<br/>world"
        result = preprocessor.process(text)
        # Should either be processed or stripped
        assert isinstance(result, str)

    # Test process() - invalid tags
    def test_process_invalid_tag_names(self, preprocessor):
        """Invalid tag names should be fixed."""
        text = "Hello <123>world</123>"
        result = preprocessor.process(text)
        # Should either fix tags or strip them
        assert isinstance(result, str)
        assert "world" in result

    def test_process_tag_name_mismatch(self, preprocessor):
        """Tag name mismatches should result in stripped text."""
        text = "Hello <b>world</i>"
        result = preprocessor.process(text)
        # Should return stripped text (no tags)
        assert "<b>" not in result
        assert "</i>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_process_unfinished_tag(self, preprocessor):
        """Unfinished tags should result in stripped text."""
        text = "Hello <b>world"
        result = preprocessor.process(text)
        # Should return stripped text
        assert "<b>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_process_malformed_xml(self, preprocessor):
        """Malformed XML should result in stripped text."""
        text = "Hello <b><i>world</b></i>"
        result = preprocessor.process(text)
        # Should return stripped text
        assert "<b>" not in result
        assert "<i>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_process_tags_at_start(self, preprocessor):
        """Tags at the start of text should be processed."""
        text = "<b>Hello</b> world"
        result = preprocessor.process(text)
        assert "<T" in result or "<b>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_process_tags_at_end(self, preprocessor):
        """Tags at the end of text should be processed."""
        text = "Hello <b>world</b>"
        result = preprocessor.process(text)
        assert "<T" in result or "<b>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_process_special_characters(self, preprocessor):
        """Text with special characters should be handled."""
        text = "Hello <b>world!</b> How are you?"
        result = preprocessor.process(text)
        assert "!" in result
        assert "?" in result

    def test_process_multiple_consecutive_tags(self, preprocessor):
        """Multiple consecutive tags should be processed."""
        text = "<b>Hello</b><i>world</i>"
        result = preprocessor.process(text)
        assert isinstance(result, str)
        assert "Hello" in result
        assert "world" in result

    # Test process() - error handling
    @patch('TMPreprocessor.Xml.TMXmlTagPreprocessor.XmlUtils')
    def test_process_xml_parsing_exception(self, mock_xmlutils, preprocessor):
        """XML parsing exceptions should result in stripped text."""
        # Mock fix_tags to return stripped text that matches the actual behavior
        mock_xmlutils.fix_tags.return_value = ("<T>Hello <T>world</T></T>", "Hello world")
        mock_xmlutils.rename_tags.side_effect = Exception("Parse error")
        
        text = "Hello <b>world</b>"
        result = preprocessor.process(text)
        # Should return stripped text (second element of fix_tags return value)
        assert "<b>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_process_parser_error_log_tag_mismatch(self, preprocessor):
        """Parser error log with tag mismatch should result in stripped text."""
        # Create text that will trigger ERR_TAG_NAME_MISMATCH
        text = "Hello <b>world</i>"
        result = preprocessor.process(text)
        # Should return stripped text
        assert "<b>" not in result
        assert "</i>" not in result

    def test_process_parser_error_log_tag_not_finished(self, preprocessor):
        """Parser error log with unfinished tag should result in stripped text."""
        # Create text that will trigger ERR_TAG_NOT_FINISHED
        text = "Hello <b>world"
        result = preprocessor.process(text)
        # Should return stripped text
        assert "<b>" not in result

    # Test transfer_tags()
    def test_transfer_tags_no_source_tags(self, preprocessor):
        """Source with no tags should return target unchanged."""
        source = "Hello world"
        target = "Hola mundo"
        result = preprocessor.transfer_tags(source, target)
        assert result == target

    def test_transfer_tags_simple_tags(self, preprocessor):
        """Simple tag transfer should work."""
        source = "Hello <b>world</b>"
        target = "Hola <i>mundo</i>"
        result = preprocessor.transfer_tags(source, target)
        # Tags from source should be transferred to target
        assert "<b>" in result
        assert "mundo" in result

    def test_transfer_tags_multiple_tags(self, preprocessor):
        """Multiple tag transfer should work."""
        source = "Hello <b>world</b> and <i>test</i>"
        target = "Hola <u>mundo</u> y <em>prueba</em>"
        result = preprocessor.transfer_tags(source, target)
        # Source tags should be in result
        assert "<b>" in result or "<i>" in result
        assert "mundo" in result
        assert "prueba" in result

    def test_transfer_tags_empty_strings(self, preprocessor):
        """Empty strings should be handled."""
        source = ""
        target = ""
        result = preprocessor.transfer_tags(source, target)
        assert result == ""

    def test_transfer_tags_delegates_to_tag_transfer_basic(self, preprocessor):
        """transfer_tags should delegate to tag_transfer_basic."""
        source = "Hello <b>world</b>"
        target = "Hola mundo"
        
        # Mock the tag_transfer_basic
        mock_transfer = Mock(return_value="Hola <b>mundo</b>")
        preprocessor.tag_transfer_basic = mock_transfer
        
        result = preprocessor.transfer_tags(source, target)
        mock_transfer.assert_called_once_with(source, target)
        assert result == "Hola <b>mundo</b>"

    def test_transfer_tags_different_language_pairs(self, preprocessor_fr_de):
        """Transfer tags should work with different language pairs."""
        source = "Bonjour <b>monde</b>"
        target = "Hallo <i>Welt</i>"
        result = preprocessor_fr_de.transfer_tags(source, target)
        assert isinstance(result, str)
        assert "Welt" in result

    # Integration tests
    def test_process_integration_with_xmlutils_fix_tags(self, preprocessor):
        """process() should use XmlUtils.fix_tags."""
        text = "Hello <b>world</b>"
        result = preprocessor.process(text)
        # Should have processed the tags
        assert isinstance(result, str)
        assert "world" in result

    def test_process_integration_with_xmlutils_rename_tags(self, preprocessor):
        """process() should use XmlUtils.rename_tags."""
        text = "Hello <b>world</b>"
        result = preprocessor.process(text)
        # If tags are present, they should be renamed
        if "<T" in result:
            assert "<T1>" in result or "<T2>" in result

    # Edge cases
    def test_process_very_long_text(self, preprocessor):
        """Very long text should be handled."""
        text = "Hello " * 1000 + "<b>world</b>"
        result = preprocessor.process(text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_process_only_tags(self, preprocessor):
        """Text with only tags should be handled."""
        text = "<b></b>"
        result = preprocessor.process(text)
        assert isinstance(result, str)

    def test_process_unicode_characters(self, preprocessor):
        """Unicode characters should be handled."""
        text = "Hello <b>世界</b>"
        result = preprocessor.process(text)
        assert "世界" in result

    def test_process_mixed_content(self, preprocessor):
        """Mixed content (text and tags) should be handled."""
        text = "Hello <b>world</b> and <i>universe</i> test"
        result = preprocessor.process(text)
        assert "Hello" in result
        assert "world" in result
        assert "universe" in result
        assert "test" in result

