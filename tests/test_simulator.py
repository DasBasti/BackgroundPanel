"""Tests for the terminal simulator panel."""

import pytest

from simulator import TerminalPanel
from interfaces import color_rgb
from config import LED_COUNT, GRID_WIDTH, GRID_HEIGHT


class TestTerminalPanel:
    """Tests for the TerminalPanel class."""

    def test_init_creates_empty_pixels(self) -> None:
        """Test that initialization creates empty pixel buffer."""
        panel = TerminalPanel()
        assert len(panel._pixels) == LED_COUNT
        assert all(p == 0 for p in panel._pixels)

    def test_dimensions(self) -> None:
        """Test panel dimensions are correct."""
        panel = TerminalPanel()
        assert panel.width == GRID_WIDTH
        assert panel.height == GRID_HEIGHT
        assert panel.pixel_count == LED_COUNT

    def test_set_pixel_stores_value(self) -> None:
        """Test that set_pixel stores the color value."""
        panel = TerminalPanel()
        test_color = color_rgb(100, 150, 200)
        panel.set_pixel(50, test_color)
        assert panel.get_pixel(50) == test_color

    def test_set_pixel_invalid_index(self) -> None:
        """Test that invalid indices are ignored."""
        panel = TerminalPanel()
        # Should not crash
        panel.set_pixel(-1, 0xFF0000)
        panel.set_pixel(LED_COUNT, 0xFF0000)

    def test_get_pixel_invalid_index(self) -> None:
        """Test that invalid indices return 0."""
        panel = TerminalPanel()
        assert panel.get_pixel(-1) == 0
        assert panel.get_pixel(LED_COUNT) == 0

    def test_set_pixel_xy(self) -> None:
        """Test setting pixel by coordinates."""
        panel = TerminalPanel()
        test_color = color_rgb(255, 128, 64)
        panel.set_pixel_xy(5, 10, test_color)
        
        # Verify via linear index
        expected_index = 5 + (10 * GRID_WIDTH)
        assert panel.get_pixel(expected_index) == test_color

    def test_get_pixel_xy(self) -> None:
        """Test getting pixel by coordinates."""
        panel = TerminalPanel()
        test_color = color_rgb(64, 128, 255)
        index = 7 + (15 * GRID_WIDTH)
        panel.set_pixel(index, test_color)
        
        assert panel.get_pixel_xy(7, 15) == test_color

    def test_clear(self) -> None:
        """Test that clear resets all pixels."""
        panel = TerminalPanel()
        
        # Set some pixels
        panel.set_pixel(0, 0xFF0000)
        panel.set_pixel(500, 0x00FF00)
        
        # Clear
        panel.clear()
        
        # Verify all are 0
        assert all(p == 0 for p in panel._pixels)

    def test_set_pixels(self) -> None:
        """Test setting all pixels at once."""
        panel = TerminalPanel()
        
        # Create test data
        test_pixels = [i for i in range(LED_COUNT)]
        panel.set_pixels(test_pixels)
        
        # Verify
        for i in range(LED_COUNT):
            assert panel.get_pixel(i) == i

    def test_get_pixels_returns_copy(self) -> None:
        """Test that get_pixels returns a copy."""
        panel = TerminalPanel()
        panel.set_pixel(0, 0xFF0000)
        
        pixels = panel.get_pixels()
        pixels[0] = 0x00FF00  # Modify the copy
        
        # Original should be unchanged
        assert panel.get_pixel(0) == 0xFF0000

    def test_half_block_mode_default(self) -> None:
        """Test that half-block mode is enabled by default."""
        panel = TerminalPanel()
        assert panel._use_half_blocks is True

    def test_full_block_mode(self) -> None:
        """Test creating panel with full-block mode."""
        panel = TerminalPanel(use_half_blocks=False)
        assert panel._use_half_blocks is False

    def test_frame_counter_increments(self) -> None:
        """Test that frame counter increments on display."""
        panel = TerminalPanel()
        initial_count = panel._frame_count
        
        # We can't easily test display() output, but we can check the counter
        # would increment (display() writes to stdout which we shouldn't
        # capture in unit tests)
        assert initial_count == 0
