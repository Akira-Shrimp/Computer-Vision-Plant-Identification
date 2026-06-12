"""
Data Collector — Captures images from camera for model training.
Features: manual/auto capture, labeling, metadata, statistics.
"""

import cv2
import json
import logging
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("plant_vision.collect")


class DataCollector:
    """Captures and organizes images for training data collection."""

    def __init__(self, settings):
        self.settings = settings
        self.capture_dir = settings.CAPTURE_DIR
        self.capture_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file
        self.metadata_file = self.capture_dir / "metadata.json"
        self.metadata = self._load_metadata()

        # Stats
        self.session_captures = 0

    def _load_metadata(self):
        """Load existing metadata or create new."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"images": [], "total_count": 0, "class_counts": {}}

    def _save_metadata(self):
        """Save metadata to disk."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def capture_image(self, frame, label="unlabeled", notes=""):
        """
        Save a single frame as a training image.

        Args:
            frame: OpenCV image (BGR)
            label: class label for this image
            notes: optional notes about the capture

        Returns:
            Path to saved image
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{label}_{timestamp}.jpg"

        # Create label subdirectory
        label_dir = self.capture_dir / label
        label_dir.mkdir(parents=True, exist_ok=True)
        filepath = label_dir / filename

        # Save image
        cv2.imwrite(str(filepath), frame)

        # Update metadata
        entry = {
            "filename": filename,
            "label": label,
            "path": str(filepath.relative_to(self.capture_dir)),
            "timestamp": datetime.now().isoformat(),
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
            "notes": notes,
        }
        self.metadata["images"].append(entry)
        self.metadata["total_count"] += 1
        self.metadata["class_counts"][label] = (
            self.metadata["class_counts"].get(label, 0) + 1
        )
        self._save_metadata()

        self.session_captures += 1
        logger.info(f"Captured: {filepath} (label={label})")
        return filepath

    def start_interactive(self):
        """
        Start interactive data collection from webcam.

        Controls:
            SPACE  — Capture image with current label
            1-9    — Change label (mapped to class names)
            a      — Toggle auto-capture mode
            i      — Add notes to next capture
            s      — Show statistics
            q      — Quit
        """
        cap = cv2.VideoCapture(self.settings.CAMERA_INDEX)
        if not cap.isOpened():
            logger.error("Cannot open camera")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.CAMERA_HEIGHT)

        classes = self.settings.ALL_CLASSES
        current_label_idx = 0
        auto_capture = False
        last_auto_time = 0
        notes = ""

        logger.info("Interactive data collection started")
        logger.info(f"Available classes: {classes}")
        logger.info("Press SPACE to capture, 1-9 to change class, 'a' for auto, 'q' to quit")

        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame")
                time.sleep(0.1)
                continue

            # Draw UI overlay
            display = frame.copy()
            current_label = classes[current_label_idx] if current_label_idx < len(classes) else "unlabeled"
            h, w = display.shape[:2]

            # Top bar
            cv2.rectangle(display, (0, 0), (w, 50), (30, 30, 30), -1)
            cv2.putText(
                display,
                f"DATA COLLECTOR | Label: {current_label} | Captured: {self.session_captures}",
                (10, 33),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 150), 2, cv2.LINE_AA,
            )

            # Auto mode indicator
            if auto_capture:
                cv2.circle(display, (w - 25, 25), 10, (0, 0, 255), -1)
                cv2.putText(
                    display, "AUTO",
                    (w - 70, 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA,
                )

            # Bottom bar with class list
            cv2.rectangle(display, (0, h - 35), (w, h), (30, 30, 30), -1)
            x_offset = 10
            for i, cls in enumerate(classes):
                color = (0, 255, 150) if i == current_label_idx else (150, 150, 150)
                text = f"[{i + 1}] {cls}"
                cv2.putText(
                    display, text,
                    (x_offset, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA,
                )
                (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                x_offset += tw + 20

            cv2.imshow("Data Collector", display)

            # Auto capture
            if auto_capture:
                now = time.time()
                if now - last_auto_time >= self.settings.AUTO_CAPTURE_INTERVAL:
                    self.capture_image(frame, current_label, notes)
                    notes = ""
                    last_auto_time = now

            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" "):
                self.capture_image(frame, current_label, notes)
                notes = ""
            elif key == ord("a"):
                auto_capture = not auto_capture
                mode = "ON" if auto_capture else "OFF"
                logger.info(f"Auto capture: {mode}")
                last_auto_time = time.time()
            elif key == ord("s"):
                stats = self.get_stats()
                logger.info(f"Collection stats: {json.dumps(stats, indent=2)}")
            elif ord("1") <= key <= ord("9"):
                idx = key - ord("1")
                if idx < len(classes):
                    current_label_idx = idx
                    logger.info(f"Label changed to: {classes[idx]}")

        cap.release()
        cv2.destroyAllWindows()
        logger.info(f"Data collection ended. Session captures: {self.session_captures}")

    def get_stats(self):
        """Return collection statistics."""
        return {
            "total_images": self.metadata["total_count"],
            "session_captures": self.session_captures,
            "class_distribution": self.metadata["class_counts"],
            "capture_dir": str(self.capture_dir),
        }
