"""
Plant Vision — Main Entry Point
================================
Computer vision system for monitoring plant growth and assisting automated harvesting.

Usage:
    python main.py detect      — Start real-time detection pipeline
    python main.py collect     — Start interactive data collection
    python main.py dashboard   — Launch web monitoring dashboard
    python main.py track       — Start growth tracking only
    python main.py status      — Show system configuration
"""

import sys
import os
import logging
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


def setup_logging(level="INFO"):
    """Configure logging for the entire application."""
    from config.settings import Settings
    settings = Settings()

    log_format = (
        "%(asctime)s │ %(levelname)-7s │ %(name)-25s │ %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # File handler
    log_file = settings.LOG_DIR / "plant_vision.log"
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Root logger
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.addHandler(console)
    root.addHandler(file_handler)

    return settings


def cmd_detect(settings):
    """Run the real-time detection pipeline."""
    from src.detect import PlantDetector
    from src.growth_tracker import GrowthTracker
    from deploy.robot_controller import RobotController

    logger = logging.getLogger("plant_vision.main")
    logger.info("=" * 60)
    logger.info("  PLANT VISION — Detection Mode")
    logger.info("=" * 60)

    # Initialize components
    robot = RobotController(settings)
    tracker = GrowthTracker(settings)
    detector = PlantDetector(settings, robot_controller=robot, growth_tracker=tracker)

    # Start growth tracking
    tracker.start_periodic_capture()

    try:
        detector.start()
    finally:
        tracker.stop_periodic_capture()
        robot.disconnect()
        logger.info("All components shut down")


def cmd_collect(settings):
    """Run interactive data collection."""
    from src.data_collector import DataCollector

    logger = logging.getLogger("plant_vision.main")
    logger.info("=" * 60)
    logger.info("  PLANT VISION — Data Collection Mode")
    logger.info("=" * 60)

    collector = DataCollector(settings)
    collector.start_interactive()

    stats = collector.get_stats()
    logger.info(f"Final stats: {stats}")


def cmd_dashboard(settings):
    """Launch the web monitoring dashboard."""
    logger = logging.getLogger("plant_vision.main")
    logger.info("=" * 60)
    logger.info("  PLANT VISION — Web Dashboard")
    logger.info("=" * 60)
    logger.info(
        f"Starting dashboard on http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}"
    )

    from dashboard.app import create_app
    app, socketio = create_app(settings)
    socketio.run(
        app,
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        debug=settings.DASHBOARD_DEBUG,
        allow_unsafe_werkzeug=True,
    )


def cmd_track(settings):
    """Run growth tracking in standalone mode (captures from camera periodically)."""
    import cv2
    import time
    from src.growth_tracker import GrowthTracker

    logger = logging.getLogger("plant_vision.main")
    logger.info("=" * 60)
    logger.info("  PLANT VISION — Growth Tracking Mode")
    logger.info("=" * 60)

    tracker = GrowthTracker(settings)
    cap = cv2.VideoCapture(settings.CAMERA_INDEX)
    if not cap.isOpened():
        logger.error("Cannot open camera")
        return

    logger.info(
        f"Capturing growth snapshots every {settings.GROWTH_CAPTURE_INTERVAL}s. "
        f"Press Ctrl+C to stop."
    )

    try:
        while True:
            ret, frame = cap.read()
            if ret:
                snapshot = tracker.capture_snapshot()
                logger.info(f"Snapshot: {snapshot}")

                # Save the frame
                from src.utils import save_screenshot
                save_screenshot(frame, settings.GROWTH_LOG_DIR / "frames", prefix="growth")

            time.sleep(settings.GROWTH_CAPTURE_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Growth tracking stopped by user")
    finally:
        cap.release()


def cmd_status(settings):
    """Display current system configuration."""
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║       PLANT VISION — System Configuration           ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Roboflow API:    {settings.ROBOFLOW_API_URL:<35s}║")
    print(f"║  Workflow:        {settings.ROBOFLOW_WORKFLOW:<35s}║")
    print(f"║  Workspace:       {settings.ROBOFLOW_WORKSPACE:<35s}║")
    print(f"║  Camera:          {settings.CAMERA_WIDTH}x{settings.CAMERA_HEIGHT} @ index {settings.CAMERA_INDEX:<19s}║")
    print(f"║  Serial Port:     {settings.SERIAL_PORT:<35s}║")
    print(f"║  Robot Mode:      {'SIMULATION' if settings.ROBOT_SIMULATION else 'LIVE':<35s}║")
    print(f"║  Confidence:      {settings.CONFIDENCE_THRESHOLD:<35.0%}║")
    print(f"║  Target Classes:  {', '.join(settings.TARGET_CLASSES):<35s}║")
    print(f"║  Dashboard:       http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT:<24}║")
    print("╠══════════════════════════════════════════════════════╣")

    # Validate
    errors = settings.validate()
    if errors:
        print("║  ⚠  Warnings:                                      ║")
        for err in errors:
            print(f"║    • {err:<48s}║")
    else:
        print("║  ✅ All configuration valid                          ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()


COMMANDS = {
    "detect": cmd_detect,
    "collect": cmd_collect,
    "dashboard": cmd_dashboard,
    "track": cmd_track,
    "status": cmd_status,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print(f"Available commands: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    command = sys.argv[1]
    settings = setup_logging()
    COMMANDS[command](settings)


if __name__ == "__main__":
    main()
