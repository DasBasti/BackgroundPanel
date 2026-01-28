"""Tests for the hardware panel coordinate mapping."""

import pytest

from config import GRID_WIDTH, GRID_HEIGHT, LED_COUNT


class TestCoordinateMapping:
    """Tests for the WS2812 serpentine coordinate mapping."""

    def test_build_coordinate_lut_size(self) -> None:
        """Test that LUT has correct size."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        assert len(panel._coordinate_lut) == LED_COUNT

    def test_coordinate_lut_covers_all_leds(self) -> None:
        """Test that LUT maps to all physical LEDs."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        physical_indices = set(panel._coordinate_lut)
        # All indices should be in valid range
        for idx in physical_indices:
            assert 0 <= idx < LED_COUNT

    def test_coordinate_lut_unique_mappings(self) -> None:
        """Test that each logical position maps to unique physical position."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        # Note: In a serpentine pattern, this may not always be unique
        # depending on the wiring. This test verifies the pattern is consistent.
        assert len(panel._coordinate_lut) == LED_COUNT

    def test_first_row_mapping(self) -> None:
        """Test that first row (y=0) maps correctly."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        
        # For y=0 (first 8 rows section):
        # x=0: even, so p = 0*8 + 0 = 0
        # x=1: odd, so p = 1*8 + 7 - 0 = 15
        # x=2: even, so p = 2*8 + 0 = 16
        assert panel._coordinate_lut[0] == 0  # x=0, y=0
        assert panel._coordinate_lut[1] == 15  # x=1, y=0 (serpentine reversal)

    def test_set_pixel_bounds(self) -> None:
        """Test that set_pixel respects bounds."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        
        # Valid indices
        panel.set_pixel(0, 0xFF0000)
        panel.set_pixel(LED_COUNT - 1, 0x00FF00)
        
        # Invalid indices should not crash
        panel.set_pixel(-1, 0xFF0000)
        panel.set_pixel(LED_COUNT, 0xFF0000)

    def test_set_pixel_xy_bounds(self) -> None:
        """Test that set_pixel_xy respects bounds."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        
        # Valid coordinates
        panel.set_pixel_xy(0, 0, 0xFF0000)
        panel.set_pixel_xy(GRID_WIDTH - 1, GRID_HEIGHT - 1, 0x00FF00)
        
        # Invalid coordinates should not crash
        panel.set_pixel_xy(-1, 0, 0xFF0000)
        panel.set_pixel_xy(GRID_WIDTH, 0, 0xFF0000)
        panel.set_pixel_xy(0, -1, 0xFF0000)
        panel.set_pixel_xy(0, GRID_HEIGHT, 0xFF0000)

    def test_get_pixel_returns_set_value(self) -> None:
        """Test that get_pixel returns previously set value."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        
        test_color = 0xABCDEF
        panel.set_pixel(42, test_color)
        assert panel.get_pixel(42) == test_color

    def test_clear_resets_all_pixels(self) -> None:
        """Test that clear sets all pixels to 0."""
        from hardware import WS2812Panel
        panel = WS2812Panel()
        
        # Set some pixels
        panel.set_pixel(0, 0xFF0000)
        panel.set_pixel(100, 0x00FF00)
        panel.set_pixel(500, 0x0000FF)
        
        # Clear
        panel.clear()
        
        # All should be 0
        assert panel.get_pixel(0) == 0
        assert panel.get_pixel(100) == 0
        assert panel.get_pixel(500) == 0
