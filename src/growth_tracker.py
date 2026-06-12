"""
Growth Tracker — Monitors plant development over time.
Features: periodic captures, ripeness tracking, trend analysis, JSON export.
"""

import json
import logging
import time
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("plant_vision.growth")


class GrowthTracker:
    """Tracks plant growth and fruit ripeness over time."""

    def __init__(self, settings):
        self.settings = settings
        self.log_dir = settings.GROWTH_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current session data
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")

        # Detection history (in-memory for current session)
        self.history = []
        self._current_snapshot = {
            "timestamp": None,
            "counts": {},
            "total": 0,
            "ripe_ratio": 0.0,
        }

        # Periodic capture
        self._capture_timer = None
        self._running = False

        logger.info(f"Growth tracker initialized. Session: {self.session_id}")

    def record_detection(self, predictions):
        """
        Record a detection snapshot from the current frame.
        Called by PlantDetector on each detection event.
        """
        now = datetime.now()
        counts = {}
        for pred in predictions:
            cls = pred.get("class", "unknown")
            counts[cls] = counts.get(cls, 0) + 1

        total = sum(counts.values())
        ripe_count = sum(
            v for k, v in counts.items()
            if "ripe" in k.lower() or "chin" in k.lower()
        )
        ripe_ratio = ripe_count / total if total > 0 else 0.0

        self._current_snapshot = {
            "timestamp": now.isoformat(),
            "counts": counts,
            "total": total,
            "ripe_count": ripe_count,
            "ripe_ratio": round(ripe_ratio, 3),
        }

    def capture_snapshot(self):
        """Take a growth data snapshot and add it to history."""
        snapshot = self._current_snapshot.copy()
        snapshot["timestamp"] = datetime.now().isoformat()
        self.history.append(snapshot)
        logger.info(
            f"Growth snapshot: total={snapshot['total']}, "
            f"ripe_ratio={snapshot['ripe_ratio']:.1%}"
        )
        self._save_session_log()
        return snapshot

    def start_periodic_capture(self):
        """Start periodic growth data capture in background."""
        self._running = True
        interval = self.settings.GROWTH_CAPTURE_INTERVAL
        logger.info(f"Periodic growth capture started (every {interval}s)")
        self._schedule_next_capture()

    def _schedule_next_capture(self):
        if not self._running:
            return
        self._capture_timer = threading.Timer(
            self.settings.GROWTH_CAPTURE_INTERVAL,
            self._periodic_capture_tick,
        )
        self._capture_timer.daemon = True
        self._capture_timer.start()

    def _periodic_capture_tick(self):
        if not self._running:
            return
        self.capture_snapshot()
        self._schedule_next_capture()

    def stop_periodic_capture(self):
        """Stop periodic capture."""
        self._running = False
        if self._capture_timer:
            self._capture_timer.cancel()
        self._save_session_log()
        logger.info("Periodic growth capture stopped")

    # ── Analysis ──────────────────────────────────────────────

    def get_trend(self, last_n=10):
        """
        Analyze growth trend from recent snapshots.
        Returns: 'improving', 'stable', 'declining', or 'insufficient_data'
        """
        if len(self.history) < 3:
            return "insufficient_data"

        recent = self.history[-last_n:]
        ratios = [s["ripe_ratio"] for s in recent]

        if len(ratios) < 2:
            return "insufficient_data"

        # Simple linear trend
        first_half = sum(ratios[: len(ratios) // 2]) / (len(ratios) // 2)
        second_half = sum(ratios[len(ratios) // 2:]) / (len(ratios) - len(ratios) // 2)
        diff = second_half - first_half

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def get_summary(self):
        """Get a summary of current growth tracking data."""
        return {
            "session_id": self.session_id,
            "session_start": self.session_start.isoformat(),
            "snapshots_count": len(self.history),
            "current": self._current_snapshot,
            "trend": self.get_trend(),
            "history": self.history[-50:],  # Last 50 snapshots
        }

    # ── Persistence ───────────────────────────────────────────

    def _save_session_log(self):
        """Save current session data to JSON file."""
        log_file = self.log_dir / f"session_{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "session_start": self.session_start.isoformat(),
            "last_updated": datetime.now().isoformat(),
            "snapshots": self.history,
        }
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Session log saved: {log_file}")
        except Exception as e:
            logger.error(f"Failed to save session log: {e}")

    def load_session(self, session_id):
        """Load a previous session's data."""
        log_file = self.log_dir / f"session_{session_id}.json"
        if not log_file.exists():
            logger.warning(f"Session file not found: {log_file}")
            return None
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def list_sessions(self):
        """List all saved growth tracking sessions."""
        sessions = []
        for f in sorted(self.log_dir.glob("session_*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                sessions.append({
                    "session_id": data.get("session_id"),
                    "session_start": data.get("session_start"),
                    "snapshots_count": len(data.get("snapshots", [])),
                    "filename": f.name,
                })
            except Exception:
                continue
        return sessions
