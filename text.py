"""Text rendering module for LED panel.

This module handles rendering text and usernames onto the LED panel
using PIL/Pillow for font rendering.
"""

import time

from PIL import Image, ImageDraw, ImageFont

from config import FONT_PATH, FONT_SIZE, GRID_HEIGHT, GRID_WIDTH
from interfaces import LEDPanelInterface, color_rgb, color_to_rgb


def get_colors_rgb(color: int) -> tuple[int, int, int]:
    """Convert a 24-bit color value to RGB tuple.

    Args:
        color: 24-bit color value.

    Returns:
        Tuple of (red, green, blue) values 0-255.
    """
    return color_to_rgb(color)


class TextRenderer:
    """Renders scrolling text onto an LED panel."""

    def __init__(self, panel: LEDPanelInterface, font_path: str | None = None) -> None:
        """Initialize the text renderer.

        Args:
            panel: The LED panel to render to.
            font_path: Path to TTF font file. Uses default if None.
        """
        self.panel = panel
        self.offset = 25
        font_file = font_path or str(FONT_PATH)
        self.font = ImageFont.truetype(font_file, FONT_SIZE)

    def draw_username(self, username: str, color: int) -> None:
        """Draw a scrolling username on the panel.

        Args:
            username: The username text to display.
            color: 24-bit color value for the text.
        """
        self.panel.clear()
        img = Image.new(mode="RGB", size=(GRID_WIDTH, GRID_HEIGHT))
        draw = ImageDraw.Draw(img)
        r, g, b = get_colors_rgb(color)
        draw.text((self.offset, 10), username, font=self.font, fill=(r, g, b))
        self.offset -= 1

        pixels = [color_rgb(p[0], p[1], p[2]) for p in img.convert("RGB").getdata()]
        self.panel.set_pixels(pixels)

    def reset(self) -> None:
        """Reset the scroll offset to starting position."""
        self.offset = 25

    def is_scrolled_off(self) -> bool:
        """Check if text has scrolled off the panel.

        Returns:
            True if the panel is empty (text scrolled off).
        """
        return not any(self.panel.get_pixels())


# Backwards compatibility layer
# TODO: Remove after full refactor

_default_renderer: TextRenderer | None = None
offset = 25
f: ImageFont.FreeTypeFont | None = None


def _get_legacy_font() -> ImageFont.FreeTypeFont:
    """Get or create legacy font instance."""
    global f
    if f is None:
        f = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    return f


def draw_username_on_panel(username: str, font: ImageFont.FreeTypeFont, color: int) -> None:
    """Legacy function for drawing username (backwards compatibility)."""
    global offset
    # Import here to avoid circular imports during transition
    import panel

    panel.clear()
    img = Image.new(mode="RGB", size=(GRID_WIDTH, GRID_HEIGHT))
    draw = ImageDraw.Draw(img)
    r, g, b = get_colors_rgb(color)
    draw.text((offset, 10), username, font=font, fill=(r, g, b))
    offset -= 1
    panel.panel = [color_rgb(p[0], p[1], p[2]) for p in img.convert("RGB").getdata()]


def reset() -> None:
    """Reset scroll offset (backwards compatibility)."""
    global offset
    offset = 25


# Initialize legacy font
f = _get_legacy_font()


if __name__ == "__main__":
    import panel
    import pcb_string

    panel.init_strip()

    while True:
        draw_username_on_panel("Platinenmacher", f, color_rgb(70, 0, 0))

        if not any(panel.panel):
            panel.display()
            break

        pcb_string.draw_pcb_string(pcb_string.code)
        panel.display()
        time.sleep(0.1)