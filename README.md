# FollowerPanel

Twitch-integrated LED panel controller for WS2812 LEDs (32×32 grid = 1024 LEDs). Runs on Raspberry Pi, receives chat commands via MQTT, and allows Twitch viewers to claim and control individual LEDs on a physical panel during Platinenmacher streams.

## Architecture

```
MQTT (chat/in) → LEDPanelController → LEDPanelInterface → WS2812Panel (hardware)
                        ↓                    ↓
                  DatabaseManager      TerminalPanel (simulator)
                   (SQLite)
```

## Requirements

- Python 3.10+
- Raspberry Pi (for hardware mode) with root access for GPIO/DMA
- Any platform with 24-bit color terminal support (for simulator mode)

## Installation

### Basic Installation

```bash
# Clone the repository
git clone <repository-url>
cd followerpanel

# Install the package with dependencies
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies (ruff, mypy, pytest)
pip install -e ".[dev]"
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `rpi-ws281x` | WS2812 LED hardware driver |
| `paho-mqtt` | MQTT client for Twitch chat integration |
| `webcolors` | CSS3 color name parsing |
| `Pillow` | Image processing (text rendering) |
| `requests` | HTTP requests to external API |
| `numpy` | Array operations |

## Usage

### Running the Application

```bash
python controller.py
```

### Simulator Mode (Development)

For development without hardware, enable the terminal simulator:

1. Edit `config.py` and set `USE_SIMULATOR = True`
2. Run `python controller.py`

The simulator displays an ASCII representation of the LED panel in your terminal using ANSI colors.

### Hardware Mode (Raspberry Pi)

1. Ensure `USE_SIMULATOR = False` in `config.py`
2. Connect WS2812 LEDs to GPIO pin 18 (configurable in `config.py`)
3. Run with root privileges:

```bash
sudo python controller.py
```

### Configuration

All settings are in `config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_SIMULATOR` | `False` | Toggle simulator/hardware mode |
| `LED_WIDTH` | 32 | Panel width in pixels |
| `LED_HEIGHT` | 32 | Panel height in pixels |
| `LED_GPIO_PIN` | 18 | GPIO pin (18 uses PWM) |
| `LED_BRIGHTNESS` | 255 | Brightness (0-255) |
| `MQTT_BROKER` | 192.168.0.11 | MQTT broker address |
| `MQTT_PORT` | 1883 | MQTT broker port |
| `LED_TIMEOUT_SECONDS` | 10800 | LED inactivity timeout (3 hours) |

## Chat Commands

Users interact with the panel via Twitch chat commands:

| Command | Description |
|---------|-------------|
| `!led off` | Turn LED off |
| `!led R G B` | Set color with RGB values (0-255 each) |
| `!led <colorname>` | Set color by CSS3 name (fuzzy matched) |
| `!led #RRGGBB` | Set color by hex code |
| `!led random` | Random color |
| `!led info` / `!led status` | Get LED position |
| `!led run <effect>` | Start an effect |
| `!deleteme` | Delete user data (GDPR) |
| `!gol` | Start Conway's Game of Life |
| `!party` | Disco party mode |
| `!partyhard` | Party mode with effects |
| `!led help` / `!led ?` | Show help |

### Available Effects

- `blink` - Blinking effect
- `boom` - Explosion animation
- `rainbow` - Slow rainbow cycle
- `fastbow` - Fast rainbow cycle
- `morse <text>` - Flash text in Morse code
- `identify` - Identify LED position
- `stop` - Stop current effect

## Development

### Code Style

The project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Type Checking

The project uses [mypy](https://mypy-lang.org/) for static type checking:

```bash
mypy .
```

### Project Structure

| File | Purpose |
|------|---------|
| `controller.py` | Main entry point, MQTT handling, command parsing |
| `interfaces.py` | `LEDPanelInterface` Protocol + color helpers |
| `hardware.py` | Physical WS2812 driver with serpentine coordinate mapping |
| `simulator.py` | Terminal ASCII simulator for development |
| `config.py` | All configuration constants |
| `gol.py` | Conway's Game of Life mode |
| `morse.py` | Morse code translation for LED effects |
| `text.py` | Text/username scrolling renderer |
| `levenshtein.py` | Fuzzy CSS3 color name matching |

### Color Handling

WS2812 LEDs use GRB byte order internally. Always use the helper functions:

```python
from interfaces import color_rgb, color_to_rgb

# Create a color (handles GRB conversion)
red = color_rgb(255, 0, 0)

# Extract RGB components
r, g, b = color_to_rgb(red)
```

## Testing

Tests are located in the `tests/` directory and use pytest:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_hardware.py

# Run with coverage report
pytest --cov
```

### Writing Tests

Tests import modules inside test functions to avoid hardware dependencies:

```python
def test_example(self) -> None:
    from hardware import WS2812Panel
    panel = WS2812Panel()
    # ...
```

## License

See LICENSE file for details.