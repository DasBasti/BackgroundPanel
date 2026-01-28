# Copilot Instructions for FollowerPanel

## Project Overview

Twitch-integrated LED panel controller for WS2812 LEDs (32x32 grid = 1024 LEDs). Runs on Raspberry Pi, receives chat commands via MQTT, and allows Twitch viewers to claim and control individual LEDs on a physical panel during Platinenmacher streams.

## Architecture

```
MQTT (chat/in) → LEDPanelController → LEDPanelInterface → WS2812Panel (hardware)
                        ↓                    ↓
                  DatabaseManager      TerminalPanel (simulator)
                   (SQLite)
```

- **controller.py**: Main entry point (`python controller.py`). Handles MQTT, command parsing, effect management, and display loop
- **interfaces.py**: `LEDPanelInterface` Protocol - abstraction layer enabling hardware/simulator swap
- **hardware.py**: `WS2812Panel` - physical LED driver with serpentine coordinate mapping LUT
- **simulator.py**: `TerminalPanel` - ANSI color terminal simulator for development without hardware
- **config.py**: All constants (grid size, MQTT settings, GPIO pins). Toggle `USE_SIMULATOR = True` for local dev

## Key Patterns

### Hardware Abstraction
Use `LEDPanelInterface` Protocol for panel operations. Implementations:
- `WS2812Panel`: Real hardware (requires rpi_ws281x, root on RPi)
- `TerminalPanel`: Development simulator

```python
# Color format is GRB internally (WS2812 native), use helper functions:
from interfaces import color_rgb, color_to_rgb
color = color_rgb(255, 0, 0)  # Creates red (handles GRB conversion)
r, g, b = color_to_rgb(color)  # Extracts RGB components
```

### Serpentine LED Mapping
Physical LEDs are wired in a serpentine pattern across 4 horizontal strips of 8 rows each. The `_coordinate_lut` in `hardware.py` maps logical (x,y) to physical LED index. Don't calculate manually—use `set_pixel_xy()`.

### Effect System
Effects in `EffectManager` are registered per-user and applied each frame:
```python
# Available: blink, boom, rainbow, fastbow, morse, identify, stop
effects.register_effect(username, "rainbow", [])
```
State is tracked in `EffectManager.state` dict (int or str depending on effect).

## Commands & Workflows

### Development
```bash
# Run with simulator (no hardware needed)
# Set USE_SIMULATOR = True in config.py first
python controller.py

# Run tests
pytest

# Lint
ruff check .
mypy .
```

### Chat Commands (via MQTT)
- `!led off` - Turn user's LED off
- `!led R G B` - Set color (0-255 each)
- `!led <colorname>` - CSS3 color names (fuzzy matched via Levenshtein)
- `!led info` - Get LED position
- `!led run <effect>` - Start effect (blink/boom/rainbow/morse/etc.)

## File Roles

| File | Purpose |
|------|---------|
| `controller.py` | Main controller, MQTT handling, entry point |
| `interfaces.py` | `LEDPanelInterface` Protocol + color helpers |
| `hardware.py` | Physical WS2812 driver with coordinate LUT |
| `simulator.py` | Terminal ASCII simulator |
| `config.py` | All configuration constants |
| `gol.py` | Conway's Game of Life mode |
| `morse.py` | Morse code translation for LED effects |
| `text.py` | Text/username scrolling renderer |
| `levenshtein.py` | Fuzzy CSS3 color name matching |
| `pcb_string.py` | PCB visualization overlay |
| `followerleds.py` | Legacy monolithic version (deprecated) |

## Testing Conventions

- Tests in `tests/` directory, named `test_<module>.py`
- Use pytest with type hints
- Import modules inside test functions to avoid hardware dependencies:
  ```python
  def test_example(self) -> None:
      from hardware import WS2812Panel
      panel = WS2812Panel()
  ```

## Important Notes

- **GRB Color Format**: WS2812 uses GRB byte order. Always use `color_rgb()`/`color_to_rgb()` helpers
- **Root Required**: Physical hardware needs root access for GPIO/DMA on Raspberry Pi
- **Legacy Code**: `followerleds.py` and `panel.py` are legacy files being refactored into the new architecture
- **SQLite Thread Safety**: `DatabaseManager` uses `check_same_thread=False` for multi-threaded access
