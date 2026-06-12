"""
Centralized configuration management for the Plant Vision system.
Loads from environment variables (.env file) with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Load .env file from project root
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Central configuration for all system components."""

    def __init__(self):
        # ── Roboflow API ──────────────────────────────────────────
        self.ROBOFLOW_API_URL = os.getenv("ROBOFLOW_API_URL", "https://serverless.roboflow.com")
        self.ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "YOUR_API_KEY")
        self.ROBOFLOW_WORKFLOW = os.getenv("ROBOFLOW_WORKFLOW", "find-tomato-oohfb")
        self.ROBOFLOW_WORKSPACE = os.getenv("ROBOFLOW_WORKSPACE", "h-m-0hina")
        self.ROBOFLOW_PLAN = os.getenv("ROBOFLOW_PLAN", "webrtc-gpu-medium")
        self.ROBOFLOW_REGION = os.getenv("ROBOFLOW_REGION", "us")

        # ── Camera ────────────────────────────────────────────────
        self.CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
        self.CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "1280"))
        self.CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "720"))
        self.CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))

        # ── Detection ────────────────────────────────────────────
        self.CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
        self.TARGET_CLASSES = os.getenv("TARGET_CLASSES", "tomato_ripe,pepper_ripe").split(",")
        self.ALL_CLASSES = os.getenv(
            "ALL_CLASSES",
            "tomato_green,tomato_ripe,pepper_green,pepper_ripe"
        ).split(",")

        # ── Robot / Serial ────────────────────────────────────────
        self.SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
        self.SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "9600"))
        self.SERIAL_TIMEOUT = float(os.getenv("SERIAL_TIMEOUT", "1"))
        self.ROBOT_SIMULATION = os.getenv("ROBOT_SIMULATION", "true").lower() == "true"
        self.ROBOT_BOUNDARY_X = (
            int(os.getenv("ROBOT_MIN_X", "0")),
            int(os.getenv("ROBOT_MAX_X", "1280")),
        )
        self.ROBOT_BOUNDARY_Y = (
            int(os.getenv("ROBOT_MIN_Y", "0")),
            int(os.getenv("ROBOT_MAX_Y", "720")),
        )
        self.ROBOT_COMMAND_DELAY = float(os.getenv("ROBOT_COMMAND_DELAY", "0.5"))

        # ── Growth Tracking ───────────────────────────────────────
        self.GROWTH_CAPTURE_INTERVAL = int(os.getenv("GROWTH_CAPTURE_INTERVAL", "3600"))  # seconds
        self.GROWTH_LOG_DIR = PROJECT_ROOT / "data" / "growth_logs"
        self.GROWTH_LOG_DIR.mkdir(parents=True, exist_ok=True)

        # ── Data Collection ───────────────────────────────────────
        self.CAPTURE_DIR = PROJECT_ROOT / "data" / "captures"
        self.CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        self.AUTO_CAPTURE_INTERVAL = int(os.getenv("AUTO_CAPTURE_INTERVAL", "5"))  # seconds

        # ── Dashboard ─────────────────────────────────────────────
        self.DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        self.DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
        self.DASHBOARD_DEBUG = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"

        # ── Logging ───────────────────────────────────────────────
        self.LOG_DIR = PROJECT_ROOT / "logs"
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        # ── Paths ─────────────────────────────────────────────────
        self.DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
        self.PROJECT_ROOT = PROJECT_ROOT

    def validate(self):
        """Validate critical configuration values."""
        errors = []
        if self.ROBOFLOW_API_KEY == "YOUR_API_KEY":
            errors.append("ROBOFLOW_API_KEY is not set. Set it in .env file.")
        if self.CAMERA_WIDTH <= 0 or self.CAMERA_HEIGHT <= 0:
            errors.append(f"Invalid camera resolution: {self.CAMERA_WIDTH}x{self.CAMERA_HEIGHT}")
        if self.CONFIDENCE_THRESHOLD < 0 or self.CONFIDENCE_THRESHOLD > 1:
            errors.append(f"CONFIDENCE_THRESHOLD must be 0-1, got {self.CONFIDENCE_THRESHOLD}")
        return errors

    def __repr__(self):
        return (
            f"Settings(\n"
            f"  roboflow_workflow={self.ROBOFLOW_WORKFLOW},\n"
            f"  camera={self.CAMERA_WIDTH}x{self.CAMERA_HEIGHT}@{self.CAMERA_FPS}fps,\n"
            f"  serial={self.SERIAL_PORT}@{self.SERIAL_BAUD},\n"
            f"  simulation={self.ROBOT_SIMULATION},\n"
            f"  confidence={self.CONFIDENCE_THRESHOLD}\n"
            f")"
        )
