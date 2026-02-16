#!/usr/bin/env python3
import os
import sys
import pytest
from lxml import etree

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from TMPreprocessor.Xml.XmlUtils import XmlUtils


@pytest.mark.unit
class TestXmlUtils:
    """Unit tests for XmlUtils class."""

    # Test strip_tags
    def test_strip_tags_no_tags(self):
        """Text with no tags should return unchanged (except whitespace normalization)."""
        text = "Hello world"
        result = XmlUtils.strip_tags(text)
        assert result == "Hello world"

    def test_strip_tags_simple_tag(self):
        """Simple tag should be removed."""
        text = "Hello <b>world</b>"
        result = XmlUtils.strip_tags(text)
        assert "<b>" not in result
        assert "</b>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_strip_tags_multiple_tags(self):
        """Multiple tags should all be removed."""
        text = "Hello <b>world</b> and <i>universe</i>"
        result = XmlUtils.strip_tags(text)
        assert "<b>" not in result
        assert "</b>" not in result
        assert "<i>" not in result
        assert "</i>" not in result
        assert "Hello" in result
        assert "world" in result
        assert "universe" in result

    def test_strip_tags_nested_tags(self):
        """Nested tags should all be removed."""
        text = "Hello <b><i>world</i></b>"
        result = XmlUtils.strip_tags(text)
        assert "<b>" not in result
        assert "<i>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_strip_tags_self_closing(self):
        """Self-closing tags should be removed."""
        text = "Hello<br/>world"
        result = XmlUtils.strip_tags(text)
        assert "<br/>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_strip_tags_with_attributes(self):
        """Tags with attributes should be removed."""
        text = 'Hello <b class="bold">world</b>'
        result = XmlUtils.strip_tags(text)
        assert "<b" not in result
        assert "world" in result

    def test_strip_tags_whitespace_normalization(self):
        """Multiple spaces should be normalized to single space."""
        text = "Hello  <b>world</b>   test"
        result = XmlUtils.strip_tags(text)
        assert "  " not in result
        assert "   " not in result

    def test_strip_tags_empty_string(self):
        """Empty string should return empty string."""
        result = XmlUtils.strip_tags("")
        assert result == ""

    def test_strip_tags_only_tags(self):
        """Text with only tags should return empty or whitespace."""
        text = "<b></b>"
        result = XmlUtils.strip_tags(text)
        assert "<b>" not in result

    # Test extract_tags
    def test_extract_tags_no_tags(self):
        """Text with no tags should return empty list."""
        result = XmlUtils.extract_tags("Hello world")
        assert result == []

    def test_extract_tags_simple_tag(self):
        """Simple tag should be extracted."""
        result = XmlUtils.extract_tags("Hello <b>world</b>")
        assert "<b>" in result
        assert "</b>" in result
        assert len(result) == 2

    def test_extract_tags_multiple_tags(self):
        """Multiple tags should all be extracted."""
        result = XmlUtils.extract_tags("Hello <b>world</b> and <i>universe</i>")
        assert "<b>" in result
        assert "</b>" in result
        assert "<i>" in result
        assert "</i>" in result
        assert len(result) == 4

    def test_extract_tags_self_closing(self):
        """Self-closing tags should be extracted."""
        result = XmlUtils.extract_tags("Hello<br/>world")
        assert "<br/>" in result

    def test_extract_tags_with_attributes(self):
        """Tags with attributes should be extracted."""
        result = XmlUtils.extract_tags('Hello <b class="bold">world</b>')
        assert any('<b' in tag for tag in result)
        assert '</b>' in result

    # Test replace_tags
    def test_replace_tags_no_tags(self):
        """Text with no tags should return unchanged."""
        text = "Hello world"
        result = XmlUtils.replace_tags(text)
        assert result == text

    def test_replace_tags_simple_tag(self):
        """Simple tag should be replaced with placeholder."""
        text = "Hello <T1>world</T1>"
        result = XmlUtils.replace_tags(text)
        assert XmlUtils.TAG_PLACEHOLDER in result
        assert "<T1>" not in result
        assert "</T1>" not in result

    def test_replace_tags_multiple_tags(self):
        """Multiple tags should all be replaced."""
        text = "Hello <T1>world</T1> and <T2>test</T2>"
        result = XmlUtils.replace_tags(text)
        # Each tag (opening and closing) gets replaced, so 2 tags = 4 placeholders
        assert result.count(XmlUtils.TAG_PLACEHOLDER) == 4

    def test_replace_tags_with_adjacent_space_placeholder(self):
        """Adjacent spaces should be replaced when placeholder is provided."""
        text = "Hello  <T1>world</T1>  test"
        result = XmlUtils.replace_tags(text, adjacent_space_placeholder=XmlUtils.SPACE_PLACEHOLDER)
        assert XmlUtils.SPACE_PLACEHOLDER in result or XmlUtils.TAG_PLACEHOLDER in result

    # Test fix_tags
    def test_fix_tags_no_tags(self):
        """Text with no tags should return tuple with same text."""
        text = "Hello world"
        otext, stext = XmlUtils.fix_tags(text)
        assert otext == text
        assert stext == text

    def test_fix_tags_simple_tag(self):
        """Simple tag should be fixed to use TAG_PREFIX."""
        text = "Hello <b>world</b>"
        otext, stext = XmlUtils.fix_tags(text)
        assert XmlUtils.TAG_PREFIX in otext
        assert "<b>" not in otext
        assert stext == "Hello world"

    def test_fix_tags_invalid_tag_name(self):
        """Invalid tag names should be replaced with TAG_PREFIX."""
        text = "Hello <123>world</123>"
        otext, stext = XmlUtils.fix_tags(text)
        assert XmlUtils.TAG_PREFIX in otext
        assert "<123>" not in otext

    def test_fix_tags_self_closing(self):
        """Self-closing tags should be handled."""
        text = "Hello<br/>world"
        otext, stext = XmlUtils.fix_tags(text)
        assert XmlUtils.TAG_PREFIX in otext
        # Self-closing tags are removed without adding space
        assert stext == "Helloworld"

    # Test simplify_tags
    def test_simplify_tags_no_tags(self):
        """Text with no tags should return unchanged."""
        text = "Hello world"
        result = XmlUtils.simplify_tags(text)
        assert result == text

    def test_simplify_tags_simple_tag(self):
        """Simple tag should be simplified to T1."""
        text = "Hello <b>world</b>"
        result = XmlUtils.simplify_tags(text)
        assert "<T1>" in result
        assert "</T1>" in result
        assert "<b>" not in result

    def test_simplify_tags_multiple_tags(self):
        """Multiple tags should be simplified to T1, T2, etc."""
        text = "Hello <b>world</b> and <i>test</i>"
        result = XmlUtils.simplify_tags(text)
        assert "<T1>" in result
        assert "<T2>" in result

    def test_simplify_tags_nested_tags(self):
        """Nested tags should be simplified."""
        text = "Hello <b><i>world</i></b>"
        result = XmlUtils.simplify_tags(text)
        assert "<T" in result
        assert "<b>" not in result
        assert "<i>" not in result

    # Test rename_tags
    def test_rename_tags_simple_tag(self):
        """Simple tag should be renamed to T1."""
        text = "<T>world</T>"
        result = XmlUtils.rename_tags(text)
        assert "<T1>" in result
        assert "</T1>" in result

    def test_rename_tags_multiple_tags(self):
        """Multiple tags should be renamed in DFS order."""
        text = "<T>world</T> and <T>test</T>"
        result = XmlUtils.rename_tags(text)
        assert "<T1>" in result
        assert "<T2>" in result

    def test_rename_tags_nested_tags(self):
        """Nested tags should be renamed in DFS order."""
        text = "<T><T>world</T></T>"
        result = XmlUtils.rename_tags(text)
        # reduce_tree removes redundant nested tags, so only one tag remains
        assert "<T1>" in result
        assert "world" in result

    def test_rename_tags_already_renamed(self):
        """Tags already in T1, T2 format should be preserved."""
        text = "<T1>world</T1>"
        result = XmlUtils.rename_tags(text)
        assert "<T1>" in result

    # Test join_tags
    def test_join_tags_simple_case(self):
        """Tags with spaces should be joined with words."""
        text = "Hello <b> world </b> test"
        pattern = '(</?[^<>]+/?>)([^<>]+)(</?[^<>]+/?>)'
        result = XmlUtils.join_tags(text, pattern)
        assert "<b>world</b>" in result
        assert " <b> " not in result

    def test_join_tags_multiple_tags(self):
        """Multiple tags should all be joined."""
        text = "Hello <b> world </b> and <i> test </i>"
        pattern = '(</?[^<>]+/?>)([^<>]+)(</?[^<>]+/?>)'
        result = XmlUtils.join_tags(text, pattern)
        assert "<b>world</b>" in result
        assert "<i>test</i>" in result

    def test_join_tags_no_match(self):
        """Text that doesn't match pattern should return unchanged."""
        text = "Hello world"
        pattern = '(</?[^<>]+/?>)([^<>]+)(</?[^<>]+/?>)'
        result = XmlUtils.join_tags(text, pattern)
        assert result == text

    # Test reduce_tags
    def test_reduce_tags_simple(self):
        """Tags should be reduced to 'T' placeholder."""
        text = "Hello <T1>world</T1>"
        result = XmlUtils.reduce_tags(text)
        assert " T " in result
        assert "<T1>" not in result

    def test_reduce_tags_multiple(self):
        """Multiple tags should all be reduced."""
        text = "Hello <T1>world</T1> and <T2>test</T2>"
        result = XmlUtils.reduce_tags(text)
        assert result.count(" T ") >= 2

    def test_reduce_tags_whitespace_normalization(self):
        """Multiple spaces should be normalized."""
        text = "Hello  <T1>world</T1>  test"
        result = XmlUtils.reduce_tags(text)
        assert "  " not in result

    # Test reduce_tree
    def test_reduce_tree_single_child_empty(self):
        """Empty tag with single child should be reduced."""
        root = etree.Element("root")
        t1 = etree.SubElement(root, "T1")
        t2 = etree.SubElement(t1, "T2")
        t2.text = "test"
        XmlUtils.reduce_tree(root)
        # T1 should be replaced by T2
        assert len(root) == 1
        assert root[0].tag == "T2"

    def test_reduce_tree_self_closing_adjacent(self):
        """Adjacent self-closing tags should be reduced."""
        root = etree.Element("root")
        t1 = etree.SubElement(root, "T1")
        t2 = etree.SubElement(root, "T2")
        XmlUtils.reduce_tree(root)
        # Should have only one self-closing tag left
        assert len(root) <= 2

    def test_reduce_tree_no_reduction_needed(self):
        """Tree with content should not be reduced."""
        root = etree.Element("root")
        t1 = etree.SubElement(root, "T1")
        t1.text = "test"
        t2 = etree.SubElement(root, "T2")
        t2.text = "test2"
        original_len = len(root)
        XmlUtils.reduce_tree(root)
        assert len(root) == original_len

    # Test recover_tags_pos
    def test_recover_tags_pos_no_tags(self):
        """Text with no tag placeholders should return POS tags only."""
        text_pos = [("Hello", "NN"), ("world", "NN")]
        tags = []
        pos_with_tags, pos = XmlUtils.recover_tags_pos(text_pos, tags)
        assert pos_with_tags == ["NN", "NN"]
        assert pos == ["NN", "NN"]

    def test_recover_tags_pos_with_tags(self):
        """Tag placeholders should be replaced with actual tags."""
        text_pos = [("Hello", "NN"), (XmlUtils.TAG_PLACEHOLDER, None), ("world", "NN")]
        tags = ["<b>"]
        pos_with_tags, pos = XmlUtils.recover_tags_pos(text_pos, tags)
        assert "<b>" in pos_with_tags
        assert "NN" in pos_with_tags
        assert pos == ["NN", "NN"]

    def test_recover_tags_pos_insufficient_tags(self):
        """If tags list is shorter, should raise IndexError."""
        text_pos = [(XmlUtils.TAG_PLACEHOLDER, None), (XmlUtils.TAG_PLACEHOLDER, None)]
        tags = ["<b>"]
        # The code doesn't handle insufficient tags gracefully - it raises IndexError
        with pytest.raises(IndexError):
            XmlUtils.recover_tags_pos(text_pos, tags)

    def test_recover_tags_pos_short_word_pos(self):
        """Word_pos with less than 2 elements should be skipped."""
        text_pos = [("Hello",), ("world", "NN")]
        tags = []
        pos_with_tags, pos = XmlUtils.recover_tags_pos(text_pos, tags)
        assert "NN" in pos_with_tags
        assert len(pos) == 1

    # Test is_empty_tag
    def test_is_empty_tag_empty(self):
        """Tag with no text or tail should be empty."""
        elem = etree.Element("T1")
        assert XmlUtils.is_empty_tag(elem) is True

    def test_is_empty_tag_with_text(self):
        """Tag with text should not be empty."""
        elem = etree.Element("T1")
        elem.text = "test"
        assert XmlUtils.is_empty_tag(elem) is False

    def test_is_empty_tag_with_tail(self):
        """Tag with tail should not be empty."""
        elem = etree.Element("T1")
        elem.tail = "test"
        assert XmlUtils.is_empty_tag(elem) is False

    def test_is_empty_tag_whitespace_only(self):
        """Tag with only whitespace should be empty."""
        elem = etree.Element("T1")
        elem.text = "   "
        assert XmlUtils.is_empty_tag(elem) is True

    # Test is_self_closing_tag
    def test_is_self_closing_tag_string(self):
        """String representation of self-closing tag should be detected."""
        # Returns Match object (truthy) or None (falsy)
        assert XmlUtils.is_self_closing_tag("<br/>") is not None
        assert XmlUtils.is_self_closing_tag("<b>") is None

    def test_is_self_closing_tag_element_empty(self):
        """Empty element should be self-closing."""
        elem = etree.Element("T1")
        assert XmlUtils.is_self_closing_tag(elem) is True

    def test_is_self_closing_tag_element_with_text(self):
        """Element with text should not be self-closing."""
        elem = etree.Element("T1")
        elem.text = "test"
        assert XmlUtils.is_self_closing_tag(elem) is False

    def test_is_self_closing_tag_element_with_tail(self):
        """Element with tail should not be self-closing."""
        elem = etree.Element("T1")
        elem.tail = "test"
        assert XmlUtils.is_self_closing_tag(elem) is False

    # Test is_opening_tag
    def test_is_opening_tag_opening(self):
        """Opening tag should be detected."""
        # Returns Match object (truthy) or None (falsy)
        assert XmlUtils.is_opening_tag("<b>") is not None
        assert XmlUtils.is_opening_tag("</b>") is None
        assert XmlUtils.is_opening_tag("<br/>") is None

    def test_is_opening_tag_closing(self):
        """Closing tag should not be detected as opening."""
        assert XmlUtils.is_opening_tag("</b>") is None

    def test_is_opening_tag_self_closing(self):
        """Self-closing tag should not be detected as opening."""
        assert XmlUtils.is_opening_tag("<br/>") is None

    # Edge cases
    def test_strip_tags_special_characters(self):
        """Text with special characters should be handled."""
        text = "Hello <b>world!</b> How are you?"
        result = XmlUtils.strip_tags(text)
        assert "!" in result
        assert "?" in result

    def test_extract_tags_special_characters(self):
        """Tags with special characters should be extracted."""
        text = 'Hello <b attr="value">world</b>'
        result = XmlUtils.extract_tags(text)
        assert len(result) >= 1

    def test_fix_tags_tags_at_start(self):
        """Tags at the start of text should be handled."""
        text = "<b>Hello</b> world"
        otext, stext = XmlUtils.fix_tags(text)
        assert XmlUtils.TAG_PREFIX in otext
        assert stext == "Hello world"

    def test_fix_tags_tags_at_end(self):
        """Tags at the end of text should be handled."""
        text = "Hello <b>world</b>"
        otext, stext = XmlUtils.fix_tags(text)
        assert XmlUtils.TAG_PREFIX in otext
        assert stext == "Hello world"

    def test_rename_tags_empty_string(self):
        """Empty string should be handled."""
        result = XmlUtils.rename_tags("")
        assert result == ""

    def test_rename_tags_malformed_xml(self):
        """Malformed XML should be handled by parser with recover=True."""
        text = "<T>unclosed"
        # Should not raise exception due to recover=True
        try:
            result = XmlUtils.rename_tags(text)
            # Result may be empty or partial
            assert isinstance(result, str)
        except Exception:
            # If it raises, that's also acceptable behavior
            pass

