import serial
import time

# Thiết lập kết nối Serial tới vi điều khiển (Arduino/ESP32)
# LƯU Ý: Đổi 'COM3' thành cổng mình sử dụng (VD: '/dev/ttyUSB0' trên Mac/Linux, hoặc 'COM5' trên Windows)
try:
    robot_serial = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2) # Chờ 2 giây để bo mạch khởi động
    print("Connected to robot")
except Exception as e:
    print(f"Cannot connect to robot. Check the USB cable: {e}")
    robot_serial = None

def send_coordinates_to_robot(x, y):

    if robot_serial is not None:
        # Tạo chuỗi lệnh theo cú pháp thống nhất với code trên Arduino
        command = f"X{int(x)}Y{int(y)}\n"
        
        # Mã hóa và cho cook
        robot_serial.write(command.encode('utf-8'))
        print(f"[Robot Controller] Send: {command.strip()}")
    else:
        print(f"[simulation mode] tomatoes coordirate: X={x}, Y={y}")
