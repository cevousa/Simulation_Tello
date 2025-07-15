# test_connection.py
print("Python ทำงานได้แล้ว!")

# ทดสอบ libraries
try:
    import zmq
    print("✓ zmq ติดตั้งสำเร็จ")
except ImportError:
    print("✗ zmq ติดตั้งไม่สำเร็จ")

try:
    import cbor2 as cbor
    print("✓ cbor ติดตั้งสำเร็จ")
except ImportError:
    print("✗ cbor ติดตั้งไม่สำเร็จ")

try:
    import numpy
    print("✓ numpy ติดตั้งสำเร็จ")
except ImportError:
    print("✗ numpy ติดตั้งไม่สำเร็จ")

try:
    import cv2
    print("✓ opencv-python ติดตั้งสำเร็จ")
except ImportError:
    print("✗ opencv-python ติดตั้งไม่สำเร็จ")

try:
    from zmqRemoteApi import RemoteAPIClient
    print("✓ zmqRemoteApi.py พร้อมใช้งาน")
    

    
except ImportError:

    print("✗ ไม่พบไฟล์ zmqRemoteApi.py")


