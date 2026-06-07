import cv2
from inference_sdk import InferenceHTTPClient
from inference_sdk.webrtc import WebcamSource, StreamConfig, VideoMetadata

from deploy.robot_controller import send_coordinates_to_robot
# Initialize client
client = InferenceHTTPClient.init(
    api_url="https://serverless.roboflow.com",
    api_key="YOUR API KEY"
)

# Configure video source (webcam)
source = WebcamSource(resolution=(1280, 720))

# Configure streaming options
config = StreamConfig(
    # stream_output=["my_stream_output"], # Uncomment and check your stream output name
    # data_output=["predictions"], # Uncomment and check your data output name
    processing_timeout=3600,             # 60 minutes
    requested_plan="webrtc-gpu-medium",  # Options: webrtc-gpu-small, webrtc-gpu-medium, webrtc-gpu-large
    requested_region="us"                # Options: us, eu, ap
)

# Create streaming session
session = client.webrtc.stream(
    source=source,
    workflow="find-tomato-oohfb",
    workspace="h-m-0hina",
    image_input="image",
    config=config
)

# Handle incoming video frames

@session.on_frame
def show_frame(frame, metadata):
    cv2.imshow("Workflow Output", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        session.close()


# Handle prediction data via datachannel
@session.on_data()
def on_data(data: dict, metadata: VideoMetadata):
    # check if found object
    if "predictions" in data and len(data["predictions"]) > 0:
        for pred in data["predictions"]:
            # Lấy thông tin class và tọa độ trung tâm
            object = pred.get("class")
            x = pred.get("x")
            y = pred.get("y")
            print(f"Found {object} at coordinates: X={x}, Y={y}")


# Handle prediction data via datachannel (code cũ của model. thay thế vì cục dữ liệu khạc ra quá to)
#@session.on_data()
#def on_data(data: dict, metadata: VideoMetadata):
#    print(f"Frame {metadata.frame_id}: {data}")

# Run the session (blocks until closed)
session.run()
