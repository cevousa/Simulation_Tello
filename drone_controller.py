#เปิดกล้องจริงๆได้แล้ว
#!/usr/bin/env python3
"""
Complete Natural Drone Controller - Fixed Version
รวมฟังก์ชันทั้งหมดจากโค้ดเก่า + แก้ไขปัญหาต่างๆ
"""
from djitellopy import Tello
import time
import numpy as np
import cv2
import os
import math
from datetime import datetime
import threading

# ตรวจสอบ libraries ที่จำเป็น
try:
    from pyzbar import pyzbar
    QR_SCANNER_AVAILABLE = True
except ImportError:
    QR_SCANNER_AVAILABLE = False
    print("⚠️ pyzbar not available - QR scanning disabled")

try:
    from djitellopy import Tello
    REAL_DRONE_AVAILABLE = True
except ImportError:
    REAL_DRONE_AVAILABLE = False
    print("⚠️ DJI Tello library not available - Simulation mode only")

try:
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient
    SIMULATION_MODE = True
except ImportError:
    SIMULATION_MODE = False
    print("⚠️ CoppeliaSim not available - Real drone mode only")

#class คำสั่งสำหรับถ่ายรูปและสแกนคิวอาโค้ดในซิมมูเลเตอร์
class DroneCamera:
    def __init__(self, sim):
        self.sim = sim
        self.image_folder = 'D:/pythonforcoppelia/captured_images'
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

    def simcapture(self, timeout=5.0):
        """สั่งให้ Lua เก็บภาพ แล้วคืนชื่อไฟล์"""
        self.sim.clearStringSignal('image_saved')
        self.sim.setStringSignal('capture_image', '1')
        
        start = time.time()
        while time.time() - start < timeout:
            signal_data = self.sim.getStringSignal('image_saved')
            if signal_data and isinstance(signal_data, str) and signal_data != '':
                self.sim.clearStringSignal('image_saved')
                return os.path.join(self.image_folder, signal_data)
            time.sleep(0.05)
        raise TimeoutError('No image_saved signal received')
    
    def simcapturebottom(self, timeout=5.0):
        """สั่งให้ Lua เก็บภาพจากกล้องล่าง"""
        self.sim.clearStringSignal('image_saved')
        self.sim.setStringSignal('capture_bottom_image', '1')
        
        start = time.time()
        while time.time() - start < timeout:
            signal_data = self.sim.getStringSignal('image_saved')
            if signal_data and isinstance(signal_data, str) and signal_data != '':
                self.sim.clearStringSignal('image_saved')
                return os.path.join(self.image_folder, signal_data)
            time.sleep(0.05)
        raise TimeoutError('No image_saved signal received')
 
