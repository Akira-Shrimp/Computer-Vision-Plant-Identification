"""
Plant Vision Dashboard — Flask + SocketIO web monitoring interface.
Provides real-time detection stats, growth charts, robot status, and camera feed.
"""

import json
import logging
import time
import threading
import base64
from pathlib import Path
from datetime import datetime

import cv2
from flask import Flask, render_template, jsonify, Response
from flask_socketio import SocketIO

logger = logging.getLogger("plant_vision.dashboard")

# Global references (set during create_app)
_settings = None
_growth_tracker = None
_robot_controller = None
_camera_cap = None
_latest_frame = None
_latest_predictions = []
_system_start_time = None


def create_app(settings):
    """Create and configure the Flask application."""
    global _settings, _growth_tracker, _robot_controller, _system_start_time

    _settings = settings
    _system_start_time = time.time()

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.config["SECRET_KEY"] = "plant-vision-secret-key"

    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    # Initialize components
    from src.growth_tracker import GrowthTracker
    from deploy.robot_controller import RobotController

    _growth_tracker = GrowthTracker(settings)
    _robot_controller = RobotController(settings)

    # ── Routes ────────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/stats")
    def api_stats():
        """Return current system statistics."""
        uptime = time.time() - _system_start_time
        growth_summary = _growth_tracker.get_summary() if _growth_tracker else {}
        robot_status = _robot_controller.get_status() if _robot_controller else {}

        return jsonify({
            "uptime_seconds": uptime,
            "uptime_formatted": format_uptime(uptime),
            "growth": growth_summary,
            "robot": robot_status,
            "predictions": _latest_predictions,
            "detection_count": len(_latest_predictions),
            "timestamp": datetime.now().isoformat(),
        })

    @app.route("/api/growth")
    def api_growth():
        """Return growth tracking data."""
        if _growth_tracker:
            return jsonify(_growth_tracker.get_summary())
        return jsonify({"error": "Growth tracker not initialized"})

    @app.route("/api/growth/sessions")
    def api_growth_sessions():
        """List all growth tracking sessions."""
        if _growth_tracker:
            return jsonify(_growth_tracker.list_sessions())
        return jsonify([])

    @app.route("/api/robot")
    def api_robot():
        """Return robot controller status."""
        if _robot_controller:
            return jsonify(_robot_controller.get_status())
        return jsonify({"error": "Robot controller not initialized"})

    @app.route("/api/captures")
    def api_captures():
        """List recent captures."""
        capture_dir = settings.CAPTURE_DIR
        images = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            for f in sorted(capture_dir.rglob(ext), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                images.append({
                    "filename": f.name,
                    "path": str(f.relative_to(capture_dir)),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
        return jsonify(images)

    @app.route("/api/config")
    def api_config():
        """Return current configuration (safe fields only)."""
        return jsonify({
            "camera": f"{settings.CAMERA_WIDTH}x{settings.CAMERA_HEIGHT}",
            "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
            "target_classes": settings.TARGET_CLASSES,
            "serial_port": settings.SERIAL_PORT,
            "robot_simulation": settings.ROBOT_SIMULATION,
            "growth_interval": settings.GROWTH_CAPTURE_INTERVAL,
        })

    @app.route("/video_feed")
    def video_feed():
        """MJPEG video stream from the camera."""
        return Response(
            generate_video_frames(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    # ── SocketIO Events ───────────────────────────────────────

    @socketio.on("connect")
    def handle_connect():
        logger.info("Dashboard client connected")

    @socketio.on("request_snapshot")
    def handle_snapshot():
        """Client requests a growth snapshot."""
        if _growth_tracker:
            snapshot = _growth_tracker.capture_snapshot()
            socketio.emit("snapshot_taken", snapshot)

    @socketio.on("robot_home")
    def handle_robot_home():
        """Send robot to home position."""
        if _robot_controller:
            _robot_controller.send_home()
            socketio.emit("robot_status", _robot_controller.get_status())

    # Start background stats broadcaster
    def broadcast_stats():
        while True:
            try:
                uptime = time.time() - _system_start_time
                data = {
                    "uptime": format_uptime(uptime),
                    "growth": _growth_tracker.get_summary() if _growth_tracker else {},
                    "robot": _robot_controller.get_status() if _robot_controller else {},
                    "predictions": _latest_predictions,
                    "timestamp": datetime.now().isoformat(),
                }
                socketio.emit("stats_update", data)
            except Exception as e:
                logger.debug(f"Broadcast error: {e}")
            time.sleep(2)

    bg_thread = threading.Thread(target=broadcast_stats, daemon=True)
    bg_thread.start()

    return app, socketio


def generate_video_frames():
    """Generator for MJPEG video stream."""
    global _camera_cap
    if _camera_cap is None:
        _camera_cap = cv2.VideoCapture(_settings.CAMERA_INDEX)
        _camera_cap.set(cv2.CAP_PROP_FRAME_WIDTH, _settings.CAMERA_WIDTH)
        _camera_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, _settings.CAMERA_HEIGHT)

    while True:
        ret, frame = _camera_cap.read()
        if not ret:
            # Send a placeholder frame
            frame = create_placeholder_frame()

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        time.sleep(0.033)  # ~30 FPS


def create_placeholder_frame():
    """Create a placeholder frame when camera is unavailable."""
    import numpy as np
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (30, 30, 30)
    cv2.putText(
        frame, "Camera Not Available",
        (140, 240),
        cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2, cv2.LINE_AA,
    )
    cv2.putText(
        frame, "Check camera connection",
        (160, 280),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 80, 80), 1, cv2.LINE_AA,
    )
    return frame


def format_uptime(seconds):
    """Format seconds into human-readable uptime string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"
