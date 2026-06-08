"""
Visualization Utilities — Custom drawing for plant detection overlays.
Features: colored bounding boxes, labels, FPS overlay, mini-map, screenshots.
"""

import cv2
import numpy as np
import time
from pathlib import Path
from datetime import datetime


# ── Color Palette (BGR format for OpenCV) ──────────────────────
# Colors mapped by ripeness: green → yellow → orange → red
CLASS_COLORS = {
    "tomato_green": (0, 180, 0),       # Green
    "tomato_ripe": (0, 0, 220),        # Red
    "pepper_green": (0, 200, 80),      # Light green
    "pepper_ripe": (0, 80, 220),       # Orange-red
    "tomato": (0, 0, 220),             # Red (generic)
    "pepper": (0, 80, 220),            # Orange-red (generic)
    "default": (255, 200, 0),          # Cyan
}

# Ripeness gradient (0.0 = green → 1.0 = red)
def ripeness_color(ratio):
    """Generate a color on the green-to-red gradient based on ripeness ratio (0-1)."""
    r = int(220 * ratio)
    g = int(200 * (1 - ratio))
    b = 0
    return (b, g, r)  # BGR


class FPSCounter:
    """Tracks and smooths FPS measurement."""

    def __init__(self, smoothing=30):
        self.smoothing = smoothing
        self._times = []
        self._fps = 0

    def tick(self):
        now = time.time()
        self._times.append(now)
        # Keep only recent timestamps
        self._times = self._times[-self.smoothing:]
        if len(self._times) >= 2:
            elapsed = self._times[-1] - self._times[0]
            self._fps = (len(self._times) - 1) / elapsed if elapsed > 0 else 0

    @property
    def fps(self):
        return self._fps


def draw_bounding_box(frame, prediction, show_confidence=True):
    """
    Draw a styled bounding box with label on the frame.

    Args:
        frame: OpenCV image (BGR)
        prediction: dict with keys 'class', 'x', 'y', 'width', 'height', 'confidence'
        show_confidence: whether to display confidence percentage
    """
    cls = prediction.get("class", "unknown")
    x_center = prediction.get("x", 0)
    y_center = prediction.get("y", 0)
    w = prediction.get("width", 0)
    h = prediction.get("height", 0)
    conf = prediction.get("confidence", 0)

    # Calculate corner coordinates
    x1 = int(x_center - w / 2)
    y1 = int(y_center - h / 2)
    x2 = int(x_center + w / 2)
    y2 = int(y_center + h / 2)

    # Get color for this class
    color = CLASS_COLORS.get(cls, CLASS_COLORS["default"])

    # Draw main bounding box (rounded corners effect with thick line)
    thickness = 2
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    # Draw corner accents (thicker, shorter lines at corners)
    corner_len = min(20, w // 4, h // 4)
    corner_thick = 4
    # Top-left
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, corner_thick)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, corner_thick)
    # Top-right
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, corner_thick)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, corner_thick)
    # Bottom-left
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, corner_thick)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, corner_thick)
    # Bottom-right
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, corner_thick)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, corner_thick)

    # Draw label background
    label = cls.replace("_", " ").title()
    if show_confidence:
        label = f"{label} {conf:.0%}"

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    font_thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)

    # Label background with slight transparency effect
    label_y1 = max(0, y1 - text_h - 10)
    label_y2 = y1
    cv2.rectangle(frame, (x1, label_y1), (x1 + text_w + 10, label_y2), color, -1)

    # Label text
    cv2.putText(
        frame, label,
        (x1 + 5, y1 - 4),
        font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA,
    )

    # Draw center point
    cv2.circle(frame, (int(x_center), int(y_center)), 4, color, -1)

    return frame


def draw_all_detections(frame, predictions, show_confidence=True):
    """Draw bounding boxes for all predictions on the frame."""
    for pred in predictions:
        draw_bounding_box(frame, pred, show_confidence)
    return frame


def draw_fps_overlay(frame, fps_counter):
    """Draw FPS counter in the top-right corner."""
    fps_text = f"FPS: {fps_counter.fps:.1f}"
    font = cv2.FONT_HERSHEY_SIMPLEX

    (text_w, text_h), _ = cv2.getTextSize(fps_text, font, 0.6, 2)
    h, w = frame.shape[:2]

    # Background
    x1 = w - text_w - 20
    y1 = 10
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (w - 10, y1 + text_h + 14), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Text
    cv2.putText(
        frame, fps_text,
        (x1 + 5, y1 + text_h + 7),
        font, 0.6, (0, 255, 0), 2, cv2.LINE_AA,
    )
    return frame


def draw_status_overlay(frame, status_info):
    """
    Draw a status overlay in the top-left corner.

    Args:
        frame: OpenCV image
        status_info: dict with status fields like 'mode', 'detections', 'robot'
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    line_height = 22
    padding = 10
    y_start = padding + 15

    lines = []
    for key, value in status_info.items():
        lines.append(f"{key}: {value}")

    # Calculate background size
    max_w = 0
    for line in lines:
        (tw, _), _ = cv2.getTextSize(line, font, font_scale, 1)
        max_w = max(max_w, tw)

    bg_h = len(lines) * line_height + padding * 2
    bg_w = max_w + padding * 2 + 10

    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (5, 5), (5 + bg_w, 5 + bg_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # Draw text lines
    for i, line in enumerate(lines):
        cv2.putText(
            frame, line,
            (padding + 5, y_start + i * line_height),
            font, font_scale, (220, 220, 220), 1, cv2.LINE_AA,
        )
    return frame


def draw_detection_summary(frame, predictions):
    """Draw a summary bar at the bottom showing detection counts by class."""
    h, w = frame.shape[:2]
    bar_height = 40

    # Count by class
    counts = {}
    for pred in predictions:
        cls = pred.get("class", "unknown")
        counts[cls] = counts.get(cls, 0) + 1

    if not counts:
        return frame

    # Semi-transparent bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - bar_height), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Draw counts
    font = cv2.FONT_HERSHEY_SIMPLEX
    x_pos = 15
    for cls, count in counts.items():
        color = CLASS_COLORS.get(cls, CLASS_COLORS["default"])
        label = f"{cls.replace('_', ' ').title()}: {count}"
        cv2.circle(frame, (x_pos, h - bar_height // 2), 6, color, -1)
        cv2.putText(
            frame, label,
            (x_pos + 12, h - bar_height // 2 + 5),
            font, 0.45, (220, 220, 220), 1, cv2.LINE_AA,
        )
        (tw, _), _ = cv2.getTextSize(label, font, 0.45, 1)
        x_pos += tw + 35

    return frame


def save_screenshot(frame, save_dir, prefix="screenshot"):
    """Save a screenshot of the current frame."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = save_dir / f"{prefix}_{timestamp}.jpg"
    cv2.imwrite(str(filename), frame)
    return filename


class VideoRecorder:
    """Records video from the detection pipeline."""

    def __init__(self, save_path, fps=20.0, resolution=(1280, 720)):
        self.save_path = Path(save_path)
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(str(self.save_path), fourcc, fps, resolution)
        self.recording = True
        self.frame_count = 0

    def write_frame(self, frame):
        if self.recording and self.writer.isOpened():
            self.writer.write(frame)
            self.frame_count += 1

    def stop(self):
        self.recording = False
        if self.writer.isOpened():
            self.writer.release()

    def __del__(self):
        self.stop()