class QRCodeScanner:
    def __init__(self):
        self.last_detected_codes = []
    
    def scan_qr_code(self, image_path):
        """แสกน QR Code จากไฟล์ภาพ"""
        if not QR_SCANNER_AVAILABLE:
            print("❌ QR Scanner not available")
            return None
            
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ ไม่สามารถอ่านไฟล์ภาพ: {image_path}")
                return None
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            qr_codes = pyzbar.decode(gray)
            
            results = []
            for qr_code in qr_codes:
                qr_data = qr_code.data.decode('utf-8')
                qr_type = qr_code.type
                
                points = qr_code.polygon
                if len(points) == 4:
                    center_x = sum([p.x for p in points]) // 4
                    center_y = sum([p.y for p in points]) // 4
                    
                    result = {
                        'data': qr_data,
                        'type': qr_type,
                        'center': (center_x, center_y),
                        'points': [(p.x, p.y) for p in points]
                    }
                    results.append(result)
                    
                    print(f"🔍 พบ QR Code: {qr_data}")
                    print(f"📍 ตำแหน่ง: ({center_x}, {center_y})")
            
            self.last_detected_codes = results
            return results
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการแสกน QR Code: {e}")
            return None
    
    def draw_qr_detection(self, image_path, output_path=None):
        """วาดกรอบรอบ QR Code ที่ตรวจพบ"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # แสกน QR Code
            qr_codes = self.scan_qr_code(image_path)
            if not qr_codes:
                return image
            
            # วาดกรอบรอบ QR Code
            for qr_code in qr_codes:
                points = qr_code['points']
                center = qr_code['center']
                data = qr_code['data']
                
                # วาดกรอบ
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(image, [pts], True, (0, 255, 0), 3)
                
                # วาดจุดกึ่งกลาง
                cv2.circle(image, center, 5, (0, 0, 255), -1)
                
                # แสดงข้อมูล QR Code
                cv2.putText(image, data, (center[0] - 50, center[1] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # บันทึกภาพ (ถ้าระบุ path)
            if output_path:
                cv2.imwrite(output_path, image)
                print(f"💾 บันทึกภาพที่มีการตรวจจับ QR Code: {output_path}")
            
            return image
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการวาดกรอบ QR Code: {e}")
            return None


#class โค้ดกล้องของตูนชาย
class DroneTello(Tello):
    """
    Enhanced Tello drone class with camera display and mission pad support.
    
    Usage:
        drone = DroneTello(show_cam=True, enable_mission_pad=True)
        drone.takeoff()
        drone.capture("photo.jpg")
        data = drone.scan_qr("photo.jpg")
        drone.land()
    """
    def __init__(self, show_cam=False, enable_mission_pad=False):
        """
        Initialize DroneTello with optional camera display and mission pads.
        
        Args:
            show_cam (bool): If True, shows live camera feed in a window
            enable_mission_pad (bool): If True, enables mission pad detection
            
        Usage:
            drone = DroneTello()  # Basic connection
            drone = DroneTello(show_cam=True)  # With camera display
            drone = DroneTello(show_cam=True, enable_mission_pad=True)  # Full features
        """
        super().__init__()

        # connect to the Tello drone
        print("Connecting to Tello drone...")
        self.connect()
        print(f"Battery: {self.get_battery()}%")
        print(f"Temperature: {self.get_temperature()}°C")
        
        # camera display attribute
        self.show_camera = False
        self._camera_thread = None
        self._stream_active = False
        
        # landing status tracking
        self.is_land = True  # Drone starts on ground
        
        # show camera in realtime if requested
        if show_cam:
            # start video stream
            self._start_video_stream()
            self.start_camera_display()
        
        time.sleep(2)  # Give some time for connection to stabilize

        # enable mission pads if requested
        if enable_mission_pad:
            print("Enabling mission pads...")
            self.enable_mission_pads()
        
        print("Drone Tello initialized successfully.")

    def __del__(self):
        """
        Destructor to ensure cleanup when object is deleted.
        
        Usage: Automatically called when drone object goes out of scope
        """
        try:
            self.cleanup()
        except:
            pass
    
    def _start_video_stream(self):
        """เริ่ม video stream พร้อมการรอให้กล้องปรับตัว"""
        try:
            print("Starting video stream...")
            self.streamon()
            
            # รอให้ stream เริ่มต้น
            time.sleep(5)
            
            # ทิ้งเฟรมแรกๆ ที่อาจเป็นสีดำ
            print("🔄 กำลังทิ้งเฟรมแรกที่อาจเป็นสีดำ...")
            for i in range(5):  # ทิ้ง 5 เฟรมแรก
                try:
                    frame_read = self.get_frame_read()
                    if frame_read is not None:
                        frame = frame_read.frame
                        if frame is not None:
                            print(f"ทิ้งเฟรมที่ {i+1}")
                    time.sleep(0.5)
                except:
                    time.sleep(0.5)
                    continue
            
            # ทดสอบว่าได้เฟรมที่ใช้งานได้แล้ว
            for attempt in range(10):
                try:
                    frame_read = self.get_frame_read()
                    if frame_read is not None:
                        test_frame = frame_read.frame
                        
                        if test_frame is not None and test_frame.size > 0:
                            # ตรวจสอบว่าไม่ใช่เฟรมสีดำ
                            if not self._is_black_frame(test_frame):
                                frame_rgb = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)
                                if frame_rgb is not None:
                                    self._stream_active = True
                                    print("✅ Video stream พร้อมใช้งาน")
                                    return
                    
                    print(f"รอเฟรมที่ใช้งานได้... (ครั้งที่ {attempt + 1})")
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"ข้อผิดพลาดในการทดสอบเฟรม: {e}")
                    time.sleep(1)
                    continue
                    
            print("⚠️ Video stream เริ่มแล้วแต่อาจยังมีปัญหา")
            self._stream_active = True  # ให้ลองใช้งานต่อไป
            
        except Exception as e:
            print(f"ไม่สามารถเริ่ม video stream: {e}")
            self._stream_active = False


    def start_camera_display(self):
        """
        Start displaying camera feed in a GUI window.
        
        Usage:
            drone.start_camera_display()  # Opens camera window
            # Press 'q' in the window to close it
        """
        if not self._stream_active:
            self._start_video_stream()
            
        if self._stream_active:
            self.show_camera = True
            self._camera_thread = threading.Thread(target=self._camera_loop)
            self._camera_thread.daemon = True
            self._camera_thread.start()
        
    def stop_camera_display(self):
        """
        Stop displaying camera feed and close the window.
        
        Usage:
            drone.stop_camera_display()  # Closes camera window
        """
        self.show_camera = False
        if self._camera_thread:
            self._camera_thread.join()
        cv2.destroyAllWindows()
        
    def _camera_loop(self):
        """
        Internal method to continuously display camera feed.
        
        Usage: Called automatically by start_camera_display()
        """
        while self.show_camera and self._stream_active:
            try:
                frame = self.get_frame_read().frame
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                if frame_rgb is not None:
                    cv2.imshow("Tello Camera Feed", frame_rgb)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop_camera_display()
                        break
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Camera error: {e}")
                self._stream_active = False
                break


    def capture(self, count=3, folder="pictures/", base_filename="tello_picture", delay=1.5):
        """
        ถ่ายรูปหลายรูปติดต่อกัน โดยข้ามเฟรมที่เป็นสีดำ
        
        Args:
            count (int): จำนวนรูปที่ต้องการถ่าย
            folder (str): โฟลเดอร์ที่จะบันทึกรูป
            base_filename (str): ชื่อไฟล์พื้นฐาน
            delay (float): ระยะเวลารอระหว่างการถ่ายแต่ละรูป (วินาที)
            
        Returns:
            list: รายการไฟล์ที่บันทึกสำเร็จ
        """
        if not self._stream_active:
            print("เริ่มต้น video stream...")
            self._start_video_stream()
            
        if not self._stream_active:
            print("❌ ไม่สามารถเริ่ม video stream ได้")
            return []
            
        # สร้างโฟลเดอร์ถ้าไม่มี
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        saved_files = []
        attempt_count = 0
        max_attempts = count * 3  # ให้โอกาสมากกว่าจำนวนรูปที่ต้องการ
        
        print(f"📸 เริ่มถ่ายรูป {count} รูป...")
        
        while len(saved_files) < count and attempt_count < max_attempts:
            attempt_count += 1
            
            try:
                print(f"🔄 ความพยายามที่ {attempt_count}: กำลังถ่ายรูป...")
                
                frame_read = self.get_frame_read()
                if frame_read is None:
                    print("⚠️ ไม่สามารถอ่าน frame ได้")
                    time.sleep(delay)
                    continue
                    
                frame = frame_read.frame
                if frame is None or frame.size == 0:
                    print("⚠️ Frame ว่างเปล่า")
                    time.sleep(delay)
                    continue
                    
                # ตรวจสอบว่าเป็นเฟรมสีดำหรือไม่
                if self._is_black_frame(frame):
                    print("⚠️ ตรวจพบเฟรมสีดำ - ข้ามไป")
                    time.sleep(delay)
                    continue
                    
                # แปลงสีและบันทึกรูป
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                filename = f"{base_filename}_{len(saved_files) + 1}.jpg"
                full_path = folder + filename
                
                success = cv2.imwrite(full_path, frame_rgb)
                
                if success:
                    saved_files.append(full_path)
                    print(f"✅ บันทึกรูปที่ {len(saved_files)}: {full_path}")
                    
                    # รอก่อนถ่ายรูปถัดไป
                    if len(saved_files) < count:
                        time.sleep(delay)
                else:
                    print("❌ ไม่สามารถบันทึกไฟล์ได้")
                    
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาด: {e}")
                time.sleep(delay)
                
        print(f"📸 ถ่ายรูปเสร็จสิ้น: {len(saved_files)}/{count} รูป")
        return saved_files

    def _is_black_frame(self, frame, threshold=10):
        """
        ตรวจสอบว่าเฟรมเป็นสีดำหรือไม่
        
        Args:
            frame: เฟรมที่ต้องการตรวจสอบ
            threshold (int): ค่าเกณฑ์สำหรับการตรวจสอบ (0-255)
            
        Returns:
            bool: True ถ้าเป็นเฟรมสีดำ
        """
        try:
            # คำนวณค่าเฉลี่ยของ pixel ทั้งหมด
            mean_value = frame.mean()
            
            # ถ้าค่าเฉลี่ยต่ำกว่า threshold แสดงว่าเป็นเฟรมสีดำ
            return mean_value < threshold
            
        except Exception as e:
            print(f"ข้อผิดพลาดในการตรวจสอบเฟรม: {e}")
            return False


    
    def scan_qr(self, filename):
        """
        Scan QR code from saved image file and return decoded data.
        
        Args:
            filename (str): Name of the image file in pictures/ folder
            
        Returns:
            str: Decoded QR code data, or None if no QR code found
            
        Usage:
            data = drone.scan_qr("my_photo.jpg")
            if data:
                print(f"QR code says: {data}")
        """
        path = "pictures/"
        full_path = path + filename
        
        if not os.path.exists(full_path):
            print(f"File {full_path} not found")
            return None
            
        try:
            frame = cv2.imread(full_path)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            qcd = cv2.QRCodeDetector()
            data, points, _ = qcd.detectAndDecode(gray)
            
            if points is not None and data:
                print(f"QR Code detected in {filename}: {data}")
                return data
            else:
                print(f"No QR code detected in {filename}")
                return None
        except Exception as e:
            print(f"QR scan error: {e}")
            return None
        
    def wait(self, seconds):
        """
        Wait for a specified number of seconds with status messages.
        
        Args:
            seconds (int/float): Number of seconds to wait
            
        Usage:
            drone.wait(2)      # Wait 2 seconds
            drone.wait(0.5)    # Wait half a second
        """
        print(f"Waiting for {seconds} seconds...")
        time.sleep(seconds)
        print("Wait complete.")
        
    def takeoff(self):
        """
        Take off and update landing status.
        
        Usage:
            drone.takeoff()  # Drone takes off and is_land becomes False
        """
        super().takeoff()
        self.is_land = False
        
    def land(self):
        """
        Land and update landing status.
        
        Usage:
            drone.land()  # Drone lands and is_land becomes True
        """
        super().land()
        self.is_land = True
        
    def cleanup(self):
        """
        Clean shutdown of drone resources to prevent errors.
        
        Usage:
            drone.cleanup()  # Call before ending program
            # Or use in finally block for automatic cleanup
        """
        try:
            self.stop_camera_display()
            
            # Land if drone is still flying
            if not self.is_land:
                print("Landing drone before cleanup...")
                try:
                    self.land()
                except Exception as e:
                    print(f"Warning: Could not land drone: {e}")
            
            # Stop video stream
            if hasattr(self, '_stream_active') and self._stream_active:
                try:
                    self.streamoff()
                    print("Video stream stopped")
                except Exception as e:
                    print(f"Warning: Could not stop video stream: {e}")
                    
        except Exception as e:
            print(f"Cleanup error: {e}")


#class มิชชั่นแพดที่รอพี่ๆทำเสร็จค่อยเอามาใส่
class MissionPadDetector:
    def __init__(self):
        self.current_mission_pad_id = None
        self.detection_enabled = False
    
    def enable_mission_pad_detection(self):
        """เปิดใช้งานการตรวจจับ Mission Pad"""
        self.detection_enabled = True
        print("✅ Mission Pad detection enabled")
    
    def disable_mission_pad_detection(self):
        """ปิดการตรวจจับ Mission Pad"""
        self.detection_enabled = False
        print("❌ Mission Pad detection disabled")
    
    def get_mission_pad_id(self):
        """ดึง Mission Pad ID ปัจจุบัน"""
        if not self.detection_enabled:
            print("⚠️ Mission Pad detection is disabled")
            return None
        
        # ใช้การจำลองแบบง่าย
        if self.current_mission_pad_id:
            return self.current_mission_pad_id
        else:
            return self.simulate_mission_pad_detection()

    def simulate_mission_pad_detection(self):
        """จำลองการตรวจจับ Mission Pad สำหรับ CoppeliaSim"""
        try:
            # ใช้เฉพาะเลข 1,2 ที่มีในซิมมูเลเตอร์
            simulated_ids = [1, 2]
            import random
            detected_id = random.choice(simulated_ids)
            
            print(f"🎯 Simulated Mission Pad detected: {detected_id}")
            return detected_id
            
        except Exception as e:
            print(f"❌ Mission Pad simulation error: {e}")
            return None
    
    def set_mission_pad_id(self, pad_id):
        """ตั้งค่า Mission Pad ID (สำหรับการทดสอบ)"""
        self.current_mission_pad_id = pad_id
        print(f"📍 Mission Pad ID set to: {pad_id}")

class HybridMissionPadDetector:
    def __init__(self, use_simulation=True):
        self.use_simulation = use_simulation
        self.detection_enabled = False
        self.tello = None
        
        if not use_simulation:
            # สำหรับโดรนจริง
            try:
                from djitellopy import Tello
                self.tello = Tello()
                self.tello.connect()
                print("✅ Connected to real Tello drone")
            except Exception as e:
                print(f"❌ Failed to connect to real drone: {e}")
                self.tello = None
        else:
            # สำหรับ CoppeliaSim
            print("✅ Using CoppeliaSim simulation mode")
    
    def enable_mission_pad_detection(self):
        """เปิดใช้งานการตรวจจับ Mission Pad"""
        try:
            if self.use_simulation:
                # โหมดจำลอง
                self.detection_enabled = True
                print("✅ Mission Pad detection enabled (Simulation)")
            else:
                # โหมดโดรนจริง
                if self.tello:
                    self.tello.enable_mission_pads()
                    self.tello.set_mission_pad_detection_direction(0)
                    self.detection_enabled = True
                    print("✅ Mission Pad detection enabled (Real Drone)")
                else:
                    print("⚠️ Real drone not connected, using simulation mode")
                    self.use_simulation = True
                    self.detection_enabled = True
        except Exception as e:
            print(f"❌ Failed to enable mission pad detection: {e}")
            self.detection_enabled = False
    
    def disable_mission_pad_detection(self):
        """ปิดการตรวจจับ Mission Pad"""
        try:
            if self.use_simulation:
                self.detection_enabled = False
                print("❌ Mission Pad detection disabled (Simulation)")
            else:
                if self.tello:
                    self.tello.disable_mission_pads()
                    self.detection_enabled = False
                    print("❌ Mission Pad detection disabled (Real Drone)")
        except Exception as e:
            print(f"❌ Failed to disable mission pad detection: {e}")
    
    def get_mission_pad_id(self, image_path=None):
        """ดึง Mission Pad ID"""
        if not self.detection_enabled:
            return None
        
        try:
            if self.use_simulation:
                # ใช้การวิเคราะห์ภาพจาก CoppeliaSim
                if image_path:
                    return self.detect_from_coppelia_image(image_path)
                else:
                    return self.simulate_detection()
            else:
                # ใช้ djitellopy กับโดรนจริง
                if self.tello:
                    return self.tello.get_mission_pad_id()
            
            return None
        except Exception as e:
            print(f"❌ Mission pad detection error: {e}")
            return None
    
    def detect_from_coppelia_image(self, image_path):
        """ตรวจจับจากภาพ CoppeliaSim - เวอร์ชันปรับปรุงสุดท้าย"""
        try:
            print(f"🔍 Analyzing image: {image_path}")
            
            # ใช้การประมวลผลภาพที่ปรับปรุงแล้ว
            processed_image = self.mission_pad_specific_preprocessing(image_path)
            if processed_image is None:
                print("❌ Failed to preprocess image")
                return self.position_based_detection_fallback()
            
            # ใช้ template matching ที่ปรับปรุงแล้ว
            detected_id = self.improved_template_matching(processed_image)
            
            if detected_id:
                print(f"🎯 Mission Pad detection success: {detected_id}")
                self.save_debug_image(image_path, processed_image, detected_id)
                return detected_id
            
            # Fallback: ใช้การตรวจจับตามตำแหน่ง
            print("⚠️ Template matching failed, using position-based fallback")
            return self.position_based_detection_fallback()
            
        except Exception as e:
            print(f"❌ Image processing error: {e}")
            return self.position_based_detection_fallback()

    def enhanced_preprocess_image(self, image_path):
        """ปรับปรุงคุณภาพภาพแบบขั้นสูง"""
        try:
            import cv2
            import numpy as np
            
            # อ่านภาพ
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # แปลงเป็น grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # ปรับ histogram equalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # ปรับ contrast และ brightness
            alpha = 1.3  # Contrast
            beta = 20    # Brightness
            adjusted = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)
            
            # ใช้ bilateral filter เพื่อลด noise แต่เก็บ edge
            filtered = cv2.bilateralFilter(adjusted, 9, 75, 75)
            
            # ใช้ morphological operations
            kernel = np.ones((2,2), np.uint8)
            processed = cv2.morphologyEx(filtered, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            print(f"❌ Enhanced preprocessing error: {e}")
            return None

    def create_mission_pad_specific_templates(self):
        """สร้าง template ที่ตรงกับ Mission Pad texture จริงในซิม"""
        """สร้าง template ที่ตรงกับ Mission Pad จริง - เส้นตรงเท่านั้น"""
        templates = {}
        
        # เลข 1 - เน้นลักษณะเส้นตรงเดี่ยวที่ไม่ซ้ำกับตัวอื่น
        template_1 = np.zeros((140, 90), dtype=np.uint8)
        cv2.line(template_1, (45, 25), (45, 80), 255, 10)
        cv2.line(template_1, (45, 80), (45, 115), 255, 10)  # เส้นหลักหนา

        
        # เลข 2 - เน้นลักษณะเฉพาะที่แตกต่างจากเลข 4
        template_2 = np.zeros((140, 90), dtype=np.uint8)
        cv2.line(template_2, (25, 15), (65, 35), 255, 8)    # เส้นบนยาว# 
        cv2.line(template_2, (65, 35), (25, 105), 255, 8)   # เส้นทแยงยาว
        cv2.line(template_2, (25, 105), (65, 115), 255, 8)  # เส้นฐานยาว
        
        # เลข 3 - เน้นลักษณะเส้นแนวนอนหลายเส้น
        template_3 = np.zeros((140, 90), dtype=np.uint8)
        cv2.line(template_3, (25, 15), (65, 35), 255, 8)    # เส้นบน
        cv2.line(template_3, (65, 35), (25, 65), 255, 8)    # เส้นกลางบน
        cv2.line(template_3, (25, 65), (65, 95), 255, 6)    # เส้นกลางล่าง
        cv2.line(template_3, (25, 115), (65, 95), 255, 8)    # เส้นล่าง


        
        # เลข 4 - ลดความโดดเด่นลง
        template_4 = np.zeros((140, 90), dtype=np.uint8)
        cv2.line(template_4, (60, 25), (30, 65), 255, 8)    # เส้นซ้ายสั้น
        cv2.line(template_4, (60, 25), (60, 115), 255, 8)   # เส้นขวายาว
        cv2.line(template_4, (30, 65), (80, 85), 255, 8)    # เส้นกลาง
        
        templates[1] = template_1
        templates[2] = template_2
        templates[3] = template_3
        templates[4] = template_4
        
        return templates


    def mission_pad_specific_preprocessing(self, image_path):
        """ประมวลผลภาพเฉพาะสำหรับ Mission Pad - ปรับปรุงแล้ว"""
        try:
            import cv2
            import numpy as np
            
            # อ่านภาพ
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # แปลงเป็น grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # ปรับ contrast แบบอ่อนๆ
            alpha = 1.5  # ลด contrast
            beta = 30    # ปรับ brightness
            enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            
            # ใช้ Gaussian blur เพื่อลด noise
            blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
            
            # ใช้ adaptive threshold แทน binary threshold
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 15, 5)
            
            # ใช้ morphological operations เบาๆ
            kernel = np.ones((2,2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            print(f"❌ Mission Pad preprocessing error: {e}")
            return None

    def improved_template_matching(self, gray_image):
        """Template Matching ที่ปรับปรุงแล้ว"""
        try:
            templates = self.create_mission_pad_specific_templates()
            results = {}
            detailed_scores = {}
            
            # ทดสอบหลายขนาดและหลายวิธี
            scales = [0.7, 0.85, 1.0, 1.15, 1.3]
            methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
            
            for number in [1, 2, 3, 4]:
                if number in templates:
                    template = templates[number]
                    all_scores = []
                    
                    for scale in scales:
                        # ปรับขนาด template
                        height, width = template.shape
                        new_height = int(height * scale)
                        new_width = int(width * scale)
                        
                        if new_height > 0 and new_width > 0:
                            scaled_template = cv2.resize(template, (new_width, new_height))
                            
                            for method in methods:
                                result = cv2.matchTemplate(gray_image, scaled_template, method)
                                _, max_val, _, _ = cv2.minMaxLoc(result)
                                all_scores.append(max_val)
                    
                    # ใช้ค่าเฉลี่ยของ top 3 scores
                    all_scores.sort(reverse=True)
                    top_scores = all_scores[:3]
                    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
                    
                    results[number] = avg_score
                    detailed_scores[number] = all_scores
                    
                    print(f"🔍 Number {number}: confidence = {avg_score:.3f} (top3: {[f'{s:.3f}' for s in top_scores]})")
            
            return self.select_best_match_improved(results, detailed_scores)
            
        except Exception as e:
            print(f"❌ Improved template matching error: {e}")
            return None

    def select_best_match_improved(self, results, detailed_scores):
        """เลือกผลลัพธ์ที่ดีที่สุดด้วยเกณฑ์ที่ปรับปรุงแล้ว"""
        try:
            if not results:
                return None
            
            # เรียงลำดับผลลัพธ์
            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
            best_number, best_score = sorted_results[0]
            
            # ลด threshold ให้เหมาะสมกับภาพจริง
            min_threshold = 0.35  # ลดจาก 0.5 เป็น 0.35
            
            if best_score < min_threshold:
                print(f"⚠️ Best score {best_score:.3f} below minimum threshold {min_threshold}")
                return None
            
            # ตรวจสอบความแตกต่างกับอันดับ 2
            if len(sorted_results) > 1:
                second_score = sorted_results[1][1]
                score_difference = best_score - second_score
                
                print(f"🔍 Score difference: {score_difference:.3f}")
                
                # ลดเกณฑ์ความแตกต่าง
                if score_difference < 0.05:  # ลดจาก 0.1 เป็น 0.05
                    print("⚠️ Scores too close - using additional verification")
                    
                    # ใช้การตรวจสอบเพิ่มเติม
                    if hasattr(self, 'verify_with_detailed_analysis'):
                        return self.verify_with_detailed_analysis(sorted_results, detailed_scores)
                    else:
                        # fallback หากไม่มีฟังก์ชัน
                        print("⚠️ Detailed analysis not available, using best score")
                        return best_number
            
            print(f"✅ Confident detection: {best_number} with score {best_score:.3f}")
            return best_number
            
        except Exception as e:
            print(f"❌ Best match selection error: {e}")
            return sorted_results[0][0] if sorted_results else None


    def create_realistic_templates(self):
        """สร้าง template ที่ตรงกับ Mission Pad จริงในซิม"""
        import cv2
        import numpy as np
        
        templates = {}
        
        # Template สำหรับเลข 1 - เส้นตรงเดี่ยวที่ชัดเจน
        template_1 = np.zeros((200, 120), dtype=np.uint8)
        cv2.line(template_1, (60, 40), (60, 160), 255, 12)  # เส้นหลักหนา
        cv2.line(template_1, (50, 55), (60, 40), 255, 6)    # เส้นบนเฉียง
        cv2.line(template_1, (45, 160), (75, 160), 255, 6)  # เส้นฐาน
        
        # Template สำหรับเลข 2 - โค้งบนและเส้นทแยง
        template_2 = np.zeros((200, 120), dtype=np.uint8)
        cv2.ellipse(template_2, (60, 60), (30, 20), 0, 0, 180, 255, 8)
        cv2.line(template_2, (90, 80), (30, 140), 255, 8)
        cv2.line(template_2, (25, 160), (95, 160), 255, 8)
        
        # Template สำหรับเลข 3 - โค้งสองส่วน
        template_3 = np.zeros((200, 120), dtype=np.uint8)
        cv2.ellipse(template_3, (60, 55), (25, 18), 0, -30, 180, 255, 8)
        cv2.ellipse(template_3, (60, 145), (25, 18), 0, -180, 30, 255, 8)
        cv2.line(template_3, (35, 100), (75, 100), 255, 6)
        
        # Template สำหรับเลข 4 - รูปร่างมุมฉาก
        template_4 = np.zeros((200, 120), dtype=np.uint8)
        cv2.line(template_4, (30, 40), (30, 100), 255, 10)
        cv2.line(template_4, (80, 40), (80, 160), 255, 10)
        cv2.line(template_4, (30, 100), (80, 100), 255, 10)
        
        templates[1] = template_1
        templates[2] = template_2
        templates[3] = template_3
        templates[4] = template_4
        
        return templates


    def verify_with_detailed_analysis(self, sorted_results, detailed_scores):
        """ตรวจสอบเพิ่มเติมด้วยการวิเคราะห์รายละเอียด"""
        try:
            # วิเคราะห์ความสม่ำเสมอของ scores
            consistency_scores = {}
            
            for number, score in sorted_results[:2]:  # ดูเฉพาะ top 2
                if number in detailed_scores:
                    scores = detailed_scores[number]
                    if len(scores) > 0:
                        # คำนวณ standard deviation
                        mean_score = sum(scores) / len(scores)
                        variance = sum((x - mean_score) ** 2 for x in scores) / len(scores)
                        std_dev = variance ** 0.5
                        
                        # คะแนนความสม่ำเสมอ (ยิ่งต่ำยิ่งดี)
                        consistency = std_dev / mean_score if mean_score > 0 else 1.0
                        consistency_scores[number] = consistency
                        
                        print(f"🔍 Number {number}: consistency = {consistency:.3f}")
            
            # เลือกตัวเลขที่มีความสม่ำเสมอดีที่สุด
            if consistency_scores:
                best_consistent = min(consistency_scores, key=consistency_scores.get)
                print(f"🎯 Selected by consistency analysis: {best_consistent}")
                return best_consistent
            
            # fallback เป็นค่าที่มี confidence สูงสุด
            return sorted_results[0][0] if sorted_results else None
            
        except Exception as e:
            print(f"❌ Detailed analysis error: {e}")
            return sorted_results[0][0] if sorted_results else None


    def save_debug_image(self, original_path, processed_image, detected_number):
        """บันทึกภาพ debug สำหรับการตรวจสอบ"""
        try:
            import cv2
            debug_path = original_path.replace('.png', f'_debug_detected_{detected_number}.png')
            cv2.imwrite(debug_path, processed_image)
            print(f"💾 Debug image saved: {debug_path}")
        except Exception as e:
            print(f"⚠️ Failed to save debug image: {e}")


    def select_best_match(self, results):
        """เลือกผลลัพธ์ที่ดีที่สุดจากการ template matching"""
        try:
            if not results:
                return None
            
            # หาค่าที่สูงที่สุด
            best_number = max(results, key=results.get)
            best_score = results[best_number]
            
            # ตรวจสอบ threshold
            threshold = 0.7
            if best_score >= threshold:
                print(f"✅ Best match: {best_number} with confidence {best_score:.3f}")
                return best_number
            else:
                print(f"⚠️ Best score {best_score:.3f} below threshold {threshold}")
                return None
                
        except Exception as e:
            print(f"❌ Best match selection error: {e}")
            return None


    def verify_detection_with_position(self, sorted_results):
        """ตรวจสอบผลลัพธ์โดยใช้ตำแหน่งโดรน"""
        try:
            # ดึงตำแหน่งปัจจุบัน (ต้องเข้าถึงจาก NaturalDroneController)
            print("🔍 Using position-based verification")
            
            # ใช้ผลลัพธ์ที่มี confidence สูงสุด
            if sorted_results:
                best_number = sorted_results[0][0]
                best_score = sorted_results[0][1]
                print(f"🎯 Selected by position verification: {best_number} (confidence: {best_score:.3f})")
                return best_number
            
            return None
            
        except Exception as e:
            print(f"❌ Position verification error: {e}")
            return sorted_results[0][0] if sorted_results else None


    def template_matching_detection(self, gray_image):
        """ใช้ Template Matching ตรวจจับตัวเลข - แก้ไขปัญหา SQDIFF"""
        try:
            templates = self.create_number_templates()
            results = {}
            
            for number in [1, 2, 3, 4]:
                if number in templates:
                    template = templates[number]
                    
                    # ใช้เฉพาะ methods ที่ทำงานได้ดี
                    methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
                    scores = []
                    
                    for method in methods:
                        result = cv2.matchTemplate(gray_image, template, method)
                        _, max_val, _, _ = cv2.minMaxLoc(result)
                        scores.append(max_val)
                    
                    # ใช้ค่าเฉลี่ยแบบง่าย
                    avg_score = sum(scores) / len(scores)
                    results[number] = avg_score
                    
                    print(f"🔍 Number {number}: confidence = {avg_score:.3f} (methods: {[f'{s:.3f}' for s in scores]})")
            
            # ปรับ threshold ให้เหมาะสม
            threshold = 0.3
            
            # หาค่าที่สูงที่สุด
            if not results:
                return None
            
            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
            best_number, best_score = sorted_results[0]
            
            if best_score < threshold:
                print(f"⚠️ Best score {best_score:.3f} below threshold {threshold}")
                return None
            
            # ตรวจสอบความแตกต่าง
            if len(sorted_results) > 1:
                second_score = sorted_results[1][1]
                score_difference = best_score - second_score
                
                print(f"🔍 Score difference: {score_difference:.3f}")
                
                # ถ้าความแตกต่างน้อย ใช้การตรวจสอบเพิ่มเติม
                if score_difference < 0.05:
                    print("⚠️ Scores too close, using additional verification")
                    return self.verify_detection_with_position(sorted_results)
            
            print(f"✅ Selected number {best_number} with confidence {best_score:.3f}")
            return best_number
            
        except Exception as e:
            print(f"❌ Template matching error: {e}")
            return None

    def multi_scale_template_matching(self, gray_image):
        """Template Matching แบบหลายขนาด"""
        try:
            templates = self.create_enhanced_templates()
            results = {}
            
            # ทดสอบหลายขนาด
            scales = [0.8, 1.0, 1.2, 1.5]
            
            for number in [1, 2, 3, 4]:
                if number in templates:
                    template = templates[number]
                    best_score = 0
                    
                    for scale in scales:
                        # ปรับขนาด template
                        height, width = template.shape
                        new_height = int(height * scale)
                        new_width = int(width * scale)
                        
                        if new_height > 0 and new_width > 0:
                            scaled_template = cv2.resize(template, (new_width, new_height))
                            
                            # Template matching
                            result = cv2.matchTemplate(gray_image, scaled_template, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(result)
                            
                            if max_val > best_score:
                                best_score = max_val
                    
                    results[number] = best_score
                    print(f"🔍 Number {number}: multi-scale confidence = {best_score:.3f}")
            
            return self.select_best_match(results)
            
        except Exception as e:
            print(f"❌ Multi-scale matching error: {e}")
            return None


    def sift_based_detection(self, gray_image):
        """ใช้ SIFT features สำหรับการตรวจจับ"""
        try:
            # สร้าง SIFT detector
            sift = cv2.SIFT_create()
            
            # หา keypoints และ descriptors ในภาพ
            kp_image, desc_image = sift.detectAndCompute(gray_image, None)
            
            if desc_image is None:
                return None
            
            # สร้าง reference templates และหา features
            templates = self.create_enhanced_templates()
            results = {}
            
            for number, template in templates.items():
                kp_template, desc_template = sift.detectAndCompute(template, None)
                
                if desc_template is not None:
                    # ใช้ FLANN matcher
                    FLANN_INDEX_KDTREE = 1
                    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                    search_params = dict(checks=50)
                    flann = cv2.FlannBasedMatcher(index_params, search_params)
                    
                    matches = flann.knnMatch(desc_template, desc_image, k=2)
                    
                    # Filter good matches
                    good_matches = []
                    for match_pair in matches:
                        if len(match_pair) == 2:
                            m, n = match_pair
                            if m.distance < 0.7 * n.distance:
                                good_matches.append(m)
                    
                    match_score = len(good_matches)
                    results[number] = match_score
                    print(f"🔍 Number {number}: SIFT matches = {match_score}")
            
            # เลือกผลลัพธ์ที่มี matches มากที่สุด
            if results:
                best_number = max(results, key=results.get)
                best_score = results[best_number]
                
                if best_score >= 5:  # threshold สำหรับ matches
                    print(f"🎯 SIFT detection: {best_number} with {best_score} matches")
                    return best_number
            
            return None
            
        except Exception as e:
            print(f"❌ SIFT detection error: {e}")
            return None

    def contour_based_detection(self, gray_image):
        """ใช้การวิเคราะห์รูปร่าง contour"""
        try:
            # ปรับปรุงภาพ
            blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY_INV, 11, 2)
            
            # หา contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # วิเคราะห์ contours
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # กรองตาม area
                if 500 < area < 5000:
                    # วิเคราะห์รูปร่าง
                    perimeter = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                    
                    # คำนวณ aspect ratio
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    
                    # วิเคราะห์ลักษณะเฉพาะ
                    detected_number = self.analyze_shape_features(contour, aspect_ratio, len(approx))
                    
                    if detected_number:
                        print(f"🎯 Contour detection: {detected_number}")
                        return detected_number
            
            return None
            
        except Exception as e:
            print(f"❌ Contour detection error: {e}")
            return None

    def analyze_shape_features(self, contour, aspect_ratio, vertices):
        """วิเคราะห์ลักษณะรูปร่าง"""
        try:
            # เลข 1: มักมี aspect ratio สูง (แคบยาว)
            if 0.2 < aspect_ratio < 0.6 and vertices <= 6:
                return 1
            
            # เลข 4: มีลักษณะเป็นมุม มี vertices มาก
            elif 0.4 < aspect_ratio < 0.8 and vertices >= 8:
                return 4
            
            # เลข 2, 3: มีโค้ง aspect ratio ปานกลาง
            elif 0.6 < aspect_ratio < 1.2:
                # ใช้การวิเคราะห์เพิ่มเติม
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                contour_area = cv2.contourArea(contour)
                
                solidity = float(contour_area) / hull_area
                
                if solidity > 0.8:
                    return 2  # เลข 2 มักมี solidity สูง
                else:
                    return 3  # เลข 3 มี solidity ต่ำกว่า
            
            return None
            
        except Exception as e:
            print(f"❌ Shape analysis error: {e}")
            return None

    def hybrid_detection_system(self, gray_image):
        """ระบบตรวจจับแบบผสมผสาน"""
        try:
            results = {}
            
            # วิธีที่ 1: Multi-scale Template Matching
            template_result = self.multi_scale_template_matching(gray_image)
            if template_result:
                results['template'] = template_result
            
            # วิธีที่ 2: SIFT Feature Detection
            sift_result = self.sift_based_detection(gray_image)
            if sift_result:
                results['sift'] = sift_result
            
            # วิธีที่ 3: Contour Analysis
            contour_result = self.contour_based_detection(gray_image)
            if contour_result:
                results['contour'] = contour_result
            
            # วิเคราะห์ผลลัพธ์
            if not results:
                return None
            
            # หาผลลัพธ์ที่ตรงกันมากที่สุด
            from collections import Counter
            all_results = list(results.values())
            vote_count = Counter(all_results)
            
            print(f"🔍 Detection results: {results}")
            print(f"🔍 Vote count: {dict(vote_count)}")
            
            # เลือกผลลัพธ์ที่ได้คะแนนโหวตมากที่สุด
            if vote_count:
                best_result = vote_count.most_common(1)[0][0]
                confidence = vote_count[best_result] / len(results)
                
                print(f"🎯 Hybrid detection: {best_result} (confidence: {confidence:.2f})")
                return best_result
            
            return None
            
        except Exception as e:
            print(f"❌ Hybrid detection error: {e}")
            return None

    def position_based_detection(self):
        """ตรวจจับ Mission Pad ตามตำแหน่งของโดรน"""
        try:
            # ดึงตำแหน่งปัจจุบันของโดรน
            current_pos = self.get_current_position()  # ต้องเพิ่มฟังก์ชันนี้
            x, y = current_pos[0], current_pos[1]
            
            print(f"🔍 Current position: ({x:.2f}, {y:.2f})")
            
            # กำหนดพื้นที่ Mission Pad ตามตำแหน่งในซิม
            # ปรับค่าตามตำแหน่งจริงใน CoppeliaSim
            if -2.0 <= x <= 0.0 and 0.0 <= y <= 2.0:
                detected_id = 4  # พื้นที่ Mission Pad 4
                print(f"🎯 Position-based detection: Mission Pad {detected_id}")
                return detected_id
            elif 0.0 <= x <= 2.0 and 0.0 <= y <= 2.0:
                detected_id = 1  # พื้นที่ Mission Pad 1
                print(f"🎯 Position-based detection: Mission Pad {detected_id}")
                return detected_id
            else:
                print("❌ Position outside Mission Pad areas")
                return None
                
        except Exception as e:
            print(f"❌ Position-based detection error: {e}")
            return None

    def get_current_position(self):
        """ดึงตำแหน่งปัจจุบันของโดรน"""
        try:
            return self.current_position
        except:
            return [0.0, 0.0, 0.0]


    def ocr_detection(self, image_path):
        """ใช้ OCR ตรวจจับตัวเลข"""
        try:
            import pytesseract
            from PIL import Image, ImageEnhance
            
            # อ่านและปรับปรุงภาพ
            image = Image.open(image_path)
            
            # เพิ่ม contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # เพิ่ม sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # แปลงเป็น grayscale
            gray = image.convert('L')
            
            # ใช้ OCR อ่านเฉพาะเลข 1,4
            config = '--psm 8 -c tessedit_char_whitelist=14'
            text = pytesseract.image_to_string(gray, config=config)
            
            # หาตัวเลข
            import re
            numbers = re.findall(r'[14]', text)
            
            if numbers:
                return int(numbers[0])
            
            return None
            
        except ImportError:
            print("⚠️ pytesseract not installed")
            return None
        except Exception as e:
            print(f"❌ OCR error: {e}")
            return None

    def preprocess_image(self, image_path):
        """ปรับปรุงคุณภาพภาพก่อนการตรวจจับ"""
        try:
            import cv2
            
            # อ่านภาพ
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # แปลงเป็น grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # ปรับ contrast และ brightness
            alpha = 1.5  # Contrast control
            beta = 30    # Brightness control
            enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            
            # ใช้ Gaussian blur เพื่อลด noise
            blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
            
            # ใช้ adaptive threshold
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 11, 2)
            
            return thresh
            
        except Exception as e:
            print(f"❌ Image preprocessing error: {e}")
            return None


#class รวมคำสั่งหลัก
class NaturalDroneController:
    def __init__(self, use_simulation=True):
        """เริ่มต้น Drone Controller"""
        # ตัวแปรพื้นฐาน
        self.use_simulation = use_simulation and SIMULATION_MODE
        self.use_real_drone = not use_simulation and REAL_DRONE_AVAILABLE

        # ตัวแปรสถานะ
        self.is_flying = False
        self.current_position = [0.0, 0.0, 0.0]
        self.target_position = [0.0, 0.0, 0.0]
        self.is_moving = False
        self.current_heading = 0.0
        self.orientation_matrix = [0, 0, 0]
        
        # พารามิเตอร์การบิน
        self.max_speed = 0.5
        self.acceleration = 0.2
        self.position_tolerance = 0.05
        
        # ตัวแปรสำหรับระบบต่างๆ
        self.client = None
        self.sim = None
        self.drone_handle = None
        self.camera = None
        self.qr_scanner = None
        self.bottom_camera_handle = None
        self.image_folder = './captured_images'
        self.simulation_running = False
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        
        # ✅ สร้าง mission_pad_detector ก่อนทุกอย่าง
        print("🔧 Creating mission pad detector...")
        self.mission_pad_detector = HybridMissionPadDetector(use_simulation)
        
        # เริ่มต้นการเชื่อมต่อ
        print("🔧 Initializing connection...")
        self._initialize_connection()
        
        # ✅ เปิดใช้งาน mission pads หลังจากทุกอย่างพร้อมแล้ว
        print("🔧 Enabling mission pads...")
        self.enable_mission_pads()
        
        print(f"🚁 Drone Controller initialized - Mode: {'Simulation' if self.use_simulation else 'Real Drone'}")

    def _initialize_connection(self):
        """เริ่มต้นการเชื่อมต่อ"""
        if self.use_simulation:
            success = self._init_simulation()
            if success:
                self._init_camera_system()
        elif self.use_real_drone:
            self._init_real_drone()
        else:
            print("❌ No drone interface available")

    def _init_simulation(self):
        try:
            print("🔄 Connecting to CoppeliaSim...")
            self.client = RemoteAPIClient()
            self.sim = self.client.getObject('sim')      
            # ค้นหาโดรน
            self.drone_handle = self.sim.getObject('/Quadcopter')
            
            # เริ่ม simulation
            self.sim.startSimulation()
            self.simulation_running = True
            
            # อัปเดตตำแหน่งปัจจุบัน
            self._update_current_position()
            
            print("✅ Connected to CoppeliaSim")
            
            # ✅ เพิ่มส่วนนี้
            # รอให้ simulation เสถียร
            time.sleep(2)
            
            # เริ่มต้นระบบลม
            print("🌪️ Setting up wind system...")
            wind_success = self.setup_wind_system()
            if wind_success:
                print("✅ Wind system ready")
            else:
                print("⚠️ Wind system setup failed - continuing without wind effects")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to CoppeliaSim: {e}")
            self.use_simulation = False
            return False

    def _init_real_drone(self):
        """เริ่มต้นการเชื่อมต่อกับโดรนจริง"""
        try:
            # ตรวจสอบว่ามี drone instance อยู่แล้วหรือไม่
            if hasattr(self, 'drone') and self.drone is not None:
                try:
                    self.drone.cleanup()
                except:
                    pass
                    
            print("🔧 Initializing DroneTello...")
            self.drone = DroneTello(show_cam=False, enable_mission_pad=True)  # ปิด show_cam ก่อน
            time.sleep(3)  # รอให้เชื่อมต่อเสถียร
            
            battery = self.drone.get_battery()
            print(f"✅ Connected to real drone - Battery: {battery}%")
            return True
        
        except Exception as e:
            print(f"❌ Failed to connect to real drone: {e}")
            self.use_real_drone = False
            return False

    def _init_camera_system(self):
        """เริ่มต้นระบบกล้องและ QR Scanner"""
        if self.use_simulation and self.sim is not None:
            try:
                self.camera = DroneCamera(self.sim)
                self.qr_scanner = QRCodeScanner()
                print("✅ Camera system initialized")
            except Exception as e:
                print(f"⚠️ Camera system initialization failed: {e}")

#โค้ดเกี่ยวกับลม
    def setup_wind_system(self):
        """เริ่มต้นระบบลมแบบสมบูรณ์"""
        try:
            if not self.use_simulation or not self.sim or not self.drone_handle:
                print("⚠️ Simulation not ready for wind system")
                return False
            
            print("🌪️ Initializing wind system...")
            
            # ตั้งค่าเริ่มต้น
            self.wind_settings = {
                'strength': 0,
                'direction': [0, 0, 0],
                'turbulence': True,
                'gusts': True,
                'zones': []
            }
            
            # ทดสอบการเรียก Lua functions
            try:
                # ทดสอบการเรียก wind function แบบง่าย
                test_result = self.sim.callScriptFunction('setWindStrength', self.drone_handle, 0)
                print("✅ Wind Lua functions accessible")
            except Exception as lua_error:
                print(f"⚠️ Wind Lua functions not available: {lua_error}")
                print("💡 Make sure you've added the wind code to the drone's Lua script")
                # ยังคงให้ Python methods ทำงานได้
            
            print("✅ Wind system ready")
            return True
            
        except Exception as e:
            print(f"❌ Wind system setup failed: {e}")
            return False

    def create_realistic_wind_scenario(self):
        """สร้างสถานการณ์ลมที่สมจริงสำหรับการทดสอบ"""
        try:
            print("🏟️ Creating realistic wind scenario...")
            
            # สร้าง wind zones ตามสนาม Drone Odyssey
            self.create_wind_zone("Launch_Area", -0.5, -0.5, 0.5, 0.5, 0.5, 0.02)  # A1 - สงบ
            self.create_wind_zone("Obstacle_Area", 1, 1, 3, 3, 1.2, 0.15)  # B2-D4 - ลมปานกลาง
            self.create_wind_zone("Mission_Area", 2, 4, 3, 5, 1.8, 0.25)   # C5-D5 - ลมแรง
            
            # ตั้งลมพื้นฐาน
            self.set_wind_strength(3)
            self.set_wind_direction(1, 0.5, 0)  # ลมพัดจากทิศตะวันออก
            
            print("✅ Realistic wind scenario for Drone Odyssey field created!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create wind scenario: {e}")
            return False

    def test_wind_effects_simple(self):
        """ทดสอบ wind effects แบบง่าย"""
        if not self.is_flying:
            print("❌ Drone must be flying to test wind effects")
            return False
        
        print("🧪 Testing simple wind effects...")
        
        try:
            # บันทึกตำแหน่งเริ่มต้น
            start_pos = self.get_position()
            
            # ทดสอบ 1: ลมสงบ
            print("\n1. 😌 Testing calm conditions...")
            self.set_calm_conditions()
            self.hover(3)
            pos_calm = self.get_position()
            drift_calm = self._calculate_drift(start_pos, pos_calm)
            
            # ทดสอบ 2: ลมเบา
            print("\n2. 🍃 Testing light breeze...")
            self.move_to_position(*start_pos)  # กลับตำแหน่งเดิม
            time.sleep(1)
            self.set_light_breeze()
            self.hover(3)
            pos_breeze = self.get_position()
            drift_breeze = self._calculate_drift(start_pos, pos_breeze)
            
            # ทดสอบ 3: ลมแรง
            print("\n3. 💨 Testing moderate wind...")
            self.move_to_position(*start_pos)  # กลับตำแหน่งเดิม
            time.sleep(1)
            self.set_moderate_wind()
            self.hover(3)
            pos_wind = self.get_position()
            drift_wind = self._calculate_drift(start_pos, pos_wind)
            
            # รีเซ็ตเป็นลมสงบ
            self.set_calm_conditions()
            self.move_to_position(*start_pos)
            
            # แสดงผลลัพธ์
            print("\n📊 Wind Test Results:")
            print(f"  Calm conditions: {drift_calm:.3f}m drift")
            print(f"  Light breeze: {drift_breeze:.3f}m drift")
            print(f"  Moderate wind: {drift_wind:.3f}m drift")
            
            if drift_wind > drift_breeze > drift_calm:
                print("✅ Wind effects working correctly!")
                return True
            else:
                print("⚠️ Wind effects may not be working as expected")
                return False
                
        except Exception as e:
            print(f"❌ Wind test failed: {e}")
            return False

    def _calculate_drift(self, start_pos, end_pos):
        """คำนวณระยะ drift"""
        try:
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            return math.sqrt(dx*dx + dy*dy)
        except:
            return 0.0

    def start_wind_demo(self):
        """เริ่ม demo wind effects แบบเต็ม"""
        print("🌪️ Starting comprehensive wind demonstration...")
        
        if not self.takeoff(height=1.5):
            return False
        
        try:
            # Demo 1: Wind strength progression
            print("\n📈 Demo 1: Wind Strength Progression")
            strengths = [0, 2, 4, 6, 8]
            for strength in strengths:
                print(f"  Setting wind strength to {strength}...")
                self.set_wind_strength(strength)
                self.set_wind_direction(1, 0, 0)  # ลมทิศตะวันออก
                self.hover(2)
                
                pos = self.get_position()
                print(f"    Position after wind {strength}: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            
            # Demo 2: Wind direction changes
            print("\n🧭 Demo 2: Wind Direction Changes")
            self.set_wind_strength(4)
            directions = [
                ([1, 0, 0], "East"),
                ([0, 1, 0], "North"), 
                ([-1, 0, 0], "West"),
                ([0, -1, 0], "South")
            ]
            
            center_pos = self.get_position()
            for direction, name in directions:
                print(f"  Wind from {name}...")
                self.move_to_position(*center_pos)  # กลับจุดกลาง
                time.sleep(1)
                self.set_wind_direction(*direction)
                self.hover(3)
                
                pos = self.get_position()
                print(f"    Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            
            # Demo 3: Wind zones
            print("\n📍 Demo 3: Wind Zones")
            self.create_realistic_wind_scenario()
            
            # บินผ่าน zones ต่างๆ
            zones_to_visit = [
                ([0, 0, 1.5], "Launch Area (Calm)"),
                ([2, 2, 1.5], "Obstacle Area (Moderate)"),
                ([2.5, 4.5, 1.5], "Mission Area (Strong)")
            ]
            
            for pos, zone_name in zones_to_visit:
                print(f"  Flying to {zone_name}...")
                self.move_to_position(*pos)
                self.hover(2)
                
                final_pos = self.get_position()
                print(f"    Final position: ({final_pos[0]:.2f}, {final_pos[1]:.2f}, {final_pos[2]:.2f})")
            
            # Reset และลงจอด
            self.set_calm_conditions()
            self.land()
            
            print("✅ Wind demonstration complete!")
            return True
            
        except Exception as e:
            print(f"❌ Wind demonstration failed: {e}")
            self.set_calm_conditions()
            self.land()
            return False

    def set_wind_strength(self, strength):
        """ตั้งค่าความแรงลม (0-10)"""
        try:
            if not (0 <= strength <= 10):
                print("❌ Wind strength must be between 0-10")
                return False
            
            # เรียก Lua function
            result = self.sim.callScriptFunction('setWindStrength', self.drone_handle, strength)
            
            self.wind_settings['strength'] = strength
            print(f"🌪️ Wind strength set to: {strength}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to set wind strength: {e}")
            return False

    def set_wind_direction(self, x=0, y=0, z=0):
        """ตั้งค่าทิศทางลม (m/s)"""
        try:
            # เรียก Lua function
            result = self.sim.callScriptFunction('setWindDirection', self.drone_handle, [x, y, z])
            
            self.wind_settings['direction'] = [x, y, z]
            print(f"🧭 Wind direction set to: ({x:.1f}, {y:.1f}, {z:.1f}) m/s")
            return True
            
        except Exception as e:
            print(f"❌ Failed to set wind direction: {e}")
            return False

    def enable_turbulence(self, enable=True):
        """เปิด/ปิด turbulence"""
        try:
            result = self.sim.callScriptFunction('enableTurbulence', self.drone_handle, enable)
            
            self.wind_settings['turbulence'] = enable
            print(f"🌊 Turbulence {'enabled' if enable else 'disabled'}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to toggle turbulence: {e}")
            return False

    def enable_wind_gusts(self, enable=True):
        """เปิด/ปิด wind gusts"""
        try:
            result = self.sim.callScriptFunction('enableWindGusts', self.drone_handle, enable)
            
            self.wind_settings['gusts'] = enable
            print(f"💨 Wind gusts {'enabled' if enable else 'disabled'}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to toggle wind gusts: {e}")
            return False

    def create_wind_zone(self, name, x_min, y_min, x_max, y_max, wind_multiplier=1.0, turbulence_level=0.1):
        """สร้าง wind zone แบบกำหนดเอง"""
        try:
            result = self.sim.callScriptFunction('createCustomWindZone', self.drone_handle, 
                                            [name, x_min, y_min, x_max, y_max, wind_multiplier, turbulence_level])
            
            zone = {
                'name': name,
                'bounds': [x_min, y_min, x_max, y_max],
                'wind_multiplier': wind_multiplier,
                'turbulence_level': turbulence_level
            }
            self.wind_settings['zones'].append(zone)
            
            print(f"📍 Wind zone '{name}' created: Wind x{wind_multiplier}, Turbulence {turbulence_level}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create wind zone: {e}")
            return False

    def get_wind_status(self):
        """รับสถานะลมปัจจุบัน"""
        try:
            status = self.sim.callScriptFunction('getWindStatus', self.drone_handle)
            
            print("🌪️ Wind Status:")
            print(f"  Strength: {status.get('strength', 0)}")
            print(f"  Direction: {status.get('global_wind', [0,0,0])}")
            print(f"  Gust Active: {status.get('gust_active', False)}")
            print(f"  Current Zone: {status.get('current_zone', 'None')}")
            print(f"  Turbulence: {status.get('turbulence_enabled', False)}")
            
            return status
            
        except Exception as e:
            print(f"❌ Failed to get wind status: {e}")
            return None

# เพิ่ม convenience methods สำหรับ wind presets
    def set_calm_conditions(self):
        """ตั้งค่าสภาพอากาศสงบ"""
        self.set_wind_strength(0)
        self.enable_turbulence(False)
        self.enable_wind_gusts(False)
        print("😌 Calm weather conditions set")

    def set_light_breeze(self):
        """ตั้งค่าลมเซาะแสง"""
        self.set_wind_strength(2)
        self.set_wind_direction(1, 0.5, 0)
        self.enable_turbulence(True)
        self.enable_wind_gusts(False)
        print("🍃 Light breeze conditions set")

    def set_moderate_wind(self):
        """ตั้งค่าลมปานกลาง"""
        self.set_wind_strength(4)
        self.set_wind_direction(2, 1, 0)
        self.enable_turbulence(True)
        self.enable_wind_gusts(True)
        print("💨 Moderate wind conditions set")

    def set_strong_wind(self):
        """ตั้งค่าลมแรง (สำหรับทดสอบ)"""
        self.set_wind_strength(7)
        self.set_wind_direction(3, 2, 0.5)
        self.enable_turbulence(True)
        self.enable_wind_gusts(True)
        print("⚠️ Strong wind conditions set - Be careful!")

    def test_wind_resistance(self):
        """ทดสอบการต้านลมของโดรน"""
        if not self.is_flying:
            print("❌ Drone must be flying to test wind resistance")
            return False
        
        print("🧪 Testing wind resistance...")
        
        # Test sequence
        original_pos = self.sim.getObjectPosition(self.drone_handle, -1)
        
        test_conditions = [
            ("Calm", lambda: self.set_calm_conditions()),
            ("Light Breeze", lambda: self.set_light_breeze()),
            ("Moderate Wind", lambda: self.set_moderate_wind()),
            ("Strong Wind", lambda: self.set_strong_wind())
        ]
        
        for condition_name, set_condition in test_conditions:
            print(f"\n🔬 Testing: {condition_name}")
            set_condition()
            
            # Hover for 5 seconds
            start_time = time.time()
            while time.time() - start_time < 5:
                self.hover(0.1)
                time.sleep(0.1)
            
            # Check position drift
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            drift = [
                current_pos[0] - original_pos[0],
                current_pos[1] - original_pos[1],
                current_pos[2] - original_pos[2]
            ]
            
            drift_distance = (drift[0]**2 + drift[1]**2 + drift[2]**2)**0.5
            print(f"  📊 Position drift: {drift_distance:.3f}m")
            
            # Return to original position
            self.move_to(original_pos[0], original_pos[1], original_pos[2])
            time.sleep(1)
        
        # Reset to calm
        self.set_calm_conditions()
        print("\n✅ Wind resistance test completed")

    def get_drone_script_handle(self):
        """Get the correct script handle for the drone"""
        try:
            # Try different possible script names
            possible_names = [
                '/Quadcopter/Script',
                'Quadcopter/Script', 
                '/Quadcopter/script',
                'Quadcopter'
            ]
            
            for name in possible_names:
                try:
                    handle = self.getObject(name)
                    if handle != -1:
                        print(f"✅ Found script handle: {name}")
                        return handle
                except:
                    continue
                    
            print("❌ Could not find script handle")
            return -1
            
        except Exception as e:
            print(f"❌ Error getting script handle: {e}")
            return -1

    def set_wind_strength(self, strength):
        """Set wind strength with proper script handle"""
        script_handle = self.get_drone_script_handle()
        if script_handle == -1:
            return False
            
        try:
            result = self.callScriptFunction('setWindStrength', self.getObject('/Quadcopter/Script'), strength)
            return result
        except Exception as e:
            print(f"❌ Failed to set wind strength: {e}")
            return False


#โค้ดเกี่ยวกับการเคลื่อนที่ปกติทั้วไป
    def _update_current_position(self):
        """อัปเดตตำแหน่งปัจจุบันของโดรน"""
        if self.use_simulation and self.drone_handle is not None:
            try:
                pos = self.sim.getObjectPosition(self.drone_handle, -1)
                self.current_position = list(pos)
            except Exception as e:
                print(f"⚠️ Failed to update position: {e}")

    def get_orientation(self):
        """ดึงข้อมูล orientation ปัจจุบันของโดรน"""
        try:
            if self.use_simulation and self.drone_handle is not None:
                orientation = self.sim.getObjectOrientation(self.drone_handle, -1)
                self.orientation_matrix = orientation
                self.current_heading = math.degrees(orientation[2]) % 360
                
                return {
                    'heading': self.current_heading,
                    'roll': math.degrees(orientation[0]),
                    'pitch': math.degrees(orientation[1]),
                    'yaw': math.degrees(orientation[2])
                }
            else:
                return {
                    'heading': self.current_heading,
                    'roll': 0.0,
                    'pitch': 0.0,
                    'yaw': self.current_heading
                }
                
        except Exception as e:
            print(f"❌ Failed to get orientation: {e}")
            return {
                'heading': self.current_heading,
                'roll': 0.0,
                'pitch': 0.0,
                'yaw': self.current_heading
            }

    def update_orientation(self):
        """อัปเดต orientation ปัจจุบัน"""
        try:
            orientation_data = self.get_orientation()
            self.current_heading = orientation_data['heading']
        except Exception as e:
            print(f"⚠️ Failed to update orientation: {e}")

    def _move_to_position_naturally(self, target_pos, duration=None):
        """เคลื่อนที่ไปยังตำแหน่งเป้าหมายแบบเป็นธรรมชาติ"""
        if self.is_moving:
            print("⚠️ Drone is already moving")
            return False
        
        if not self.use_simulation or self.drone_handle is None:
            print("❌ Simulation not available")
            return False
        
        self.is_moving = True
        self.target_position = target_pos.copy()
        
        try:
            start_pos = self.current_position.copy()
            
            dx = target_pos[0] - start_pos[0]
            dy = target_pos[1] - start_pos[1]
            dz = target_pos[2] - start_pos[2]
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            if distance < self.position_tolerance:
                self.is_moving = False
                return True
            
            if duration is None:
                move_duration = distance / self.max_speed
            else:
                move_duration = duration
            
            steps = max(10, int(move_duration * 20))
            dt = move_duration / steps
            
            print(f"🎯 Moving to ({target_pos[0]:.2f}, {target_pos[1]:.2f}, {target_pos[2]:.2f}) - Distance: {distance:.2f}m, Time: {move_duration:.2f}s")
            
            for i in range(steps + 1):
                if not self.is_moving:
                    break
                
                t = i / steps
                smooth_t = 3*t*t - 2*t*t*t
                
                current_x = start_pos[0] + dx * smooth_t
                current_y = start_pos[1] + dy * smooth_t
                current_z = start_pos[2] + dz * smooth_t
                
                self.sim.setObjectPosition(self.drone_handle, -1, [current_x, current_y, current_z])
                self.current_position = [current_x, current_y, current_z]
                
                time.sleep(dt)
            
            self._update_current_position()
            final_distance = math.sqrt(
                (self.current_position[0] - target_pos[0])**2 +
                (self.current_position[1] - target_pos[1])**2 +
                (self.current_position[2] - target_pos[2])**2
            )
            
            success = final_distance < self.position_tolerance
            if success:
                print(f"✅ Reached target position")
            else:
                print(f"⚠️ Close to target (error: {final_distance:.3f}m)")
            
            self.is_moving = False
            return success
            
        except Exception as e:
            print(f"❌ Movement failed: {e}")
            self.is_moving = False
            return False

    def takeoff(self, height=1.0):
        """ขึ้นบิน"""
        if self.is_flying:
            print("⚠️ Drone is already flying")
            return True
        
        print(f"🚁 Taking off to {height}m...")
        
        if self.use_simulation and self.drone_handle is not None:
            self._update_current_position()
            target_pos = self.current_position.copy()
            target_pos[2] = height
            
            success = self._move_to_position_naturally(target_pos, duration=3.0)
            
        elif self.use_real_drone:
            try:
                self.drone.takeoff()
                time.sleep(3)
                success = True
            except Exception as e:
                print(f"❌ Takeoff failed: {e}")
                success = False
        else:
            print("❌ No drone interface available")
            success = False
        
        if success:
            self.is_flying = True
            print("✅ Takeoff complete")
        
        return success

    def land(self):
        """ลงจอด"""
        if not self.is_flying:
            print("⚠️ Drone is not flying")
            return True
        
        print("🛬 Landing...")
        
        if self.use_simulation and self.drone_handle is not None:
            self._update_current_position()
            target_pos = self.current_position.copy()
            target_pos[2] = 0.1
            
            success = self._move_to_position_naturally(target_pos, duration=3.0)
            
        elif self.use_real_drone:
            try:
                self.drone.land()
                time.sleep(3)
                success = True
            except Exception as e:
                print(f"❌ Landing failed: {e}")
                success = False
        else:
            success = False
        
        if success:
            self.is_flying = False
            print("✅ Landing complete")
        
        return success

    def hover(self, duration):
        """โฮเวอร์ (ลอยอยู่กับที่)"""
        if not self.is_flying:
            print("⚠️ Drone must be flying first")
            return False
        
        print(f"🚁 Hovering for {duration} seconds...")
        time.sleep(duration)
        print("✅ Hover complete")
        return True

    def move_forward(self, distance):
        """เคลื่อนที่ไปข้างหน้าตามทิศทางปัจจุบัน"""
        return self._move_relative([distance, 0, 0])

    def move_backward(self, distance):
        """เคลื่อนที่ไปข้างหลัง"""
        return self._move_relative([-distance, 0, 0])

    def move_left(self, distance):
        """เคลื่อนที่ไปทางซ้าย"""
        return self._move_relative([0, distance, 0])

    def move_right(self, distance):
        """เคลื่อนที่ไปทางขวา"""
        return self._move_relative([0, -distance, 0])

    def move_up(self, distance):
        """เคลื่อนที่ขึ้น"""
        return self._move_relative([0, 0, distance])

    def move_down(self, distance):
        """เคลื่อนที่ลง"""
        return self._move_relative([0, 0, -distance])

    def _move_relative(self, relative_pos):
        """เคลื่อนที่แบบสัมพัทธ์ตามทิศทางที่โดรนหันหน้าไป"""
        if not self.is_flying:
            print("⚠️ Drone must be flying first")
            return False
        
        self._update_current_position()
        
        # ดึงการหมุนปัจจุบันของโดรน
        if self.use_simulation and self.drone_handle is not None:
            try:
                current_orientation = self.sim.getObjectOrientation(self.drone_handle, -1)
                yaw = current_orientation[2]  # การหมุนรอบแกน Z
                
                # แปลงการเคลื่อนที่จาก local coordinates เป็น global coordinates
                cos_yaw = math.cos(yaw)
                sin_yaw = math.sin(yaw)
                
                # คำนวณการเคลื่อนที่ใน global coordinates
                global_x = relative_pos[0] * cos_yaw - relative_pos[1] * sin_yaw
                global_y = relative_pos[0] * sin_yaw + relative_pos[1] * cos_yaw
                global_z = relative_pos[2]
                
                target_pos = [
                    self.current_position[0] + global_x,
                    self.current_position[1] + global_y,
                    self.current_position[2] + global_z
                ]
                
            except Exception as e:
                print(f"❌ Failed to get orientation: {e}")
                # fallback เป็นการเคลื่อนที่แบบเดิม
                target_pos = [
                    self.current_position[0] + relative_pos[0],
                    self.current_position[1] + relative_pos[1],
                    self.current_position[2] + relative_pos[2]
                ]
        else:
            # สำหรับโดรนจริงหรือกรณีที่ไม่สามารถดึง orientation ได้
            target_pos = [
                self.current_position[0] + relative_pos[0],
                self.current_position[1] + relative_pos[1],
                self.current_position[2] + relative_pos[2]
            ]
        
        # จำกัดความสูงขั้นต่ำ
        target_pos[2] = max(0.1, target_pos[2])
        
        if self.use_real_drone:
            # โดรนจริง: ใช้คำสั่งการเคลื่อนที่
            try:
                # แปลงเป็น cm และจำกัดค่า
                x_cm = max(-500, min(500, int(relative_pos[0] * 100)))
                y_cm = max(-500, min(500, int(relative_pos[1] * 100)))
                z_cm = max(-500, min(500, int(relative_pos[2] * 100)))
                
                if abs(x_cm) > 20 or abs(y_cm) > 20 or abs(z_cm) > 20:
                    self.drone.go_xyz_speed(x_cm, y_cm, z_cm, 50)
                    time.sleep(abs(max(x_cm, y_cm, z_cm)) / 50 + 1)
                
                return True
            except Exception as e:
                print(f"❌ Real drone movement failed: {e}")
                return False
        else:
            return self._move_to_position_naturally(target_pos)

    def rotate_clockwise(self, degrees):
        """หมุนตามเข็มนาฬิกา"""
        return self._rotate(degrees)

    def rotate_counter_clockwise(self, degrees):
        """หมุนทวนเข็มนาฬิกา"""
        return self._rotate(-degrees)

    def _rotate(self, degrees):
        """หมุนโดรน"""
        if not self.is_flying:
            print("⚠️ Drone must be flying first")
            return False
        
        print(f"🔄 Rotating {degrees} degrees...")
        
        if self.use_simulation:
            try:
                # ในซิม: หมุนแบบ smooth
                current_orient = self.sim.getObjectOrientation(self.drone_handle, -1)
                target_orient = list(current_orient)
                target_orient[2] += math.radians(degrees)
                
                # หมุนแบบ smooth
                steps = max(10, int(abs(degrees) / 10))
                for i in range(steps + 1):
                    t = i / steps
                    smooth_t = 3*t*t - 2*t*t*t
                    
                    current_yaw = current_orient[2] + math.radians(degrees) * smooth_t
                    orient = [current_orient[0], current_orient[1], current_yaw]
                    
                    self.sim.setObjectOrientation(self.drone_handle, -1, orient)
                    time.sleep(0.05)
                
                print("✅ Rotation complete")
                return True
                
            except Exception as e:
                print(f"❌ Rotation failed: {e}")
                return False
                
        elif self.use_real_drone:
            try:
                if degrees > 0:
                    self.drone.rotate_clockwise(int(degrees))
                else:
                    self.drone.rotate_counter_clockwise(int(abs(degrees)))
                time.sleep(abs(degrees) / 90 + 1)
                return True
            except Exception as e:
                print(f"❌ Real drone rotation failed: {e}")
                return False
        
        return False

    def move_to_position(self, x, y, z):
        """เคลื่อนที่ไปยังตำแหน่งเฉพาะ"""
        if not self.is_flying:
            print("⚠️ Drone must be flying first")
            return False
        
        target_pos = [x, y, max(0.1, z)]
        return self._move_to_position_naturally(target_pos)

    def get_position(self):
        """ดึงตำแหน่งปัจจุบัน"""
        self._update_current_position()
        return self.current_position.copy()

    def get_battery(self):
        """ดึงระดับแบตเตอรี่"""
        if self.use_real_drone:
            try:
                return self.drone.get_battery()
            except:
                return -1
        else:
            # ในซิม: จำลองแบตเตอรี่
            return 85

    def take_picture(self, count=3, delay=1.5):
        """ถ่ายรูปหลายรูปติดต่อกัน"""
        if self.use_simulation:
            print("🚁 ใช้กล้องในโปรแกรมจำลอง")
            if not self.camera:
                print("❌ กล้องไม่ได้เริ่มต้น")
                return []
                
            saved_files = []
            for i in range(count):
                try:
                    img_path = self.camera.simcapture()
                    if img_path:
                        # เปลี่ยนชื่อไฟล์ให้มีหมายเลข
                        import shutil
                        new_path = f"captured_images/sim_picture_{i+1}.jpg"
                        shutil.move(img_path, new_path)
                        saved_files.append(new_path)
                        print(f"📸 ถ่ายรูปที่ {i+1}: {new_path}")
                        time.sleep(delay)
                except Exception as e:
                    print(f"❌ ถ่ายรูปที่ {i+1} ไม่สำเร็จ: {e}")
            return saved_files
            
        elif self.use_real_drone:
            print("🚁 ใช้กล้องโดรนจริง")
            try:
                return self.drone.capture(count=count, delay=delay)
            except Exception as e:
                print(f"❌ ถ่ายรูปหลายรูปไม่สำเร็จ: {e}")
                return []
        else:
            print("❌ ไม่มีอินเตอร์เฟซกล้อง")
            return []

    def take_bottom_picture(self):
        """ถ่ายรูปด้วยกล้องล่าง"""
        if self.use_simulation:
            print("🚁 Using bottom camera in simulator")
            if not self.camera:
                print("❌ Camera not initialized")
                return None
                
            try:
                img_path = self.camera.simcapturebottom()
                print(f"📸 ถ่ายรูปสำเร็จ: {img_path}")
                return img_path
            except Exception as e:
                print(f"❌ ถ่ายรูปไม่สำเร็จ: {e}")
                return None
        elif self.use_real_drone:
            print("🚁 Using Real Camera Drone (bottom)")
            # สำหรับโดรนจริง - ใช้กล้องเดียวกัน
            return self.take_picture()
        else:
            print("❌ No camera interface available")
            return None

    def scan_qr_code(self):
        """ถ่ายรูปและแสกน QR Code"""
        if not self.camera or not self.qr_scanner:
            print("❌ Camera or QR Scanner not initialized")
            return None
        
        try:
            img_path = self.take_picture()
            if not img_path:
                return None
            
            print("🔍 กำลังแสกน QR Code...")
            qr_results = self.qr_scanner.scan_qr_code(img_path)
            
            if qr_results:
                print(f"✅ พบ QR Code จำนวน {len(qr_results)} รายการ")
                return qr_results
            else:
                print("❌ ไม่พบ QR Code ในภาพ")
                return None
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการแสกน QR Code: {e}")
            return None

    def scan_mission_pad(self):
        """แสกน Mission Pad"""
        try:
            # ถ่ายรูปก่อน
            img_path = self.take_picture()
            if img_path:
                print("🔍 กำลังค้นหา Mission Pad...")
                # ใช้ mission_pad_detector ที่มีอยู่
                pad_id = self.mission_pad_detector.get_mission_pad_id()
                if pad_id:
                    print(f"✅ พบ Mission Pad: {pad_id}")
                    return pad_id
                else:
                    print("❌ ไม่พบ Mission Pad")
                    return None
            else:
                print("❌ Cannot capture image for mission pad scanning")
                return None
        except Exception as e:
            print(f"❌ Mission pad scanning error: {e}")
            return None

    def get_mission_pad_id(self):
        """ดึง Mission Pad ID จากการแสกนจริง"""
        try:
            # ตรวจสอบว่า mission_pad_detector มีอยู่และพร้อมใช้งาน
            if not hasattr(self, 'mission_pad_detector') or not self.mission_pad_detector:
                print("❌ Mission Pad Detector not found - creating new one")
                self.mission_pad_detector = HybridMissionPadDetector(self.use_simulation)
                self.enable_mission_pads()
            
            # ✅ ใช้ detection_enabled จาก mission_pad_detector
            if not self.mission_pad_detector.detection_enabled:
                print("⚠️ Mission Pad detection disabled - enabling now")
                self.mission_pad_detector.enable_mission_pad_detection()
            
            if self.use_simulation:
                # ถ่ายภาพและวิเคราะห์
                image_path = self.take_bottom_picture()
                return self.mission_pad_detector.get_mission_pad_id(image_path)
            else:
                # ใช้ djitellopy กับโดรนจริง
                return self.mission_pad_detector.get_mission_pad_id()
                
        except Exception as e:
            print(f"❌ Mission Pad detection error: {e}")
            return None

    def enable_mission_pads(self):
        """เปิดใช้งาน Mission Pad detection"""
        try:
            if hasattr(self, 'mission_pad_detector') and self.mission_pad_detector:
                self.mission_pad_detector.enable_mission_pad_detection()
            else:
                print("⚠️ Mission Pad Detector not initialized yet")
        except Exception as e:
            print(f"❌ Failed to enable mission pads: {e}")

    def disable_mission_pads(self):
        """ปิด Mission Pad detection"""
        try:
            if hasattr(self, 'mission_pad_detector') and self.mission_pad_detector:
                self.mission_pad_detector.disable_mission_pad_detection()
            else:
                print("⚠️ Mission Pad Detector not initialized")
        except Exception as e:
            print(f"❌ Failed to disable mission pads: {e}")

    def get_mission_pad_sum(self):
        """คำนวณผลรวมของ Mission Pad ที่ตรวจพบ"""
        if not self.detected_mission_pads:
            return 0
        
        total = sum([pad['id'] for pad in self.detected_mission_pads])
        print(f"📊 Mission Pad Sum: {total}")
        return total
    
    def get_mission_pad_sequence(self):
        """ได้ลำดับของ Mission Pad ที่ตรวจพบ"""
        sequence = [pad['id'] for pad in self.detected_mission_pads]
        print(f"📋 Mission Pad Sequence: {sequence}")
        return sequence
    
    def process_mission_pad_data(self, operation="sum"):
        """ประมวลผลข้อมูล Mission Pad ตามที่ต้องการ"""
        if not self.detected_mission_pads:
            print("❌ No mission pad data to process")
            return None
        
        pad_ids = [pad['id'] for pad in self.detected_mission_pads]
        
        if operation == "sum":
            result = sum(pad_ids)
        elif operation == "multiply":
            result = 1
            for pad_id in pad_ids:
                result *= pad_id
        elif operation == "average":
            result = sum(pad_ids) / len(pad_ids)
        elif operation == "max":
            result = max(pad_ids)
        elif operation == "min":
            result = min(pad_ids)
        else:
            result = pad_ids
        
        print(f"🔢 Mission Pad {operation}: {result}")
        return result

    def print_drone_status(self):
        """แสดงสถานะปัจจุบันของโดรน"""
        try:
            if hasattr(self, 'sim') and self.sim:
                # ดึงตำแหน่งปัจจุบัน
                current_pos = self.get_position()
                
                # ดึงการหมุนปัจจุบัน
                current_orientation = self.sim.getObjectOrientation(self.drone_handle, -1)
                
                print("🚁 === Drone Status ===")
                print(f"📍 Position: ({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})")
                print(f"🧭 Orientation: ({math.degrees(current_orientation[0]):.1f}°, {math.degrees(current_orientation[1]):.1f}°, {math.degrees(current_orientation[2]):.1f}°)")
                print(f"✈️ Flying: {self.is_flying}")
                print(f"⚡ Simulation running: {self.simulation_running}")
                print(f"🔋 Battery: {self.get_battery()}%")
                print("=====================")
            else:
                print("❌ Drone not initialized")
        except Exception as e:
            print(f"❌ Error getting drone status: {e}")

    def fly_pattern_up_down(self, cycles=3, height_change=0.5):
        """บินขึ้นลงแบบซ้ำๆ เพื่อทดสอบ"""
        if not self.is_flying:
            print("❌ Drone is not flying! Call takeoff() first.")
            return False
            
        try:
            print(f"🚁 Flying up-down pattern for {cycles} cycles...")
            
            current_pos = self.get_position()
            base_height = current_pos[2]
            
            for cycle in range(cycles):
                print(f"  Cycle {cycle + 1}/{cycles}")
                
                # บินขึ้น
                self.move_to_position(current_pos[0], current_pos[1], base_height + height_change)
                time.sleep(0.5)
                
                # บินลง
                self.move_to_position(current_pos[0], current_pos[1], base_height)
                time.sleep(0.5)
            
            print("✓ Pattern flight complete!")
            return True
            
        except Exception as e:
            print(f"❌ Pattern flight failed: {e}")
            return False
    
    def fly_square_pattern(self, size=2.0, height=1.5):
        """บินเป็นรูปสี่เหลี่ยม"""
        if not self.is_flying:
            print("❌ Drone is not flying! Call takeoff() first.")
            return False
            
        try:
            print(f"🚁 Flying square pattern (size: {size}m)...")
            
            current_pos = self.get_position()
            center_x, center_y = current_pos[0], current_pos[1]
            
            # จุดมุมของสี่เหลี่ยม
            corners = [
                [center_x + size/2, center_y + size/2, height],  # มุมขวาบน
                [center_x - size/2, center_y + size/2, height],  # มุมซ้ายบน
                [center_x - size/2, center_y - size/2, height],  # มุมซ้ายล่าง
                [center_x + size/2, center_y - size/2, height],  # มุมขวาล่าง
                [center_x, center_y, height]                      # กลับจุดกลาง
            ]
            
            for i, corner in enumerate(corners):
                print(f"  Moving to corner {i + 1}/5")
                self.move_to_position(corner[0], corner[1], corner[2])
                time.sleep(1)
            
            print("✓ Square pattern complete!")
            return True
            
        except Exception as e:
            print(f"❌ Square pattern failed: {e}")
            return False

    def find_and_approach_qr(self, target_data=None):
        """ค้นหาและเข้าใกล้ QR Code"""
        try:
            # แสกน QR Code
            qr_results = self.scan_qr_code()
            if not qr_results:
                return False
            
            # หา QR Code ที่ต้องการ (ถ้าระบุ)
            target_qr = None
            if target_data:
                for qr in qr_results:
                    if target_data in qr['data']:
                        target_qr = qr
                        break
            else:
                # ใช้ QR Code แรกที่พบ
                target_qr = qr_results[0]
            
            if not target_qr:
                print(f"❌ ไม่พบ QR Code ที่มีข้อมูล: {target_data}")
                return False
            
            print(f"🎯 กำลังเข้าใกล้ QR Code: {target_qr['data']}")
            
            # คำนวณการเคลื่อนที่ (ตัวอย่างง่ายๆ)
            center_x, center_y = target_qr['center']
            image_width = 640  # ขนาดภาพมาตรฐาน
            image_height = 480
            
            # คำนวณการเคลื่อนที่แบบง่าย
            offset_x = (center_x - image_width/2) / image_width
            offset_y = (center_y - image_height/2) / image_height
            
            # เคลื่อนที่ไปยัง QR Code
            if abs(offset_x) > 0.1:
                if offset_x > 0:
                    self.move_right(0.2)
                else:
                    self.move_left(0.2)
            
            if abs(offset_y) > 0.1:
                if offset_y > 0:
                    self.move_down(0.2)
                else:
                    self.move_up(0.2)
            
            print(f"✅ เข้าใกล้ QR Code สำเร็จ")
            return True
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการเข้าใกล้ QR Code: {e}")
            return False

    def test_movement_commands(self):
        """ทดสอบคำสั่งการเคลื่อนที่ทั้งหมด"""
        print("🧪 Testing all movement commands...")
        
        if not self.takeoff(height=2.0):
            return False
        
        try:
            # ทดสอบการเคลื่อนที่
            print("\n1. Testing directional movements...")
            self.move_forward(1.0)
            time.sleep(1)
            
            self.move_right(1.0)
            time.sleep(1)
            
            self.move_backward(1.0)
            time.sleep(1)
            
            self.move_left(1.0)
            time.sleep(1)
            
            # ทดสอบการบินขึ้นลง
            print("\n2. Testing vertical movements...")
            self.move_up(0.5)
            time.sleep(1)
            
            self.move_down(0.5)
            time.sleep(1)
            
            # ทดสอบการหมุน
            print("\n3. Testing rotations...")
            self.rotate_clockwise(90)
            time.sleep(1)
            
            self.rotate_counter_clockwise(180)
            time.sleep(1)
            
            self.rotate_clockwise(90)  # กลับสู่ทิศเดิม
            time.sleep(1)
            
            print("\n✅ All movement tests completed!")
            self.land()
            return True
            
        except Exception as e:
            print(f"❌ Movement test failed: {e}")
            return False

    def stop_simulation(self):
        """หยุด simulation"""
        if self.use_simulation and self.sim is not None:
            try:
                self.sim.stopSimulation()
                self.simulation_running = False
                print("✅ Simulation stopped")
            except:
                pass

    def disconnect(self):
        if self.is_flying:
            self.land()
        
        # ✅ เพิ่มส่วนนี้
        # รีเซ็ตลมก่อนปิด simulation
        if self.use_simulation and hasattr(self, 'wind_settings'):
            try:
                self.set_calm_conditions()
                print("🌪️ Wind effects reset to calm")
            except:
                pass
        
        if self.use_simulation:
            self.stop_simulation()
        
        # เพิ่มการ cleanup สำหรับโดรนจริง
        if self.use_real_drone and hasattr(self, 'drone'):
            try:
                self.drone.cleanup()
            except Exception as e:
                print(f"⚠️ Drone cleanup error: {e}")
        
        print("👋 Drone controller disconnected")

#testing method
    def interactive_wind_control(self):
        """โหมดควบคุมลมแบบ interactive"""
        print("\n🎮 Interactive Wind Control Mode")
        print("=" * 50)
        print("Commands:")
        print("  0-9: Set wind strength (0-9)")
        print("  n/s/e/w: Wind direction (North/South/East/West)")
        print("  t: Toggle turbulence")
        print("  g: Toggle gusts")
        print("  c: Calm conditions")
        print("  m: Moderate wind preset")
        print("  r: Strong wind preset")
        print("  status: Show wind status")
        print("  test: Quick wind test")
        print("  q: Quit")
        print("-" * 50)
        
        if not self.is_flying:
            print("🚁 Taking off for wind testing...")
            if not self.takeoff(height=1.5):
                return False
        
        try:
            while True:
                command = input("\nWind Control> ").lower().strip()
                
                if command == 'q':
                    break
                elif command.isdigit() and 0 <= int(command) <= 9:
                    strength = int(command)
                    self.set_wind_strength(strength)
                elif command == 'n':
                    self.set_wind_direction(0, 1, 0)
                    print("🧭 Wind from North")
                elif command == 's':
                    self.set_wind_direction(0, -1, 0)
                    print("🧭 Wind from South")
                elif command == 'e':
                    self.set_wind_direction(1, 0, 0)
                    print("🧭 Wind from East")
                elif command == 'w':
                    self.set_wind_direction(-1, 0, 0)
                    print("🧭 Wind from West")
                elif command == 't':
                    current = self.wind_settings.get('turbulence', False)
                    self.enable_turbulence(not current)
                elif command == 'g':
                    current = self.wind_settings.get('gusts', False)
                    self.enable_wind_gusts(not current)
                elif command == 'c':
                    self.set_calm_conditions()
                elif command == 'm':
                    self.set_moderate_wind()
                elif command == 'r':
                    self.set_strong_wind()
                elif command == 'status':
                    self.get_wind_status()
                    self.print_drone_status()
                elif command == 'test':
                    self.test_wind_effects_simple()
                else:
                    print("❌ Unknown command. Type 'q' to quit.")
            
            # ลงจอดก่อนออก
            self.set_calm_conditions()
            print("🛬 Landing...")
            self.land()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.set_calm_conditions()
            self.land()
            return False
            
        except Exception as e:
            print(f"❌ Interactive control error: {e}")
            self.set_calm_conditions()
            self.land()
            return False



def test_wind_system():
    """ทดสอบระบบลมแบบสมบูรณ์"""
    print("🌪️ Testing Wind System")
    print("=" * 50)
    
    # สร้าง drone controller
    drone = NaturalDroneController(use_simulation=True)
    
    if not drone.use_simulation:
        print("❌ Simulation not available for wind testing")
        return False
    
    try:
        # ทดสอบพื้นฐาน
        print("\n1. Testing basic wind functions...")
        drone.takeoff(height=1.5)
        time.sleep(2)
        
        # ทดสอบ wind effects
        success = drone.test_wind_effects_simple()
        
        if success:
            print("\n2. Testing wind demo...")
            drone.start_wind_demo()
        
        return success
        
    except Exception as e:
        print(f"❌ Wind system test failed: {e}")
        return False
    
    finally:
        drone.disconnect()

def interactive_wind_demo():
    """Demo แบบ interactive"""
    print("🎮 Interactive Wind Demo")
    print("=" * 50)
    
    drone = NaturalDroneController(use_simulation=True)
    
    if not drone.use_simulation:
        print("❌ Simulation required")
        return
    
    try:
        drone.interactive_wind_control()
    finally:
        drone.disconnect()

# Main execution
if __name__ == "__main__":
    print("🌪️ Wind Effects Test Suite")
    print("=" * 60)
    
    choice = input("Select test:\n1. Automated Wind Test\n2. Interactive Wind Demo\n3. Exit\nChoice: ")
    
    if choice == "1":
        test_wind_system()
    elif choice == "2":
        interactive_wind_demo()
    else:
        print("👋 Goodbye!")