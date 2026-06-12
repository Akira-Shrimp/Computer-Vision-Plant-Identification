"""
Plant Detector — Main detection pipeline using Roboflow WebRTC streaming.
Features: multi-class detection, confidence filtering, callback system, FPS tracking.
"""

import cv2
import logging
import time
import sys

logger = logging.getLogger("plant_vision.detect")


class PlantDetector:
    """
    Real-time plant detection using Roboflow WebRTC streaming.
    Detects tomatoes and peppers at various growth stages.
    """

    def __init__(self, settings, robot_controller=None, growth_tracker=None):
        self.settings = settings
        self.robot = robot_controller
        self.growth_tracker = growth_tracker
        self.running = False

        # Stats
        self.total_detections = 0
        self.frame_count = 0
        self.start_time = None
        self.last_predictions = []

        # Callbacks for external consumers (dashboard, etc.)
        self._on_detection_callbacks = []
        self._on_frame_callbacks = []

    def on_detection(self, callback):
        """Register a callback for when objects are detected. callback(predictions, frame_id)"""
        self._on_detection_callbacks.append(callback)

    def on_frame(self, callback):
        """Register a callback for each processed frame. callback(frame, metadata)"""
        self._on_frame_callbacks.append(callback)

    def _notify_detection(self, predictions, frame_id):
        """Notify all registered detection callbacks."""
        for cb in self._on_detection_callbacks:
            try:
                cb(predictions, frame_id)
            except Exception as e:
                logger.error(f"Detection callback error: {e}")

    def _notify_frame(self, frame, metadata):
        """Notify all registered frame callbacks."""
        for cb in self._on_frame_callbacks:
            try:
                cb(frame, metadata)
            except Exception as e:
                logger.error(f"Frame callback error: {e}")

    def _filter_predictions(self, predictions):
        """Filter predictions by confidence threshold."""
        return [
            p for p in predictions
            if p.get("confidence", 0) >= self.settings.CONFIDENCE_THRESHOLD
        ]

    def _handle_predictions(self, data, metadata):
        """Process incoming prediction data from Roboflow."""
        if "predictions" not in data or len(data["predictions"]) == 0:
            self.last_predictions = []
            return

        predictions = self._filter_predictions(data["predictions"])
        self.last_predictions = predictions
        self.total_detections += len(predictions)

        if predictions:
            logger.debug(
                f"Frame {metadata.frame_id}: {len(predictions)} objects detected"
            )

        # Notify callbacks
        frame_id = getattr(metadata, "frame_id", self.frame_count)
        self._notify_detection(predictions, frame_id)

        # Send ripe fruit coordinates to robot
        for pred in predictions:
            detected_class = pred.get("class", "")
            x = pred.get("x", 0)
            y = pred.get("y", 0)
            confidence = pred.get("confidence", 0)

            # Check if this is a harvestable class
            if detected_class in self.settings.TARGET_CLASSES:
                logger.info(
                    f"Ripe {detected_class} detected at ({x}, {y}) "
                    f"confidence={confidence:.0%}"
                )
                if self.robot:
                    self.robot.send_coordinates(x, y)

        # Feed data to growth tracker
        if self.growth_tracker:
            self.growth_tracker.record_detection(predictions)

    def _handle_frame(self, frame, metadata):
        """Process incoming video frames."""
        self.frame_count += 1
        self._notify_frame(frame, metadata)

        # Display with OpenCV
        cv2.imshow("Plant Vision — Detection", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            logger.info("User pressed 'q' — shutting down")
            self.stop()
        elif key == ord("s"):
            from src.utils import save_screenshot
            path = save_screenshot(frame, self.settings.CAPTURE_DIR)
            logger.info(f"Screenshot saved: {path}")

    def start(self):
        """Start the real-time detection pipeline."""
        logger.info("Starting Plant Vision detection pipeline...")
        self.running = True
        self.start_time = time.time()

        # Validate config
        errors = self.settings.validate()
        if errors:
            for err in errors:
                logger.warning(f"Config warning: {err}")

        try:
            from inference_sdk import InferenceHTTPClient
            from inference_sdk.webrtc import WebcamSource, StreamConfig, VideoMetadata
        except ImportError:
            logger.error(
                "inference_sdk not installed. Run: pip install inference-sdk"
            )
            sys.exit(1)

        # Initialize Roboflow client
        client = InferenceHTTPClient.init(
            api_url=self.settings.ROBOFLOW_API_URL,
            api_key=self.settings.ROBOFLOW_API_KEY,
        )
        logger.info(f"Connected to Roboflow API: {self.settings.ROBOFLOW_API_URL}")

        # Configure video source
        source = WebcamSource(
            resolution=(self.settings.CAMERA_WIDTH, self.settings.CAMERA_HEIGHT)
        )
        logger.info(
            f"Camera source: {self.settings.CAMERA_WIDTH}x{self.settings.CAMERA_HEIGHT}"
        )

        # Configure streaming
        config = StreamConfig(
            processing_timeout=3600,
            requested_plan=self.settings.ROBOFLOW_PLAN,
            requested_region=self.settings.ROBOFLOW_REGION,
        )

        # Create streaming session
        session = client.webrtc.stream(
            source=source,
            workflow=self.settings.ROBOFLOW_WORKFLOW,
            workspace=self.settings.ROBOFLOW_WORKSPACE,
            image_input="image",
            config=config,
        )
        logger.info(f"Streaming session created: workflow={self.settings.ROBOFLOW_WORKFLOW}")

        # Store session reference for shutdown
        self._session = session

        # Register handlers
        @session.on_frame
        def on_frame(frame, metadata):
            if self.running:
                self._handle_frame(frame, metadata)

        @session.on_data()
        def on_data(data: dict, metadata: VideoMetadata):
            if self.running:
                self._handle_predictions(data, metadata)

        # Run (blocks until closed)
        logger.info("Detection pipeline running. Press 'q' to quit, 's' to screenshot.")
        try:
            session.run()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    def stop(self):
        """Stop the detection pipeline."""
        if not self.running:
            return
        self.running = False

        if hasattr(self, "_session"):
            try:
                self._session.close()
            except Exception as e:
                logger.debug(f"Session close: {e}")

        cv2.destroyAllWindows()

        # Print summary
        elapsed = time.time() - self.start_time if self.start_time else 0
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
        logger.info(
            f"Pipeline stopped. Frames: {self.frame_count}, "
            f"Detections: {self.total_detections}, "
            f"Avg FPS: {avg_fps:.1f}, "
            f"Runtime: {elapsed:.0f}s"
        )

    def get_stats(self):
        """Return current detection statistics."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "running": self.running,
            "frame_count": self.frame_count,
            "total_detections": self.total_detections,
            "avg_fps": self.frame_count / elapsed if elapsed > 0 else 0,
            "runtime_seconds": elapsed,
            "last_predictions": self.last_predictions,
        }
