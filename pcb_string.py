"""PCB visualization string drawing module.

This module renders a string code onto specific LED positions
representing a PCB layout on the panel.
"""

from interfaces import LEDPanelInterface, color_rgb

# Lookup table mapping code position to LED panel position
PCB_LUT: list[int] = [
    285, 315, 345, 375, 405, 435, 465, 495,
    251, 281, 311, 341, 371, 401, 431, 461,
    217, 247, 277, 307, 337, 367, 397, 427,
    183, 213, 243, 273, 303, 333, 363, 393,
    149, 179, 209, 239, 269, 299, 329, 359,
    115, 145, 175, 205, 235, 265, 295, 325,
    81, 111, 141, 171, 201, 231, 261, 291,
    47, 77, 107, 137, 167, 197, 227, 257,
]

# Color mapping for PCB code characters
PCB_COLORS: dict[str, tuple[int, int, int]] = {
    "w": (150, 150, 150),  # white/silver
    "k": (0, 0, 0),        # black
    "b": (0, 0, 200),      # blue
    "r": (200, 0, 0),      # red
    "g": (0, 200, 0),      # green
    "y": (127, 127, 0),    # yellow
    "o": (127, 70, 0),     # orange
    "c": (0, 127, 127),    # cyan
    "m": (127, 0, 127),    # magenta
    "s": (0, 0, 0),        # space (black)
}

# Default PCB code pattern
DEFAULT_CODE: str = "sswwwwwssswyyowsswwyoywswswoyywswswyyowswwwoyywssswssswsssssssss"


def draw_pcb_string(panel: LEDPanelInterface, code: str) -> None:
    """Draw a PCB visualization code string onto the panel.

    Args:
        panel: The LED panel to draw on.
        code: A string of color codes to render. Each character maps to a color:
              w=white, k=black, b=blue, r=red, g=green, y=yellow,
              o=orange, c=cyan, m=magenta, s=space (skip)
    """
    for i, char in enumerate(code):
        if i >= len(PCB_LUT):
            break
        if char == " ":
            continue
        if char in PCB_COLORS:
            r, g, b = PCB_COLORS[char]
            panel.set_pixel(PCB_LUT[i], color_rgb(r, g, b))


# Backwards compatibility
code = DEFAULT_CODE
pcb_lut = PCB_LUT

