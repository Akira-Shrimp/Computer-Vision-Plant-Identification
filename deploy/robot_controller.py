"""
Robot Controller — Manages serial communication with the harvesting robot arm.
Features: auto-reconnect, command queue, boundary safety, simulation mode.
"""

import serial
import time
import logging
import threading
from collections import deque

logger = logging.getLogger("plant_vision.robot")


class RobotController:
    """Controls the robotic harvesting arm via serial communication."""

    def __init__(self, settings):
        self.settings = settings
        self.serial_conn = None
        self.connected = False
        self.simulation = settings.ROBOT_SIMULATION
        self.command_queue = deque(maxlen=100)
        self._lock = threading.Lock()
        self._last_command_time = 0

        # Stats
        self.commands_sent = 0
        self.last_command = None
        self.last_coordinates = None

        if not self.simulation:
            self._connect()

    # ── Connection Management ─────────────────────────────────

    def _connect(self):
        """Establish serial connection to the robot controller."""
        try:
            self.serial_conn = serial.Serial(
                port=self.settings.SERIAL_PORT,
                baudrate=self.settings.SERIAL_BAUD,
                timeout=self.settings.SERIAL_TIMEOUT,
            )
            time.sleep(2)  # Wait for board to initialize
            self.connected = True
            logger.info(
                f"Connected to robot on {self.settings.SERIAL_PORT} "
                f"@ {self.settings.SERIAL_BAUD} baud"
            )
        except Exception as e:
            logger.warning(f"Cannot connect to robot: {e}")
            self.connected = False
            self.serial_conn = None

    def reconnect(self):
        """Attempt to reconnect to the robot."""
        logger.info("Attempting to reconnect to robot...")
        self.disconnect()
        time.sleep(1)
        self._connect()
        return self.connected

    def disconnect(self):
        """Safely close the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")
        self.connected = False
        self.serial_conn = None
        logger.info("Robot disconnected")

    # ── Safety Checks ─────────────────────────────────────────

    def _is_within_bounds(self, x, y, z=None):
        """Check if coordinates are within safe operating boundaries."""
        min_x, max_x = self.settings.ROBOT_BOUNDARY_X
        min_y, max_y = self.settings.ROBOT_BOUNDARY_Y

        if not (min_x <= x <= max_x):
            logger.warning(f"X={x} out of bounds [{min_x}, {max_x}]")
            return False
        if not (min_y <= y <= max_y):
            logger.warning(f"Y={y} out of bounds [{min_y}, {max_y}]")
            return False
        return True

    # ── Command Sending ───────────────────────────────────────

    def send_coordinates(self, x, y, z=None):
        """
        Send harvest coordinates to the robot arm.
        Returns True if the command was sent successfully.
        """
        x, y = int(x), int(y)

        # Safety check
        if not self._is_within_bounds(x, y, z):
            logger.error(f"Coordinates ({x}, {y}) rejected: out of bounds")
            return False

        # Rate limiting
        now = time.time()
        elapsed = now - self._last_command_time
        if elapsed < self.settings.ROBOT_COMMAND_DELAY:
            time.sleep(self.settings.ROBOT_COMMAND_DELAY - elapsed)

        # Build command string
        if z is not None:
            command = f"X{x}Y{y}Z{int(z)}\n"
        else:
            command = f"X{x}Y{y}\n"

        self.last_coordinates = {"x": x, "y": y, "z": z}
        self.last_command = command.strip()

        # Simulation mode
        if self.simulation:
            logger.info(f"[SIMULATION] Harvest command: {command.strip()}")
            self.commands_sent += 1
            self._last_command_time = time.time()
            return True

        # Real mode — send via serial
        with self._lock:
            try:
                if not self.connected or self.serial_conn is None:
                    logger.warning("Robot not connected, attempting reconnect...")
                    if not self.reconnect():
                        logger.error("Reconnect failed, command dropped")
                        return False

                self.serial_conn.write(command.encode("utf-8"))
                self.commands_sent += 1
                self._last_command_time = time.time()
                logger.info(f"Sent to robot: {command.strip()}")
                return True

            except serial.SerialException as e:
                logger.error(f"Serial error: {e}")
                self.connected = False
                return False

    def send_home(self):
        """Send the robot arm to its home position."""
        command = "HOME\n"
        self.last_command = "HOME"

        if self.simulation:
            logger.info("[SIMULATION] Robot returning to HOME")
            return True

        with self._lock:
            try:
                if self.connected and self.serial_conn:
                    self.serial_conn.write(command.encode("utf-8"))
                    logger.info("Robot returning to HOME")
                    return True
            except serial.SerialException as e:
                logger.error(f"Serial error sending HOME: {e}")
                return False
        return False

    # ── Status ────────────────────────────────────────────────

    def get_status(self):
        """Return current robot controller status."""
        return {
            "connected": self.connected,
            "simulation": self.simulation,
            "port": self.settings.SERIAL_PORT,
            "commands_sent": self.commands_sent,
            "last_command": self.last_command,
            "last_coordinates": self.last_coordinates,
        }

    def __del__(self):
        self.disconnect()
