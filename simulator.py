"""ASCII terminal simulator for LED panel.

This module provides the TerminalPanel class for simulating an LED panel
in the terminal using ANSI color codes, useful for development and testing
without physical hardware.
"""

import sys

from config import GRID_HEIGHT, GRID_WIDTH, LED_COUNT
from interfaces import color_rgb, color_to_rgb


class TerminalPanel:
    """Terminal-based LED panel simulator using ANSI colors.
    
    This class implements LEDPanelInterface and renders the panel state
    to the terminal using 24-bit ANSI color codes.
    """

    def __init__(self, use_half_blocks: bool = True) -> None:
        """Initialize the terminal panel simulator.
        
        Args:
            use_half_blocks: If True, use half-block characters for 
                             better aspect ratio (2 pixels per character height)
        """
        self._width = GRID_WIDTH
        self._height = GRID_HEIGHT
        self._pixels: list[int] = [0] * LED_COUNT
        self._use_half_blocks = use_half_blocks
        self._frame_count = 0

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

    def init(self) -> None:
        """Initialize the terminal (clear screen, hide cursor)."""
        # Hide cursor
        sys.stdout.write("\033[?25l")
        # Clear screen
        sys.stdout.write("\033[2J")
        sys.stdout.flush()

    def _move_cursor_home(self) -> None:
        """Move cursor to top-left corner."""
        sys.stdout.write("\033[H")

    def _ansi_color_fg(self, r: int, g: int, b: int) -> str:
        """Generate ANSI escape code for 24-bit foreground color."""
        return f"\033[38;2;{r};{g};{b}m"

    def _ansi_color_bg(self, r: int, g: int, b: int) -> str:
        """Generate ANSI escape code for 24-bit background color."""
        return f"\033[48;2;{r};{g};{b}m"

    def _ansi_reset(self) -> str:
        """Generate ANSI reset code."""
        return "\033[0m"

    def display(self) -> None:
        """Render the panel to the terminal."""
        self._move_cursor_home()
        
        output: list[str] = []
        
        # Header with frame counter
        self._frame_count += 1
        output.append(f"LED Panel Simulator - Frame {self._frame_count}")
        output.append("─" * (self._width * 2 + 2))
        
        if self._use_half_blocks:
            # Use upper half block (▀) to show 2 vertical pixels per row
            # Top pixel as foreground, bottom pixel as background
            for y in range(0, self._height, 2):
                row_chars: list[str] = ["│"]
                for x in range(self._width):
                    top_idx = x + (y * self._width)
                    bottom_idx = x + ((y + 1) * self._width) if y + 1 < self._height else top_idx
                    
                    top_r, top_g, top_b = color_to_rgb(self._pixels[top_idx])
                    bottom_r, bottom_g, bottom_b = color_to_rgb(self._pixels[bottom_idx])
                    
                    row_chars.append(
                        f"{self._ansi_color_fg(top_r, top_g, top_b)}"
                        f"{self._ansi_color_bg(bottom_r, bottom_g, bottom_b)}"
                        f"▀"
                    )
                row_chars.append(f"{self._ansi_reset()}│")
                output.append("".join(row_chars))
        else:
            # Use full block (█) for each pixel
            for y in range(self._height):
                row_chars = ["│"]
                for x in range(self._width):
                    idx = x + (y * self._width)
                    r, g, b = color_to_rgb(self._pixels[idx])
                    row_chars.append(f"{self._ansi_color_fg(r, g, b)}██")
                row_chars.append(f"{self._ansi_reset()}│")
                output.append("".join(row_chars))
        
        output.append("─" * (self._width * 2 + 2))
        
        sys.stdout.write("\n".join(output))
        sys.stdout.flush()

    def clear(self) -> None:
        """Clear all pixels to black."""
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

    def cleanup(self) -> None:
        """Restore terminal state (show cursor)."""
        sys.stdout.write("\033[?25h")  # Show cursor
        sys.stdout.write(self._ansi_reset())
        sys.stdout.flush()


# Backwards compatibility layer for existing code
# TODO: Remove after full refactor is complete

_default_panel: TerminalPanel | None = None
panel: list[int] = []


def Color(r: int, g: int, b: int) -> int:
    """Create a color value (backwards compatibility)."""
    return color_rgb(r, g, b)


def init_strip() -> None:
    """Initialize the simulator (backwards compatibility)."""
    global _default_panel, panel
    _default_panel = TerminalPanel()
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


def cleanup() -> None:
    """Restore terminal state (backwards compatibility)."""
    if _default_panel is not None:
        _default_panel.cleanup()
