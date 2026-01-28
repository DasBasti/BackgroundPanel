"""Conway's Game of Life implementation for LED panel.

This module provides a colorful Game of Life simulation that runs
on the LED panel with color inheritance between cells.
"""

from __future__ import annotations

import math
import random

from config import GOL_AGING, GOL_INHERIT, GRID_HEIGHT, GRID_WIDTH, LED_COUNT
from interfaces import LEDPanelInterface, color_rgb, color_to_rgb


class GameOfLife:
    """Conway's Game of Life with color inheritance."""

    def __init__(self, panel: LEDPanelInterface) -> None:
        """Initialize Game of Life.

        Args:
            panel: The LED panel to render to.
        """
        self.panel = panel
        self.field: list[int] = [0] * LED_COUNT
        self.aging = GOL_AGING
        self.inherit = GOL_INHERIT
        self.running = False
        self._width = GRID_WIDTH
        self._height = GRID_HEIGHT

    def _add_color(self, c1: int, c2: int) -> int:
        """Mix two colors with inheritance factor.

        Args:
            c1: First color value.
            c2: Second color value.

        Returns:
            Mixed color value.
        """
        r1, g1, b1 = color_to_rgb(c1)
        r2, g2, b2 = color_to_rgb(c2)
        inherit_factor = self.inherit + random.randint(0, 2) / 10
        return color_rgb(
            min(255, math.floor((r1 + r2) / inherit_factor)),
            min(255, math.floor((g1 + g2) / inherit_factor)),
            min(255, math.floor((b1 + b2) / inherit_factor)),
        )

    def init(self) -> None:
        """Initialize the field with random cells."""
        self.running = True
        initial_colors = [
            color_rgb(200, 0, 0),
            color_rgb(0, 200, 0),
            color_rgb(0, 0, 200),
            color_rgb(100, 100, 100),
        ]
        for cell in range(LED_COUNT):
            if random.randint(0, 10) > 4:
                self.field[cell] = random.choice(initial_colors)
            else:
                self.field[cell] = 0

    def _get_neighbors(self, x: int, y: int) -> tuple[int, int]:
        """Count neighbors and calculate inherited color.

        Args:
            x: X coordinate of cell.
            y: Y coordinate of cell.

        Returns:
            Tuple of (neighbor_count, inherited_color).
        """
        neighbors = 0
        new_cell = 0

        # Check all 8 neighboring cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self._width and 0 <= ny < self._height:
                    neighbor_color = self.field[nx * self._height + ny]
                    if neighbor_color:
                        neighbors += 1
                        new_cell = self._add_color(new_cell, neighbor_color)

        return neighbors, new_cell

    def run(self) -> None:
        """Execute one generation of the simulation."""
        new_field: list[int] = [0] * LED_COUNT

        for x in range(self._width):
            for y in range(self._height):
                idx = x * self._height + y
                alive = self.field[idx]
                neighbors, new_cell = self._get_neighbors(x, y)

                # Game of Life rules:
                if alive and neighbors < 2:
                    # Underpopulation - cell dies
                    new_field[idx] = 0
                elif alive and neighbors <= 3:
                    # Survival - cell lives but ages
                    r, g, b = color_to_rgb(self.field[idx])
                    new_field[idx] = color_rgb(
                        max(0, r - self.aging),
                        max(0, g - self.aging),
                        max(0, b - self.aging),
                    )
                elif alive and neighbors > 3:
                    # Overpopulation - cell dies
                    new_field[idx] = 0
                elif not alive and neighbors == 3:
                    # Reproduction - new cell born
                    r, g, b = color_to_rgb(new_cell)
                    new_field[idx] = color_rgb(r, g, b)

        self.field = new_field.copy()

        # Stop if all cells are dead
        if not any(new_field):
            self.running = False

    def display(self) -> None:
        """Render the current field to the panel."""
        self.panel.clear()
        self.panel.set_pixels(self.field.copy())
        self.panel.display()


# Backwards compatibility layer
# TODO: Remove after full refactor

field: list[int] = [0] * LED_COUNT
aging = GOL_AGING
inherit = GOL_INHERIT
running = True

_legacy_gol: GameOfLife | None = None


def _get_legacy_gol() -> GameOfLife:
    """Get or create legacy GameOfLife instance."""
    global _legacy_gol
    if _legacy_gol is None:
        # Import here to avoid circular import during transition
        from config import USE_SIMULATOR

        if USE_SIMULATOR:
            import simulator as legacy_panel
        else:
            import panel as legacy_panel

        # Create a wrapper that bridges old panel to new interface
        class LegacyPanelWrapper:
            @property
            def width(self) -> int:
                return GRID_WIDTH

            @property
            def height(self) -> int:
                return GRID_HEIGHT

            @property
            def pixel_count(self) -> int:
                return LED_COUNT

            def init(self) -> None:
                legacy_panel.init_strip()

            def display(self) -> None:
                legacy_panel.display()

            def clear(self) -> None:
                legacy_panel.clear()

            def set_pixel(self, index: int, color: int) -> None:
                legacy_panel.panel[index] = color

            def get_pixel(self, index: int) -> int:
                return legacy_panel.panel[index]

            def set_pixels(self, pixels: list[int]) -> None:
                legacy_panel.panel[:] = pixels

            def get_pixels(self) -> list[int]:
                return legacy_panel.panel.copy()

            def set_pixel_xy(self, x: int, y: int, color: int) -> None:
                legacy_panel.panel[x * GRID_HEIGHT + y] = color

            def get_pixel_xy(self, x: int, y: int) -> int:
                return legacy_panel.panel[x * GRID_HEIGHT + y]

        _legacy_gol = GameOfLife(LegacyPanelWrapper())  # type: ignore
    return _legacy_gol


def init() -> None:
    """Initialize Game of Life (backwards compatibility)."""
    global field, running
    gol = _get_legacy_gol()
    gol.init()
    field = gol.field
    running = gol.running


def run() -> None:
    """Run one generation (backwards compatibility)."""
    global field, running
    gol = _get_legacy_gol()
    gol.field = field
    gol.run()
    field = gol.field
    running = gol.running


def display() -> None:
    """Display the field (backwards compatibility)."""
    gol = _get_legacy_gol()
    gol.field = field
    gol.display()


if __name__ == "__main__":
    import time

    import panel

    panel.init_strip()

    for c in range(LED_COUNT):
        if random.randint(0, 10) > 4:
            panel.panel[c] = color_rgb(
                random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)
            )

    init()
    while running:
        run()
        display()
        time.sleep(0.1)
