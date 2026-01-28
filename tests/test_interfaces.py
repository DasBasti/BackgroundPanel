"""Tests for the interfaces module."""

import pytest

from interfaces import color_rgb, color_to_rgb, LEDPanelInterface


class TestColorFunctions:
    """Tests for color conversion functions."""

    def test_color_rgb_black(self) -> None:
        """Test creating black color."""
        result = color_rgb(0, 0, 0)
        assert result == 0

    def test_color_rgb_white(self) -> None:
        """Test creating white color."""
        result = color_rgb(255, 255, 255)
        # GRB format: (255 << 16) | (255 << 8) | 255
        assert result == 0xFFFFFF

    def test_color_rgb_red(self) -> None:
        """Test creating red color."""
        result = color_rgb(255, 0, 0)
        # RGB format: (255 << 16) | (0 << 8) | 0
        assert result == 0xFF0000

    def test_color_rgb_green(self) -> None:
        """Test creating green color."""
        result = color_rgb(0, 255, 0)
        # RGB format: (0 << 16) | (255 << 8) | 0
        assert result == 0x00FF00

    def test_color_rgb_blue(self) -> None:
        """Test creating blue color."""
        result = color_rgb(0, 0, 255)
        # RGB format: (0 << 16) | (0 << 8) | 255
        assert result == 0x0000FF

    def test_color_to_rgb_black(self) -> None:
        """Test extracting black color components."""
        r, g, b = color_to_rgb(0)
        assert (r, g, b) == (0, 0, 0)

    def test_color_to_rgb_white(self) -> None:
        """Test extracting white color components."""
        r, g, b = color_to_rgb(0xFFFFFF)
        assert (r, g, b) == (255, 255, 255)

    def test_color_roundtrip(self) -> None:
        """Test that color_rgb and color_to_rgb are inverses."""
        original = (128, 64, 32)
        color = color_rgb(*original)
        result = color_to_rgb(color)
        assert result == original

    def test_color_roundtrip_various(self) -> None:
        """Test roundtrip with various colors."""
        test_colors = [
            (0, 0, 0),
            (255, 255, 255),
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (100, 150, 200),
            (1, 1, 1),
        ]
        for original in test_colors:
            color = color_rgb(*original)
            result = color_to_rgb(color)
            assert result == original, f"Failed for color {original}"
