#!/usr/bin/env python3
"""
Unit tests for edit distance functionality in TMUtilsMatching.

Tests the editdistance package usage for translation memory matching.
"""
import os
import sys
import pytest

# Add src to path for imports
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from TMMatching.TMUtilsMatching import TMUtilsMatching


class TestTMUtilsMatchingEditDistance:
    """Test suite for edit distance functions in TMUtilsMatching."""

    # Tests for _edit_distance()

    @pytest.mark.unit
    def test_edit_distance_identical_strings(self):
        """Test that identical strings return edit distance of 0."""
        result = TMUtilsMatching._edit_distance("hello", "hello")
        assert result == 0

    @pytest.mark.unit
    def test_edit_distance_single_insertion(self):
        """Test edit distance with single character insertion."""
        # "abc" -> "abcd" requires 1 insertion
        result = TMUtilsMatching._edit_distance("abc", "abcd")
        assert result == 1

    @pytest.mark.unit
    def test_edit_distance_single_deletion(self):
        """Test edit distance with single character deletion."""
        # "abcd" -> "abc" requires 1 deletion
        result = TMUtilsMatching._edit_distance("abcd", "abc")
        assert result == 1

    @pytest.mark.unit
    def test_edit_distance_single_substitution(self):
        """Test edit distance with single character substitution."""
        # "abc" -> "abd" requires 1 substitution
        result = TMUtilsMatching._edit_distance("abc", "abd")
        assert result == 1

    @pytest.mark.unit
    def test_edit_distance_multiple_changes(self):
        """Test edit distance with multiple character changes."""
        # "hello" -> "world" requires multiple changes
        result = TMUtilsMatching._edit_distance("hello", "world")
        assert result == 4

    @pytest.mark.unit
    def test_edit_distance_both_empty_strings(self):
        """Test edit distance with both strings empty."""
        result = TMUtilsMatching._edit_distance("", "")
        assert result == 0

    @pytest.mark.unit
    def test_edit_distance_one_empty_string(self):
        """Test edit distance when one string is empty."""
        # Empty string to "hello" requires 5 insertions
        result1 = TMUtilsMatching._edit_distance("", "hello")
        assert result1 == 5

        # "hello" to empty string requires 5 deletions
        result2 = TMUtilsMatching._edit_distance("hello", "")
        assert result2 == 5

    @pytest.mark.unit
    def test_edit_distance_whitespace_handling(self):
        """Test edit distance with whitespace differences."""
        # "a b" vs "ab" - space is a character difference
        result = TMUtilsMatching._edit_distance("a b", "ab")
        assert result == 1

    @pytest.mark.unit
    def test_edit_distance_unicode(self):
        """Test edit distance with Unicode characters."""
        # Test with non-ASCII characters
        result1 = TMUtilsMatching._edit_distance("café", "cafe")
        assert result1 == 1  # é -> e substitution

        result2 = TMUtilsMatching._edit_distance("こんにちは", "こんにちわ")
        assert result2 == 1  # Single character difference in Japanese

    @pytest.mark.unit
    def test_edit_distance_case_sensitive(self):
        """Test that edit distance is case sensitive."""
        # "Hello" vs "hello" - case difference counts as substitution
        result = TMUtilsMatching._edit_distance("Hello", "hello")
        assert result == 1

    @pytest.mark.unit
    def test_edit_distance_special_characters(self):
        """Test edit distance with special characters and punctuation."""
        result1 = TMUtilsMatching._edit_distance("hello!", "hello")
        assert result1 == 1  # Exclamation mark difference

        result2 = TMUtilsMatching._edit_distance("test@123", "test#123")
        assert result2 == 1  # @ vs # substitution

    @pytest.mark.unit
    def test_edit_distance_long_strings(self):
        """Test edit distance with longer strings."""
        str1 = "The quick brown fox jumps over the lazy dog"
        str2 = "The quick brown fox jumps over the lazy cat"
        result = TMUtilsMatching._edit_distance(str1, str2)
        assert result == 3  # "dog" -> "cat" = 3 substitutions

    @pytest.mark.unit
    def test_edit_distance_returns_integer(self):
        """Test that edit distance always returns an integer."""
        result = TMUtilsMatching._edit_distance("test", "text")
        assert isinstance(result, int)
        assert result >= 0

    # Tests for un_match_distance()

    @pytest.mark.unit
    def test_un_match_distance_identical_strings(self):
        """Test that identical strings return normalized distance of 1.0."""
        result = TMUtilsMatching.un_match_distance("hello", "hello")
        assert result == 1.0

    @pytest.mark.unit
    def test_un_match_distance_identical_strings_with_whitespace(self):
        """Test that identical strings with leading/trailing whitespace return 1.0 after stripping."""
        result = TMUtilsMatching.un_match_distance("  hello  ", "hello")
        assert result == 1.0

    @pytest.mark.unit
    def test_un_match_distance_completely_different(self):
        """Test normalized distance with completely different strings."""
        result = TMUtilsMatching.un_match_distance("hello", "world")
        # Should return a value close to 0 (more different = lower score)
        assert 0.0 <= result < 1.0
        assert result < 0.5  # Completely different should be well below 0.5

    @pytest.mark.unit
    def test_un_match_distance_partial_match(self):
        """Test normalized distance with partially matching strings."""
        # "hello" vs "hell" - one character difference
        result = TMUtilsMatching.un_match_distance("hello", "hell")
        assert 0.0 < result < 1.0
        assert result > 0.5  # Should be closer to 1.0 than 0.0

    @pytest.mark.unit
    def test_un_match_distance_single_character_difference(self):
        """Test normalized distance with single character difference."""
        result = TMUtilsMatching.un_match_distance("abc", "abd")
        # Normalized: 1 - (1 / max(3, 3)) = 1 - 1/3 = 2/3 ≈ 0.667
        expected = 1.0 - (1.0 / max(len("abc"), len("abd")))
        assert abs(result - expected) < 0.001

    @pytest.mark.unit
    def test_un_match_distance_both_empty_strings(self):
        """Test normalized distance with both strings empty (after stripping)."""
        # Both empty after strip: should return 1.0 (perfect match) instead of division by zero
        result = TMUtilsMatching.un_match_distance("", "")
        assert result == 1.0

    @pytest.mark.unit
    def test_un_match_distance_whitespace_only_strings(self):
        """Test normalized distance with whitespace-only strings (after stripping)."""
        # Strings with only whitespace become empty after strip, should return 1.0
        result = TMUtilsMatching.un_match_distance("   ", "  ")
        assert result == 1.0

    @pytest.mark.unit
    def test_un_match_distance_one_empty_string(self):
        """Test normalized distance when one string is empty."""
        # Empty vs "hello": edit distance = 5, max(0, 5) = 5
        # Result: 1 - (5/5) = 0.0
        result = TMUtilsMatching.un_match_distance("", "hello")
        assert result == 0.0

    @pytest.mark.unit
    def test_un_match_distance_whitespace_stripping(self):
        """Test that whitespace is properly stripped before calculation."""
        # "  hello  " should be treated as "hello" after strip
        result1 = TMUtilsMatching.un_match_distance("  hello  ", "hello")
        result2 = TMUtilsMatching.un_match_distance("hello", "hello")
        assert result1 == result2 == 1.0

    @pytest.mark.unit
    def test_un_match_distance_length_normalization(self):
        """Test that normalization uses max length correctly."""
        # "abc" vs "abcd": edit distance = 1, max(3, 4) = 4
        # Result: 1 - (1/4) = 0.75
        result = TMUtilsMatching.un_match_distance("abc", "abcd")
        expected = 1.0 - (1.0 / max(len("abc"), len("abcd")))
        assert abs(result - expected) < 0.001

    @pytest.mark.unit
    def test_un_match_distance_unicode(self):
        """Test normalized distance with Unicode characters."""
        result = TMUtilsMatching.un_match_distance("café", "cafe")
        # Should handle Unicode properly
        assert 0.0 <= result <= 1.0
        assert result < 1.0  # Different strings

    @pytest.mark.unit
    def test_un_match_distance_returns_float(self):
        """Test that un_match_distance always returns a float."""
        result = TMUtilsMatching.un_match_distance("test", "text")
        assert isinstance(result, (int, float))
        assert 0.0 <= result <= 1.0

    @pytest.mark.unit
    def test_un_match_distance_short_vs_long_strings(self):
        """Test normalized distance with strings of very different lengths."""
        # Short vs long string
        result = TMUtilsMatching.un_match_distance("a", "abcdefghij")
        # Edit distance = 9, max(1, 10) = 10
        # Result: 1 - (9/10) = 0.1
        expected = 1.0 - (9.0 / max(len("a"), len("abcdefghij")))
        assert abs(result - expected) < 0.001

    @pytest.mark.unit
    def test_un_match_distance_case_sensitive(self):
        """Test that normalized distance is case sensitive."""
        result = TMUtilsMatching.un_match_distance("Hello", "hello")
        # Single character difference (case)
        assert 0.0 < result < 1.0

    @pytest.mark.unit
    @pytest.mark.parametrize("src,tgt,expected_min,expected_max", [
        ("hello", "hello", 1.0, 1.0),  # Identical
        ("hello", "world", 0.0, 0.3),  # Completely different
        ("hello", "hell", 0.7, 1.0),   # One character off
        ("abc", "abcd", 0.7, 0.8),     # One insertion
    ])
    def test_un_match_distance_parametrized(self, src, tgt, expected_min, expected_max):
        """Parametrized test for various string pairs."""
        result = TMUtilsMatching.un_match_distance(src, tgt)
        assert expected_min <= result <= expected_max

    @pytest.mark.unit
    @pytest.mark.parametrize("src,tgt,expected", [
        ("", "", 0),           # Both empty
        ("a", "", 1),          # One empty
        ("", "a", 1),         # One empty (reversed)
        ("abc", "abc", 0),    # Identical
        ("abc", "abd", 1),    # One substitution
        ("abc", "abcd", 1),   # One insertion
        ("abcd", "abc", 1),   # One deletion
    ])
    def test_edit_distance_parametrized(self, src, tgt, expected):
        """Parametrized test for edit distance with various string pairs."""
        result = TMUtilsMatching._edit_distance(src, tgt)
        assert result == expected

