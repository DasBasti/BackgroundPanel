"""WS2812 LED panel hardware driver.

This module provides the WS2812Panel class for controlling a physical
LED panel connected to a Raspberry Pi via the rpi_ws281x library.
"""

from typing import TYPE_CHECKING

from config import (
    GRID_HEIGHT,
    GRID_WIDTH,
    LED_BRIGHTNESS,
    LED_CHANNEL,
    LED_COUNT,
    LED_DMA,
    LED_FREQ_HZ,
    LED_INVERT,
    LED_PIN,
)
from interfaces import color_rgb

if TYPE_CHECKING:
    from rpi_ws281x import Adafruit_NeoPixel


class WS2812Panel:
    """Hardware driver for WS2812 LED panel.
    
    This class implements LEDPanelInterface for physical LED hardware
    connected to a Raspberry Pi GPIO pin.
    """

    def __init__(self) -> None:
        """Initialize the panel (does not start hardware yet)."""
        self._width = GRID_WIDTH
        self._height = GRID_HEIGHT
        self._pixels: list[int] = [0] * LED_COUNT
        self._strip: "Adafruit_NeoPixel | None" = None
        self._coordinate_lut: list[int] = self._build_coordinate_lut()

    @property
    def width(self) -> int:
        """Grid width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Grid height in pixels."""
        return self._height

    @property
    def pixel_count(self) -> int:
        """Total number of pixels."""
        return LED_COUNT

    def _build_coordinate_lut(self) -> list[int]:
        """Build lookup table mapping logical x,y to physical LED index.
        
        The physical LED layout uses a serpentine pattern across 4 sections
        of 8 rows each. This LUT pre-computes the mapping for fast access.
        """
        lut: list[int] = [0] * LED_COUNT
        
        for x in range(self._width):
            for y in range(self._height):
                logical_index = x + (y * self._width)
                
                # Calculate physical position based on serpentine wiring
                if y < 8:
                    if x % 2 == 0:
                        p = x * 8 + y
                    else:
                        p = x * 8 + 7 - y
                elif y < 16:
                    if x % 2 == 0:
                        p = (31 - x) * 8 + (y - 7)
                    else:
                        p = (31 - x) * 8 + (16 - y)
                    p += 255
                elif y < 24:
                    if x % 2 == 0:
                        p = x * 8 + y - 16
                    else:
                        p = x * 8 + 7 + (16 - y)
                    p += 256 * 2
                else:
                    if x % 2 == 0:
                        p = (31 - x) * 8 + (y - 23)
                    else:
                        p = (31 - x) * 8 + 32 - y
                    p += 256 * 3 - 1
                
                lut[logical_index] = p
        
        return lut

    def init(self) -> None:
        """Initialize the LED strip hardware."""
        from rpi_ws281x import Adafruit_NeoPixel

        self._strip = Adafruit_NeoPixel(
            LED_COUNT,
            LED_PIN,
            LED_FREQ_HZ,
            LED_DMA,
            LED_INVERT,
            LED_BRIGHTNESS,
            LED_CHANNEL,
        )
        self._strip.begin()

    def display(self) -> None:
        """Push the pixel buffer to the physical LEDs."""
        if self._strip is None:
            raise RuntimeError("Panel not initialized. Call init() first.")
        
        for logical_idx, color in enumerate(self._pixels):
            if color:  # Only update non-zero pixels for performance
                physical_idx = self._coordinate_lut[logical_idx]
                self._strip.setPixelColor(physical_idx, color)
        
        self._strip.show()

    def clear(self) -> None:
        """Clear all pixels to black."""
        if self._strip is not None:
            for i in range(LED_COUNT):
                self._strip.setPixelColor(i, 0)
        self._pixels = [0] * LED_COUNT

    def set_pixel(self, index: int, color: int) -> None:
        """Set a pixel by linear index."""
        if 0 <= index < LED_COUNT:
            self._pixels[index] = color

    def get_pixel(self, index: int) -> int:
        """Get a pixel color by linear index."""
        if 0 <= index < LED_COUNT:
            return self._pixels[index]
        return 0

    def set_pixel_xy(self, x: int, y: int, color: int) -> None:
        """Set a pixel by x,y coordinates."""
        if 0 <= x < self._width and 0 <= y < self._height:
            index = x + (y * self._width)
            self._pixels[index] = color

    def get_pixel_xy(self, x: int, y: int) -> int:
        """Get a pixel color by x,y coordinates."""
        if 0 <= x < self._width and 0 <= y < self._height:
            index = x + (y * self._width)
            return self._pixels[index]
        return 0

    def set_pixels(self, pixels: list[int]) -> None:
        """Set all pixels from a list."""
        if len(pixels) == LED_COUNT:
            self._pixels = pixels.copy()

    def get_pixels(self) -> list[int]:
        """Get a copy of all pixel values."""
        return self._pixels.copy()


# Backwards compatibility layer for existing code
# TODO: Remove after full refactor is complete

_default_panel: WS2812Panel | None = None
panel: list[int] = []


def Color(r: int, g: int, b: int) -> int:
    """Create a color value (backwards compatibility)."""
    return color_rgb(r, g, b)


def init_strip() -> None:
    """Initialize the LED strip (backwards compatibility)."""
    global _default_panel, panel
    _default_panel = WS2812Panel()
    _default_panel.init()
    panel = _default_panel._pixels


def display() -> None:
    """Display the panel (backwards compatibility)."""
    if _default_panel is not None:
        _default_panel._pixels = panel
        _default_panel.display()


def clear() -> None:
    """Clear the panel (backwards compatibility)."""
    global panel
    if _default_panel is not None:
        _default_panel.clear()
        panel = _default_panel._pixels
    else:
        panel = [0] * LED_COUNT
