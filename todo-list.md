CSI Research based learning: Computer vision
===============
To realize this project for tomatoes and peppers, and to easily scale it up later, we need to go through a standard process for an Artificial Intelligence (AI) and Computer Vision project. Here are the specific steps:
---------------
### 1. Thu thập dữ liệu (Data Collection)
    Máy tính học qua ví dụ, nên bạn cần một lượng lớn hình ảnh thực tế để "dạy" nó.
    Chụp ảnh: Thu thập hàng ngàn bức ảnh của cà chua và ớt ở các môi trường thực tế.
    Tính đa dạng: Đảm bảo chụp ở nhiều điều kiện khác nhau: ánh sáng (sáng sớm, trưa, chiều tối), góc độ (bị lá che khuất một phần, dính mưa), và các giai đoạn phát triển (cây non, quả xanh, quả ương, quả chín, quả hỏng).
### 2. Gán nhãn dữ liệu (Data Annotation)
    Đây là bước bạn chỉ cho máy tính biết đâu là đối tượng cần tìm trong bức ảnh.
    Sử dụng các công cụ như LabelImg, Roboflow, hoặc CVAT.
    Vẽ các hộp giới hạn (bounding boxes) hoặc phân vùng (polygons) bao quanh từng quả cà chua/ớt.
    Gắn nhãn (label) cho chúng, ví dụ: ca_chua_xanh, ca_chua_chin, ot_xanh, ot_chin.
### 3. Lựa chọn bài toán và mô hình (Model Selection)
    Đối với việc xác định vị trí để cánh tay robot có thể hái, bạn cần dùng bài toán Phát hiện đối tượng (Object Detection) hoặc cao cấp hơn là Phân vùng thực thể (Instance Segmentation).
    YOLO (You Only Look Once): (Ví dụ YOLOv8, YOLOv10) Đây là họ mô hình phổ biến nhất hiện nay vì tốc độ xử lý cực nhanh (phù hợp cho camera thời gian thực) và độ chính xác cao.
    Mask R-CNN: Dùng nếu bạn cần độ chính xác cực cao đến từng pixel biên giới của quả (hữu ích nếu quả bị che khuất nhiều), nhưng sẽ đòi hỏi máy tính cấu hình mạnh hơn.
### 4. Huấn luyện mô hình (Training)
    Chia tập dữ liệu của bạn thành 3 phần: Tập huấn luyện (Train), Tập xác thực (Validation) và Tập kiểm thử (Test).
    Sử dụng ngôn ngữ Python với các framework như PyTorch hoặc TensorFlow.
    Cho mô hình học qua tập dữ liệu đã gán nhãn. Quá trình này sẽ cần máy tính có Card đồ họa (GPU) đủ mạnh. Bạn có thể tận dụng Google Colab để huấn luyện miễn phí nếu không có máy tính chuyên dụng.
### 5. Đánh giá và Tối ưu (Evaluation & Optimization)
    Sau khi huấn luyện, cho mô hình chạy thử trên các bức ảnh/video nó chưa từng thấy (Tập Test).
    Đánh giá qua các chỉ số như mAP (mean Average Precision). Nếu máy tính thường xuyên nhầm quả xanh thành quả chín, hoặc không nhìn thấy quả bị lá che, bạn cần quay lại bước 1 và 2 để bổ sung thêm dữ liệu cho các trường hợp khó đó.
### 6. Triển khai lên phần cứng (Deployment)
    Đưa mô hình đã huấn luyện xong vào thiết bị xử lý tại vườn (Edge Computing).
    Phần cứng: Bạn có thể sử dụng Raspberry Pi hoặc NVIDIA Jetson Nano kết nối với một module Camera.
    Phần mềm: Sử dụng thư viện OpenCV để mở luồng video trực tiếp từ camera, đưa từng khung hình vào mô hình AI để nhận diện, và xuất ra tọa độ (x, y) của quả đã chín.
### 7. Tích hợp Robot tự động hóa (Integration - Mở rộng)
    Gửi tín hiệu tọa độ (x, y, z) từ hệ thống camera sang bộ điều khiển của cánh tay robot cơ khí hoặc xe tự hành.
    Lập trình để cánh tay robot di chuyển đến đúng vị trí và thực hiện thao tác cắt/hái mà không làm dập quả.
