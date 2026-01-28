"""Tests for the Levenshtein distance module."""

import pytest

from levenshtein import levenshtein_ratio_and_distance, CSS3_COLORS


class TestLevenshteinDistance:
    """Tests for levenshtein_ratio_and_distance function."""

    def test_identical_strings(self) -> None:
        """Test that identical strings have ratio 1.0."""
        result = levenshtein_ratio_and_distance("test", "test", ratio_calc=True)
        assert result == 1.0

    def test_completely_different_strings(self) -> None:
        """Test completely different strings."""
        result = levenshtein_ratio_and_distance("abc", "xyz", ratio_calc=True)
        assert isinstance(result, float)
        assert result < 0.5

    def test_similar_strings(self) -> None:
        """Test similar strings have high ratio."""
        result = levenshtein_ratio_and_distance("test", "tast", ratio_calc=True)
        assert isinstance(result, float)
        assert result > 0.7

    def test_empty_strings(self) -> None:
        """Test empty strings."""
        result = levenshtein_ratio_and_distance("", "", ratio_calc=True)
        # Division by zero edge case - both strings empty
        # This should be handled gracefully
        assert isinstance(result, (float, int))

    def test_one_empty_string(self) -> None:
        """Test one empty string."""
        result = levenshtein_ratio_and_distance("test", "", ratio_calc=True)
        assert isinstance(result, float)
        assert result == 0.0

    def test_distance_mode_returns_string(self) -> None:
        """Test that non-ratio mode returns a string."""
        result = levenshtein_ratio_and_distance("test", "tast", ratio_calc=False)
        assert isinstance(result, str)
        assert "edits" in result

    def test_case_sensitive(self) -> None:
        """Test that comparison is case sensitive."""
        result1 = levenshtein_ratio_and_distance("Test", "test", ratio_calc=True)
        result2 = levenshtein_ratio_and_distance("test", "test", ratio_calc=True)
        assert isinstance(result1, float)
        assert isinstance(result2, float)
        assert result1 < result2

    def test_color_name_matching(self) -> None:
        """Test matching typo to CSS3 color name."""
        # Simulate matching "bleu" to "Blue"
        best_match = ""
        best_ratio = 0.0
        for color in CSS3_COLORS:
            ratio = levenshtein_ratio_and_distance(color.lower(), "bleu", ratio_calc=True)
            if isinstance(ratio, float) and ratio > best_ratio:
                best_ratio = ratio
                best_match = color
        
        assert best_match == "Blue"
        assert best_ratio > 0.6


class TestCSS3Colors:
    """Tests for the CSS3 colors list."""

    def test_colors_not_empty(self) -> None:
        """Test that color list is not empty."""
        assert len(CSS3_COLORS) > 0

    def test_common_colors_present(self) -> None:
        """Test that common colors are present."""
        common_colors = ["Red", "Green", "Blue", "White", "Black", "Yellow"]
        for color in common_colors:
            assert color in CSS3_COLORS, f"{color} not in CSS3_COLORS"

    def test_colors_are_strings(self) -> None:
        """Test that all colors are strings."""
        for color in CSS3_COLORS:
            assert isinstance(color, str)

    def test_no_duplicate_colors(self) -> None:
        """Test that there are no duplicate colors."""
        assert len(CSS3_COLORS) == len(set(CSS3_COLORS))
