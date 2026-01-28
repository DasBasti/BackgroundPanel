"""LED Panel Controller for Twitch integration.

This module provides the main controller for the LED panel, handling MQTT
communication, effect management, and user LED assignments via Twitch chat.
"""

import json
import logging
import queue
import random
import re
import signal
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import paho.mqtt.client as mqtt
import requests
import webcolors

import gol
import levenshtein
import pcb_string
import text
from config import (
    DB_PATH,
    DISCO_COLORS,
    GRID_HEIGHT,
    GRID_WIDTH,
    LED_COUNT,
    MQTT_HOST,
    MQTT_KEEPALIVE,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_TOPIC_IN,
    MQTT_TOPIC_OUT,
    MQTT_USERNAME,
    PANEL_API_AUTH,
    PANEL_API_URL,
    USE_SIMULATOR,
    USER_TIMEOUT_SECONDS,
)
from interfaces import LEDPanelInterface, color_rgb
from morse import morse_translator

logger = logging.getLogger(__name__)

# Regex for matching RGB color values (0-255)
RGB_REGEX = re.compile(
    r"^!led ([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]) "
    r"([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]) "
    r"([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])$"
)


@dataclass
class EffectState:
    """State for a running effect."""

    effect_fn: Callable[[str, int], int | None]
    state: int | str


class EffectManager:
    """Manages LED effects for users."""

    def __init__(self, panel: LEDPanelInterface) -> None:
        """Initialize the effect manager.

        Args:
            panel: The LED panel to apply effects to.
        """
        self.panel = panel
        self.effects: dict[str | int, Callable[[str | int, int], int | None]] = {}
        self.state: dict[str | int, int | str] = {}

        # Effect functions
        self._effect_functions: dict[str, Callable[[str | int, int], int | None]] = {
            "blink": self._blink,
            "boom": self._boom,
            "rainbow": self._rainbow,
            "fastbow": self._fastbow,
            "morse": self._morse,
            "identify": self._identify,
            "stop": self._stop,
        }

        # Initial state generators
        self._state_generators: dict[str, Callable[[list[str]], int | str]] = {
            "blink": lambda args: random.randint(25, 100) * 2,
            "boom": lambda args: 10,
            "rainbow": lambda args: random.randint(0, 255),
            "fastbow": lambda args: random.randint(0, 255),
            "morse": lambda args: morse_translator(" ".join(args)),
            "identify": lambda args: 4,
            "stop": lambda args: 0,
        }

        # Boom animation colors (reverse order)
        self._boom_colors = [
            color_rgb(1, 1, 1),
            color_rgb(10, 10, 10),
            color_rgb(20, 20, 20),
            color_rgb(40, 40, 40),
            color_rgb(70, 70, 70),
            color_rgb(130, 130, 130),
            color_rgb(190, 190, 190),
            color_rgb(255, 255, 255),
            color_rgb(255, 255, 255),
            color_rgb(255, 255, 255),
        ]

    @property
    def available_effects(self) -> list[str]:
        """Get list of available effect names."""
        return list(self._effect_functions.keys())

    def register_effect(self, username: str | int, effect_name: str, args: list[str]) -> bool:
        """Register an effect for a user.

        Args:
            username: The username to register the effect for.
            effect_name: Name of the effect to register.
            args: Arguments for effect initialization.

        Returns:
            True if effect was registered, False if effect name unknown.
        """
        if effect_name not in self._effect_functions:
            return False

        self.effects[username] = self._effect_functions[effect_name]
        self.state[username] = self._state_generators[effect_name](args)
        return True

    def remove_effect(self, username: str | int) -> None:
        """Remove an effect from a user."""
        self.effects.pop(username, None)
        self.state.pop(username, None)

    def apply_effect(self, username: str | int, color: int) -> int | None:
        """Apply the registered effect for a user.

        Args:
            username: The username to apply the effect for.
            color: The base color of the LED.

        Returns:
            The modified color, or None if effect should stop.
        """
        if username not in self.effects:
            return color

        return self.effects[username](username, color)

    def party_map(self, led_index: int) -> None:
        """Map a random effect to an LED for party mode."""
        effect_names = [n for n in self._effect_functions.keys() if n != "stop"]
        effect_name = random.choice(effect_names)
        self.register_effect(led_index, effect_name, ["party"])

    def _rainbow_table(self, pos: int, brightness: int = 1) -> int:
        """Generate rainbow color from position.

        Args:
            pos: Position on rainbow (0-255).
            brightness: Brightness divisor.

        Returns:
            RGB color value.
        """
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos * 3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos * 3)
            g = 0
            b = int(pos * 3)
        else:
            pos -= 170
            r = 0
            g = int(pos * 3)
            b = int(255 - pos * 3)
        return color_rgb(int(r / brightness), int(g / brightness), int(b / brightness))

    def _blink(self, username: str | int, color: int) -> int:
        """Blink effect - alternates LED on/off."""
        if state_val := self.state.get(username, 0):
            if isinstance(state_val, int):
                if state_val % 2:
                    color = color_rgb(1, 1, 1)
                self.state[username] = state_val - 1
                if self.state[username] == 0:
                    self.remove_effect(username)
        return color

    def _boom(self, username: str | int, color: int) -> int:
        """Boom effect - explosion animation."""
        if state_val := self.state.get(username, 0):
            if isinstance(state_val, int) and state_val > 0:
                color = self._boom_colors[state_val - 1]
                self.state[username] = state_val - 1
                if self.state[username] == 0:
                    self.remove_effect(username)
        return color

    def _rainbow(self, username: str | int, color: int) -> int:
        """Rainbow effect - cycles through colors."""
        if isinstance(self.state.get(username), int):
            pos = self.state[username]
            if pos < 255:
                self.state[username] = pos + 1
            else:
                self.state[username] = 0
            return self._rainbow_table(self.state[username])
        return color

    def _fastbow(self, username: str | int, color: int) -> int:
        """Fast rainbow effect - 10x faster cycle."""
        if isinstance(self.state.get(username), int):
            pos = self.state[username]
            if pos < 245:
                self.state[username] = pos + 10
            else:
                self.state[username] = 0
            return self._rainbow_table(self.state[username])
        return color

    def _morse(self, username: str | int, color: int) -> int | None:
        """Morse code effect - blinks LED in morse pattern."""
        if morse_str := self.state.get(username):
            if isinstance(morse_str, str) and len(morse_str) > 1:
                self.state[username] = morse_str[1:]
                return color if morse_str[1] == "x" else color_rgb(0, 0, 0)
            else:
                self.remove_effect(username)
        return color

    def _identify(self, username: str | int, color: int) -> int:
        """Identify effect - same as blink with fixed count."""
        return self._blink(username, color)

    def _stop(self, username: str | int, color: int) -> int:
        """Stop effect - removes effect immediately."""
        self.remove_effect(username)
        return color


