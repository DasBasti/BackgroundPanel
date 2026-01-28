"""Tests for the PCB string drawing module."""

import pytest

from pcb_string import PCB_LUT, PCB_COLORS, DEFAULT_CODE, draw_pcb_string
from interfaces import color_rgb


class MockPanel:
    """Mock panel for testing."""

    def __init__(self) -> None:
        self.pixels: dict[int, int] = {}

    @property
    def width(self) -> int:
        return 32

    @property
    def height(self) -> int:
        return 32

    @property
    def pixel_count(self) -> int:
        return 1024

    def init(self) -> None:
        pass

    def display(self) -> None:
        pass

    def clear(self) -> None:
        self.pixels.clear()

    def set_pixel(self, index: int, color: int) -> None:
        self.pixels[index] = color

    def get_pixel(self, index: int) -> int:
        return self.pixels.get(index, 0)

    def set_pixel_xy(self, x: int, y: int, color: int) -> None:
        self.set_pixel(x + y * 32, color)

    def get_pixel_xy(self, x: int, y: int) -> int:
        return self.get_pixel(x + y * 32)

    def set_pixels(self, pixels: list[int]) -> None:
        for i, p in enumerate(pixels):
            self.pixels[i] = p

    def get_pixels(self) -> list[int]:
        return [self.pixels.get(i, 0) for i in range(1024)]


class TestPCBLUT:
    """Tests for the PCB lookup table."""

    def test_lut_length(self) -> None:
        """Test that LUT has 64 entries."""
        assert len(PCB_LUT) == 64

    def test_lut_values_in_range(self) -> None:
        """Test that all LUT values are valid LED indices."""
        for idx in PCB_LUT:
            assert 0 <= idx < 1024, f"LUT value {idx} out of range"

    def test_lut_values_unique(self) -> None:
        """Test that all LUT values are unique."""
        assert len(PCB_LUT) == len(set(PCB_LUT))


class TestPCBColors:
    """Tests for the PCB color mapping."""

    def test_all_color_codes_present(self) -> None:
        """Test that all expected color codes are present."""
        expected_codes = ["w", "k", "b", "r", "g", "y", "o", "c", "m", "s"]
        for code in expected_codes:
            assert code in PCB_COLORS

    def test_color_values_valid(self) -> None:
        """Test that all color values are valid RGB tuples."""
        for code, color in PCB_COLORS.items():
            assert len(color) == 3, f"Color {code} doesn't have 3 components"
            for component in color:
                assert 0 <= component <= 255, f"Color {code} has invalid component"


class TestDrawPCBString:
    """Tests for the draw_pcb_string function."""

    def test_draw_empty_string(self) -> None:
        """Test drawing empty string does nothing."""
        panel = MockPanel()
        draw_pcb_string(panel, "")
        assert len(panel.pixels) == 0

    def test_draw_single_character(self) -> None:
        """Test drawing a single character."""
        panel = MockPanel()
        draw_pcb_string(panel, "r")
        assert len(panel.pixels) == 1
        assert PCB_LUT[0] in panel.pixels

    def test_draw_skips_space(self) -> None:
        """Test that space characters are skipped."""
        panel = MockPanel()
        draw_pcb_string(panel, " r")
        # Space should be skipped, 'r' should be drawn at second position
        assert len(panel.pixels) == 1

    def test_draw_respects_lut_limit(self) -> None:
        """Test that drawing stops at LUT limit."""
        panel = MockPanel()
        # Create a string longer than LUT
        long_string = "r" * 100
        draw_pcb_string(panel, long_string)
        # Should only draw 64 pixels (LUT length)
        assert len(panel.pixels) <= 64

    def test_default_code_valid(self) -> None:
        """Test that the default code contains valid characters."""
        for char in DEFAULT_CODE:
            assert char in PCB_COLORS or char == " "

    def test_color_mapping_correct(self) -> None:
        """Test that colors are mapped correctly."""
        panel = MockPanel()
        draw_pcb_string(panel, "r")
        expected_color = color_rgb(200, 0, 0)  # Red from PCB_COLORS
        assert panel.pixels[PCB_LUT[0]] == expected_color
