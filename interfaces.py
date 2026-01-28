"""Hardware abstraction layer interfaces for LED panel."""

from typing import Protocol


class LEDPanelInterface(Protocol):
    """Protocol defining the interface for LED panel implementations.
    
    This abstraction allows switching between hardware (WS2812) and 
    simulator implementations without changing application code.
    """

    @property
    def width(self) -> int:
        """Grid width in pixels."""
        ...

    @property
    def height(self) -> int:
        """Grid height in pixels."""
        ...

    @property
    def pixel_count(self) -> int:
        """Total number of pixels (width * height)."""
        ...

    def init(self) -> None:
        """Initialize the panel hardware/simulator."""
        ...

    def display(self) -> None:
        """Push the current pixel buffer to the display."""
        ...

    def clear(self) -> None:
        """Clear all pixels (set to black)."""
        ...

    def set_pixel(self, index: int, color: int) -> None:
        """Set a single pixel by linear index.
        
        Args:
            index: Linear index (0 to pixel_count-1)
            color: 24-bit RGB color value (0xRRGGBB format)
        """
        ...

    def get_pixel(self, index: int) -> int:
        """Get the color of a pixel by linear index.
        
        Args:
            index: Linear index (0 to pixel_count-1)
            
        Returns:
            24-bit RGB color value
        """
        ...

    def set_pixel_xy(self, x: int, y: int, color: int) -> None:
        """Set a single pixel by x,y coordinates.
        
        Args:
            x: X coordinate (0 to width-1)
            y: Y coordinate (0 to height-1)
            color: 24-bit RGB color value
        """
        ...

    def get_pixel_xy(self, x: int, y: int) -> int:
        """Get the color of a pixel by x,y coordinates.
        
        Args:
            x: X coordinate (0 to width-1)
            y: Y coordinate (0 to height-1)
            
        Returns:
            24-bit RGB color value
        """
        ...

    def set_pixels(self, pixels: list[int]) -> None:
        """Set all pixels from a list of color values.
        
        Args:
            pixels: List of pixel_count color values
        """
        ...

    def get_pixels(self) -> list[int]:
        """Get a copy of all pixel values.
        
        Returns:
            List of pixel_count color values
        """
        ...


def color_rgb(r: int, g: int, b: int) -> int:
    """Create a 24-bit color value from RGB components.
    
    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        
    Returns:
        24-bit color value in RGB format (0xRRGGBB)
    """
    return (r << 16) | (g << 8) | b


def color_to_rgb(color: int) -> tuple[int, int, int]:
    """Extract RGB components from a 24-bit color value.
    
    Args:
        color: 24-bit color value in RGB format
        
    Returns:
        Tuple of (red, green, blue) components
    """
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return (r, g, b)
