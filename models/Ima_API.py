# 1. Import the library
from inference_sdk import InferenceHTTPClient

# 2. Connect to your workflow
client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="DXYjbmlbSJIze71C80LA"
)

# 3. Run your workflow on an image
result = client.run_workflow(
    workspace_name="h-m-0hina",
    workflow_id="find-tomato-oohfb",
    images={
        "image": "YOUR_IMAGE.jpg" # Path to your image file
    },
    use_cache=True # Speeds up repeated requests
)

# 4. Get your results
print(result)
