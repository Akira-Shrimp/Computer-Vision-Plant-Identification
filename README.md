#Plant Vision — Computer Vision Plant Identification

A computer vision system that uses a camera to monitor plant growth, identify ripe tomatoes and peppers, and assist automated robotic harvesting.

Hệ thống thị giác máy tính sử dụng camera để theo dõi quá trình phát triển cây trồng, nhận diện cà chua và ớt chín, hỗ trợ thu hoạch tự động bằng robot.

---

## Features

| Feature | Description |
|---------|-------------|
|  **Real-time Detection** | Detect tomatoes & peppers via Roboflow AI + WebRTC streaming |
|  **Growth Tracking** | Monitor plant development over time with ripeness ratio analysis |
|  **Robot Integration** | Send harvest coordinates to robot arm via Serial (Arduino/ESP32) |
|  **Data Collection** | Interactive tool to capture & label training images from webcam |
|  **Web Dashboard** | Real-time monitoring dashboard with live camera feed & charts |
|  **Custom Visualization** | Styled bounding boxes, FPS overlay, detection summary |

##  Project Structure

```
Computer-Vision-Plant-Identification/
├── main.py                    # Entry point (CLI: detect/collect/dashboard/track/status)
├── config/
│   ├── settings.py            # Centralized configuration
│   └── .env.example           # Environment variable template
├── src/
│   ├── detect.py              # PlantDetector — real-time detection pipeline
│   ├── growth_tracker.py      # GrowthTracker — development monitoring
│   ├── data_collector.py      # DataCollector — training data capture
│   └── utils.py               # Visualization utilities (bounding boxes, overlays)
├── deploy/
│   └── robot_controller.py    # RobotController — serial robot arm communication
├── dashboard/
│   ├── app.py                 # Flask + SocketIO web server
│   ├── templates/index.html   # Dashboard UI
│   └── static/                # CSS + JS assets
├── data/
│   ├── raw/                   # Raw training images
│   ├── captures/              # Captured images from data collector
│   └── growth_logs/           # Growth tracking JSON logs
├── logs/                      # Application logs
├── requirements.txt           # Python dependencies
└── todo-list.md               # Project roadmap
```

##  Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the template and fill in your values
copy config\.env.example .env
```

Edit `.env` and set your `ROBOFLOW_API_KEY`.

### 3. Check Configuration

```bash
python main.py status
```

### 4. Run

```bash
# Real-time detection (requires Roboflow API key)
python main.py detect

# Interactive data collection
python main.py collect

# Web monitoring dashboard
python main.py dashboard

# Growth tracking only
python main.py track
```

## 🖥️ Dashboard

Access the web dashboard at `http://localhost:5000` after running:

```bash
python main.py dashboard
```

Features:
-  Live camera feed (MJPEG stream)
-  Real-time detection stats
-  Growth tracking chart (Chart.js)
-  Robot controller status
-  System configuration overview

##  Robot Integration

The system communicates with a robot arm (Arduino/ESP32) via Serial:

- **Protocol**: `X{x}Y{y}\n` or `X{x}Y{y}Z{z}\n`
- **Safety**: Boundary checks prevent out-of-range commands
- **Simulation Mode**: Test without hardware (default: enabled)

Set `ROBOT_SIMULATION=false` in `.env` to enable live mode.

##  Data Collection

Interactive tool for collecting training images:

| Key | Action |
|-----|--------|
| `SPACE` | Capture image |
| `1-9` | Switch class label |
| `A` | Toggle auto-capture |
| `S` | Show statistics |
| `Q` | Quit |

##  Hardware Requirements

- **Camera**: USB webcam or built-in camera
- **Optional**: NVIDIA GPU for faster inference
- **Robot**: Arduino/ESP32 with serial connection
- **Edge Deploy**: Raspberry Pi / NVIDIA Jetson Nano

##  References

- [Roboflow](https://roboflow.com/) — Model training & inference
- [YOLOv8](https://docs.ultralytics.com/) — Object detection
- [OpenCV](https://opencv.org/) — Computer vision library

##  TODO List

See [todo-list.md](todo-list.md) for the full project roadmap.

## 📄 Google Docs

[Project Document](https://docs.google.com/document/d/1npDWAj0Ff6ecBgSx1cd7IKI_FOZj0kJFu4YAhijxcKA/edit?usp=sharing)