class DatabaseManager:
    """Manages SQLite database for LED assignments."""

    def __init__(self, db_path: Path) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(str(db_path), check_same_thread=False)
        self.cursor = self.connection.cursor()
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS "leds" (
                "id" INTEGER NOT NULL UNIQUE,
                "owner" TEXT UNIQUE,
                "color" INTEGER,
                "lastSeen" TEXT,
                PRIMARY KEY("id")
            );"""
        )
        # Fill database with LED entries
        for led_id in range(LED_COUNT):
            self.cursor.execute(
                "INSERT OR IGNORE INTO leds VALUES(?, NULL, ?, ?)", (led_id, "", "")
            )
        self.connection.commit()

    def get_user_led(self, username: str) -> tuple[int, str | None, int | None, str | None] | None:
        """Get LED assignment for a user.

        Args:
            username: The username to look up.

        Returns:
            Tuple of (id, owner, color, lastSeen) or None if not found.
        """
        self.cursor.execute("SELECT * FROM leds WHERE owner=?;", (username,))
        return self.cursor.fetchone()

    def assign_led(self, username: str) -> int:
        """Assign an LED to a user.

        Args:
            username: The username to assign an LED to.

        Returns:
            The LED ID assigned.
        """
        # Check if user already has an LED
        existing = self.get_user_led(username)
        if existing:
            return existing[0]

        # Get random unassigned LED
        self.cursor.execute("SELECT * FROM leds WHERE owner IS NULL ORDER BY RANDOM();")
        led = self.cursor.fetchone()

        if led is None:
            # No free LEDs, take oldest one
            self.cursor.execute("SELECT * FROM leds ORDER BY lastSeen ASC LIMIT 1;")
            led = self.cursor.fetchone()
            logger.info(f"Reassigning LED from {led[1]} to {username}")

        self.cursor.execute("UPDATE leds SET owner=? WHERE id=?", (username, led[0]))
        return led[0]

    def update_user(
        self, username: str, color: int | None = None, update_timestamp: bool = True
    ) -> int:
        """Update user's LED entry.

        Args:
            username: The username to update.
            color: New color value (optional).
            update_timestamp: Whether to update lastSeen timestamp.

        Returns:
            The LED ID for this user.
        """
        led_id = self.assign_led(username)

        if color is not None:
            self.cursor.execute(
                "UPDATE leds SET lastSeen=DATETIME('now'), color=? WHERE owner=?;",
                (color, username),
            )
        elif update_timestamp:
            self.cursor.execute(
                "UPDATE leds SET lastSeen=DATETIME('now') WHERE owner=?;", (username,)
            )

        self.connection.commit()
        return led_id

    def delete_user(self, username: str) -> None:
        """Remove user from LED assignment."""
        self.cursor.execute(
            "UPDATE leds SET owner=NULL, color=NULL, lastSeen=NULL WHERE owner=?;",
            (username,),
        )
        self.connection.commit()

    def get_led_id(self, username: str) -> int | None:
        """Get LED ID for a username."""
        self.cursor.execute("SELECT id FROM leds WHERE owner=?;", (username,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_active_leds(self, include_expired: bool = False) -> list[tuple]:
        """Get all active LEDs.

        Args:
            include_expired: If True, include LEDs past timeout.

        Returns:
            List of LED tuples.
        """
        if include_expired:
            self.cursor.execute("SELECT * FROM leds WHERE owner IS NOT NULL;")
        else:
            self.cursor.execute(
                f"SELECT * FROM leds WHERE owner IS NOT NULL "
                f"AND lastSeen > DATETIME('now', '-{USER_TIMEOUT_SECONDS} seconds');"
            )
        return self.cursor.fetchall()

    def get_all_leds(self) -> list[tuple]:
        """Get all LEDs for export."""
        self.cursor.execute("SELECT * FROM leds;")
        return self.cursor.fetchall()

    def commit(self) -> None:
        """Commit pending changes."""
        self.connection.commit()


class MQTTHandler:
    """Handles MQTT communication."""

    def __init__(self, controller: "LEDPanelController") -> None:
        """Initialize MQTT handler.

        Args:
            controller: The main controller instance.
        """
        self.controller = controller
        self.client = mqtt.Client()
        self.message_queue: queue.Queue[str] = queue.Queue()
        self._running = False
        self._send_thread: threading.Thread | None = None

    def connect(self) -> None:
        """Connect to MQTT broker."""
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
        self.client.subscribe(MQTT_TOPIC_IN)
        logger.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")

    def start_send_thread(self) -> None:
        """Start the message sending thread."""
        self._running = True
        self._send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._send_thread.start()

    def stop(self) -> None:
        """Stop MQTT handler."""
        self._running = False
        if self._send_thread:
            self._send_thread.join(timeout=2)

    def queue_message(self, message: str) -> None:
        """Queue a message for sending."""
        self.message_queue.put(message)

    def loop(self) -> None:
        """Process MQTT events (call in main loop)."""
        self.client.loop()

    def _send_loop(self) -> None:
        """Background thread for sending queued messages."""
        while self._running:
            try:
                message = self.message_queue.get(timeout=0.1)
                self.client.publish(MQTT_TOPIC_OUT, payload=message)
                time.sleep(1)  # Rate limit
            except queue.Empty:
                continue

    def _on_connect(
        self, client: mqtt.Client, userdata: object, flags: dict, rc: int
    ) -> None:
        """Callback when connected to broker."""
        logger.info("MQTT connected")

    def _on_message(
        self, client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage
    ) -> None:
        """Callback when message received."""
        if not msg.payload:
            return

        try:
            data = json.loads(msg.payload)
            username = data.get("username", "").lower()
            chat_text = data.get("message", "").lower()
            display_name = data.get("username", username)

            self.controller.handle_chat_message(username, chat_text, display_name)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MQTT message: {e}")
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")


class LEDPanelController:
    """Main controller for the LED panel system."""

    def __init__(self, panel: LEDPanelInterface) -> None:
        """Initialize the controller.

        Args:
            panel: The LED panel interface to use.
        """
        self.panel = panel
        self.db = DatabaseManager(DB_PATH)
        self.effects = EffectManager(panel)
        self.mqtt = MQTTHandler(self)

        # Mode flags
        self.discomode = 0
        self.partymode = 0
        self.game_of_life = False
        self.static_image = False

        # Disco colors
        self._disco_colors = [color_rgb(r, g, b) for r, g, b in DISCO_COLORS]

        # Running state
        self._running = False
        self._display_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the controller."""
        self._running = True

        # Initialize panel
        self.panel.init()
        self.panel.display()

        # Connect MQTT
        self.mqtt.connect()
        self.mqtt.start_send_thread()

        # Start display thread
        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()

        logger.info("LED Panel Controller started")

    def stop(self) -> None:
        """Stop the controller."""
        self._running = False
        self.db.commit()
        self.mqtt.stop()
        if self._display_thread:
            self._display_thread.join(timeout=2)
        logger.info("LED Panel Controller stopped")

    def run(self) -> None:
        """Main loop - process MQTT messages."""
        while self._running:
            self.mqtt.loop()

    def handle_chat_message(
        self, username: str, chat_text: str, display_name: str
    ) -> None:
        """Handle an incoming chat message.

        Args:
            username: Lowercase username.
            chat_text: Lowercase message text.
            display_name: Original display name for responses.
        """
        if not chat_text.startswith("!led"):
            # Just update user timestamp
            self.db.update_user(username)
            return

        # Parse command
        command = chat_text[5:].strip() if len(chat_text) > 4 else ""
        cmd_parts = command.split(" ") if command else []

        # Check for RGB values
        rgb_match = RGB_REGEX.findall(chat_text)
        if rgb_match:
            r, g, b = int(rgb_match[0][0]), int(rgb_match[0][1]), int(rgb_match[0][2])
            self.db.update_user(username, color_rgb(r, g, b))
            self.effects.remove_effect(username)
            return

        # Handle specific commands
        if command.startswith("off"):
            self.db.update_user(username, color_rgb(1, 1, 1))
            return

        if command.startswith("info") or command.startswith("status"):
            led_id = self.db.update_user(username)
            self._send_led_info(display_name, led_id)
            return

        if command.startswith("random"):
            r, g, b = random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)
            self.db.update_user(username, color_rgb(r, g, b))
            self.mqtt.queue_message(
                f"@{display_name} deine LED leuchtet jetzt in ({r} {g} {b})RGB"
            )
            return

        if command.startswith("dsgvo"):
            self.db.delete_user(username)
            self.mqtt.queue_message(
                f"@{display_name} dein Name wurde aus der LED Tabelle entfernt"
            )
            return

        # Check for effect commands
        if cmd_parts and cmd_parts[0] in self.effects.available_effects:
            self.db.update_user(username)
            self.effects.register_effect(username, cmd_parts[0], cmd_parts[1:])
            return

        # Try CSS3 color name
        if cmd_parts:
            try:
                col = webcolors.name_to_rgb(cmd_parts[0])
                self.db.update_user(username, color_rgb(col.red, col.green, col.blue))
                self.effects.remove_effect(username)
                return
            except ValueError:
                pass

        # Try hex color
        if command.startswith("#"):
            try:
                col = webcolors.hex_to_rgb(cmd_parts[0])
                self.db.update_user(username, color_rgb(col.red, col.green, col.blue))
                self.effects.remove_effect(username)
                return
            except ValueError as e:
                self.mqtt.queue_message(f"@{display_name} {e}")
                return

        # Special modes
        if command.startswith("disco") or command.startswith("disko"):
            self.discomode = 10
            return

        if command.startswith("party"):
            self.partymode = 100
            for c in range(LED_COUNT):
                self.effects.party_map(c)
            return

        if command == "gol":
            if not self.game_of_life:
                self.game_of_life = True
                gol.init()
            return

        # Help or empty command
        if not command or command.startswith("help") or command.startswith("?"):
            self._send_help(display_name)
            return

        # Fuzzy color matching via Levenshtein distance
        if cmd_parts:
            best_distance = 0.0
            best_color = ""
            for css3_color in levenshtein.CSS3_COLORS:
                dist = levenshtein.levenshtein_ratio_and_distance(
                    css3_color.lower(), cmd_parts[0], ratio_calc=True
                )
                if isinstance(dist, float) and dist > best_distance:
                    best_distance = dist
                    best_color = css3_color

            if best_distance > 0.6:
                self.mqtt.queue_message(
                    f"@{display_name} Ich habe für dich die Farbe {best_color} ausgesucht."
                )
                col = webcolors.name_to_rgb(best_color)
                self.db.update_user(username, color_rgb(col.red, col.green, col.blue))
                return

        # Nothing matched
        self._send_help(display_name)

    def _send_led_info(self, display_name: str, led_id: int) -> None:
        """Send LED position info to user."""
        x = (led_id // GRID_HEIGHT) + 1
        y = (led_id % GRID_HEIGHT) + 1
        self.mqtt.queue_message(
            f"@{display_name} deine LED ist Nr. {led_id} und befindet sich auf {x}/{y}."
        )

    def _send_help(self, display_name: str) -> None:
        """Send help message to user."""
        self.mqtt.queue_message(
            f"@{display_name} du findest die LED Funktionen im Beschreibungstext."
        )

    def _update_panel(self) -> None:
        """Update the panel display."""
        self.panel.clear()

        if self.discomode > 0:
            # Disco mode - random colors
            for led in range(LED_COUNT):
                self.panel.set_pixel(led, random.choice(self._disco_colors))
            self.discomode -= 1
        else:
            # Normal mode - show user LEDs
            active_leds = self.db.get_active_leds(include_expired=self.partymode > 0)

            for led in active_leds:
                led_id, owner, color, _ = led
                if owner and color:
                    current_color = color

                    # Apply user effect
                    if owner in self.effects.effects:
                        result = self.effects.apply_effect(owner, color)
                        if result is not None:
                            current_color = result

                    # Apply party mode effect (by LED ID)
                    elif self.partymode and led_id in self.effects.effects:
                        result = self.effects.apply_effect(led_id, color)
                        if result is not None:
                            current_color = result

                    self.panel.set_pixel(led_id, current_color)

        if self.partymode > 0:
            self.partymode -= 1

        self.panel.display()

    def _display_loop(self) -> None:
        """Background thread for updating display."""
        while self._running:
            if self.static_image:
                time.sleep(0.1)
                continue

            if self.game_of_life:
                gol.run()
                gol.display()
                if not gol.running:
                    self.game_of_life = False
                time.sleep(0.1)
            else:
                self._update_panel()
                time.sleep(0.1 if self.discomode == 0 else 1)

    def _sync_to_api(self) -> None:
        """Sync panel data to external API."""
        panel_data = []
        for led in self.db.get_all_leds():
            panel_data.append({
                "id": led[0],
                "owner": led[1],
                "color": led[2],
                "last_seen": led[3],
            })

        try:
            requests.post(
                PANEL_API_URL,
                data={"data": json.dumps(panel_data), "auth": PANEL_API_AUTH},
                timeout=5,
            )
        except requests.RequestException as e:
            logger.warning(f"Failed to sync to API: {e}")


def create_panel() -> LEDPanelInterface:
    """Create the appropriate panel based on configuration."""
    if USE_SIMULATOR:
        from simulator import TerminalPanel
        return TerminalPanel()
    else:
        from hardware import WS2812Panel
        return WS2812Panel()


def main() -> None:
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    panel = create_panel()
    controller = LEDPanelController(panel)

    def signal_handler(signum: int, frame: object) -> None:
        logger.info("Received shutdown signal")
        controller.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    controller.start()

    try:
        controller.run()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()


if __name__ == "__main__":
    main()
