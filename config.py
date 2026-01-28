"""Centralized configuration for the LED panel controller."""

from __future__ import annotations

from pathlib import Path

# Panel dimensions
GRID_WIDTH: int = 32
GRID_HEIGHT: int = 32
LED_COUNT: int = GRID_WIDTH * GRID_HEIGHT  # 1024

# Hardware settings (WS2812)
LED_PIN: int = 18  # GPIO pin (18 uses PWM)
LED_FREQ_HZ: int = 800000  # LED signal frequency in hertz
LED_DMA: int = 10  # DMA channel for generating signal
LED_BRIGHTNESS: int = 255  # 0 (darkest) to 255 (brightest)
LED_INVERT: bool = False  # True to invert signal (NPN transistor level shift)
LED_CHANNEL: int = 0  # Set to 1 for GPIOs 13, 19, 41, 45 or 53

# Panel mode selection
USE_SIMULATOR: bool = True  # Set True to use terminal simulator instead of hardware

# MQTT settings
MQTT_HOST: str = "192.168.0.11"
MQTT_PORT: int = 1883
MQTT_KEEPALIVE: int = 60
MQTT_USERNAME: str = "panel"
MQTT_PASSWORD: str = "panel"
MQTT_TOPIC_IN: str = "chat/in"
MQTT_TOPIC_OUT: str = "chat/out"

# Database settings
DB_PATH: Path = Path(__file__).parent / "led.db"

# API settings
PANEL_API_URL: str = "https://platinenmacher.tech/pcb/panel/dumps"
PANEL_API_AUTH: str = "123"

# Display settings
USER_TIMEOUT_SECONDS: int = 10800  # 3 hours - LEDs fade after this time of inactivity

# Font settings
FONT_PATH: Path = Path(__file__).parent / "osifont.ttf"
FONT_SIZE: int = 14

# Disco mode colors (RGB values)
DISCO_COLORS: list[tuple[int, int, int]] = [
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (50, 0, 0),
    (0, 50, 0),
    (0, 0, 50),
    (30, 30, 30),
]

# Game of Life settings
GOL_AGING: int = 10
GOL_INHERIT: float = 1.5
