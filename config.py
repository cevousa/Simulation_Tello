"""
Configuration file for Drone Controller
กำหนดว่าจะใช้ Simulator หรือโดรนจริง
"""

# โหมดการทำงาน
USE_SIMULATOR = True  # True = CoppeliaSim, False = โดรนจริง

# การตั้งค่า CoppeliaSim
COPPELIA_CONFIG = {
    'host': 'localhost',
    'port': 23000,
    'image_folder': './captured_images/',
    'vision_sensor_name': '/Quadcopter/visionSensor'
}

# การตั้งค่าโดรนจริง
TELLO_CONFIG = {
    'ip': '192.168.10.1',
    'port': 8889,
    'image_folder': './captured_images/',
    'video_port': 11111
}

# การตั้งค่าทั่วไป
GENERAL_CONFIG = {
    'default_speed': 50,
    'default_height': 100,  # ซม.
    'qr_timeout': 5.0,
    'photo_quality': 90
}
