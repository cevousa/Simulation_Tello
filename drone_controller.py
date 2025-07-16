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
from collections import Counter

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
            print("📸 Starting camera display as requested...")
            self._start_video_stream()
            self.start_camera_display()
        else:
            print("📸 Camera display disabled - no automatic photo taking")
        
        time.sleep(2)  # Give some time for connection to stabilize

        # enable mission pads if requested
        if enable_mission_pad:
            print("Enabling mission pads...")
            self.enable_mission_pads()
        else:
            print("Mission pads disabled")
        
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
        """เริ่ม video stream พร้อมการรอให้กล้องปรับตัว - ไม่ถ่ายรูปทดสอบ"""
        try:
            print("Starting video stream...")
            self.streamon()
            
            # รอให้ stream เริ่มต้น
            time.sleep(3)  # ลดเวลารอจาก 5 เป็น 3 วินาที
            
            # ตั้งค่า stream ให้พร้อมใช้งานโดยไม่ทดสอบเฟรม
            self._stream_active = True
            print("✅ Video stream initialized (without frame testing)")
            
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
        self.mission_pad_detector = None
        self.bottom_camera_handle = None
        self.image_folder = './captured_images'
        self.simulation_running = False
        self.detected_mission_pads = []
        # Wind system variables
        self.wind_settings = {
            'strength': 0,
            'direction': [0, 0, 0],
            'turbulence': True,
            'gusts': True,
            'zones': []
        }
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        
        # เริ่มต้นการเชื่อมต่อ
        print("🔧 Initializing connection...")
        self._initialize_connection()
        
        # ✅ ไม่เปิดใช้งาน mission pads อัตโนมัติ - ให้ผู้ใช้เรียกใช้เอง
        print("🔧 Mission pads disabled by default - call enable_mission_pads() manually if needed")
        
        print(f"🚁 Drone Controller initialized - Mode: {'Simulation' if self.use_simulation else 'Real Drone'}")

    def _initialize_connection(self):
        """เริ่มต้นการเชื่อมต่อ - ไม่เริ่มกล้องอัตโนมัติ"""
        if self.use_simulation:
            success = self._init_simulation()
            if success:
                print("✅ Simulation connected - camera system ready but not started")
                # ไม่เรียก _init_camera_system() อัตโนมัติ
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
    # ---------------- WIND SYSTEM ----------------
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
                test_result = self.sim.callScriptFunction('setWindStrength', self.drone_handle, 0)
                print("✅ Wind Lua functions accessible")
            except Exception as lua_error:
                print(f"⚠️ Wind Lua functions not available: {lua_error}")
                print("💡 Make sure you've added the wind code to the drone's Lua script")
            print("✅ Wind system ready")
            return True
        except Exception as e:
            print(f"❌ Wind system setup failed: {e}")
            return False

    def set_wind_strength(self, strength):
        """ตั้งค่าความแรงลม (0-10)"""
        try:
            if not (0 <= strength <= 10):
                print("❌ Wind strength must be between 0-10")
                return False
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
            result = self.sim.callScriptFunction('setWindDirection', self.drone_handle, [x, y, z])
            self.wind_settings['direction'] = [x, y, z]
            print(f"🧭 Wind direction set to: ({x:.1f}, {y:.1f}, {z:.1f}) m/s")
            return True
        except Exception as e:
            return False

    def enable_turbulence(self, enable=True):
        """เปิด/ปิด turbulence"""
        try:
            result = self.sim.callScriptFunction('enableTurbulence', self.drone_handle, enable)
            self.wind_settings['turbulence'] = enable
            print(f"🌊 Turbulence {'enabled' if enable else 'disabled'}")
            return True
        except Exception as e:
            return False

    def enable_wind_gusts(self, enable=True):
        """เปิด/ปิด wind gusts"""
        try:
            result = self.sim.callScriptFunction('enableWindGusts', self.drone_handle, enable)
            self.wind_settings['gusts'] = enable
            print(f"💨 Wind gusts {'enabled' if enable else 'disabled'}")
            return True
        except Exception as e:
            return False

    def create_wind_zone(self, name, x_min, y_min, x_max, y_max, wind_multiplier=1.0, turbulence_level=0.1):
        """สร้าง wind zone แบบกำหนดเอง"""
        try:
            result = self.sim.callScriptFunction('createCustomWindZone', self.drone_handle, [name, x_min, y_min, x_max, y_max, wind_multiplier, turbulence_level])
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

    # Wind presets
    def set_calm_conditions(self):
        self.set_wind_strength(0)
        self.enable_turbulence(False)
        self.enable_wind_gusts(False)
        print("😌 Calm weather conditions set")

    def set_light_breeze(self):
        self.set_wind_strength(2)
        self.set_wind_direction(1, 0.5, 0)
        self.enable_turbulence(True)
        self.enable_wind_gusts(False)
        print("🍃 Light breeze conditions set")

    def set_moderate_wind(self):
        self.set_wind_strength(4)
        self.set_wind_direction(2, 1, 0)
        self.enable_turbulence(True)
        self.enable_wind_gusts(True)
        print("💨 Moderate wind conditions set")

    def set_strong_wind(self):
        self.set_wind_strength(7)
        self.set_wind_direction(3, 2, 0.5)
        self.enable_turbulence(True)
        self.enable_wind_gusts(True)
        print("⚠️ Strong wind conditions set - Be careful!")

    def create_realistic_wind_scenario(self):
        """สร้างสถานการณ์ลมที่สมจริงสำหรับการทดสอบ"""
        try:
            print("🏟️ Creating realistic wind scenario...")
            self.create_wind_zone("Launch_Area", -0.5, -0.5, 0.5, 0.5, 0.5, 0.02)
            self.create_wind_zone("Obstacle_Area", 1, 1, 3, 3, 1.2, 0.15)
            self.create_wind_zone("Mission_Area", 2, 4, 3, 5, 1.8, 0.25)
            self.set_wind_strength(3)
            self.set_wind_direction(1, 0.5, 0)
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
            start_pos = self.get_position()
            print("\n1. 😌 Testing calm conditions...")
            self.set_calm_conditions()
            self.hover(3)
            pos_calm = self.get_position()
            drift_calm = self._calculate_drift(start_pos, pos_calm)
            print("\n2. 🍃 Testing light breeze...")
            self.move_to_position(*start_pos)
            time.sleep(1)
            self.set_light_breeze()
            self.hover(3)
            pos_breeze = self.get_position()
            drift_breeze = self._calculate_drift(start_pos, pos_breeze)
            print("\n3. 💨 Testing moderate wind...")
            self.move_to_position(*start_pos)
            time.sleep(1)
            self.set_moderate_wind()
            self.hover(3)
            pos_wind = self.get_position()
            drift_wind = self._calculate_drift(start_pos, pos_wind)
            self.set_calm_conditions()
            self.move_to_position(*start_pos)
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
            print("\n📈 Demo 1: Wind Strength Progression")
            strengths = [0, 2, 4, 6, 8]
            for strength in strengths:
                print(f"  Setting wind strength to {strength}...")
                self.set_wind_strength(strength)
                self.set_wind_direction(1, 0, 0)
                self.hover(2)
                pos = self.get_position()
                print(f"    Position after wind {strength}: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            print("\n🧭 Demo 2: Wind Direction Changes")
            self.set_wind_strength(4)
            directions = [([1, 0, 0], "East"), ([0, 1, 0], "North"), ([-1, 0, 0], "West"), ([0, -1, 0], "South")]
            center_pos = self.get_position()
            for direction, name in directions:
                print(f"  Wind from {name}...")
                self.move_to_position(*center_pos)
                time.sleep(1)
                self.set_wind_direction(*direction)
                self.hover(3)
                pos = self.get_position()
                print(f"    Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            print("\n📍 Demo 3: Wind Zones")
            self.create_realistic_wind_scenario()
            zones_to_visit = [([0, 0, 1.5], "Launch Area (Calm)"), ([2, 2, 1.5], "Obstacle Area (Moderate)"), ([2.5, 4.5, 1.5], "Mission Area (Strong)")]
            for pos, zone_name in zones_to_visit:
                print(f"  Flying to {zone_name}...")
                self.move_to_position(*pos)
                self.hover(2)
                final_pos = self.get_position()
                print(f"    Final position: ({final_pos[0]:.2f}, {final_pos[1]:.2f}, {final_pos[2]:.2f})")
            self.set_calm_conditions()
            self.land()
            print("✅ Wind demonstration complete!")
            return True
        except Exception as e:
            print(f"❌ Wind demonstration failed: {e}")
            self.set_calm_conditions()
            self.land()
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
            self.drone = DroneTello(show_cam=False, enable_mission_pad=False)  # ปิดทั้ง show_cam และ mission_pad
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
                
                # ใช้ ImprovedMissionPadDetector ถ้ามี
                if IMPROVED_MISSION_PAD_AVAILABLE:
                    self.mission_pad_detector = ImprovedMissionPadDetector()
                    print("✅ Using ImprovedMissionPadDetector")
                elif MISSION_PAD_AVAILABLE:
                    self.mission_pad_detector = MissionPadDetector()
                    print("✅ Using standard MissionPadDetector")
                else:
                    self.mission_pad_detector = MissionPadDetector()  # Fallback
                    print("⚠️ Using fallback MissionPadDetector")
                
                print("✅ Camera system initialized")
            except Exception as e:
                print(f"⚠️ Camera system initialization failed: {e}")
                
        elif self.use_real_drone:
            try:
                self.qr_scanner = QRCodeScanner()
                
                # ใช้ ImprovedMissionPadDetector ถ้ามี
                if IMPROVED_MISSION_PAD_AVAILABLE:
                    self.mission_pad_detector = ImprovedMissionPadDetector()
                    print("✅ Using ImprovedMissionPadDetector")
                elif MISSION_PAD_AVAILABLE:
                    self.mission_pad_detector = MissionPadDetector()
                    print("✅ Using standard MissionPadDetector")
                else:
                    self.mission_pad_detector = MissionPadDetector()  # Fallback
                    print("⚠️ Using fallback MissionPadDetector")
                
                print("✅ QR Scanner and Mission Pad Detector initialized")
            except Exception as e:
                print(f"⚠️ Scanner system initialization failed: {e}")

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
        """ถ่ายรูป"""
        if self.use_simulation:
            print("🚁 Using camera in simulator")
            if not self.camera:
                print("❌ Camera not initialized")
                return None
            try:
                img_path = self.camera.simcapture()
                print(f"📸 ถ่ายรูปสำเร็จ: {img_path}")
                return img_path
            except Exception as e:
                print(f"❌ ถ่ายรูปไม่สำเร็จ: {e}")
                return None
        
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
        """ถ่ายรูปด้วยกล้องล่าง - เริ่มกล้องเฉพาะเมื่อจำเป็น"""
        if self.use_simulation:
            print("🚁 Using bottom camera in simulator")
            
            # เริ่มกล้องเฉพาะเมื่อจำเป็น
            if not self.camera:
                print("📸 Initializing camera system...")
                self._init_camera_system()
            
            if not self.camera:
                print("❌ Camera not initialized")
                return None
                
            try:
                print("📸 Taking bottom picture...")
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

    def scan_qr_code(self, image_path=None):
        """แสกน QR Code จากไฟล์ภาพ - ต้องส่ง image_path หรือถ่ายรูปก่อน"""
        # เริ่มกล้องเฉพาะเมื่อจำเป็น
        if not self.camera and self.use_simulation:
            print("📸 Initializing camera system for QR scanning...")
            self._init_camera_system()
        
        if not self.camera or not self.qr_scanner:
            print("❌ Camera or QR Scanner not initialized")
            return None
        
        try:
            # ถ้าไม่มี image_path ให้ถ่ายรูปใหม่
            if not image_path:
                print("📸 No image provided, taking new picture...")
                img_paths = self.take_picture(count=1)
                if not img_paths:
                    print("❌ Failed to take picture for QR scanning")
                    return None
                image_path = img_paths[0]
            
            print(f"🔍 กำลังแสกน QR Code จาก: {image_path}")
            qr_results = self.qr_scanner.scan_qr_code(image_path)
            
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
        """ดึง Mission Pad ID จากการแสกนจริง - ต้องเรียกใช้ด้วยตนเอง"""
        try:
            # ตรวจสอบว่า mission_pad_detector มีอยู่และพร้อมใช้งาน
            if not hasattr(self, 'mission_pad_detector') or not self.mission_pad_detector:
                print("❌ Mission Pad Detector not found - call enable_mission_pads() first")
                return None
            
            # ✅ ตรวจสอบว่า detection เปิดอยู่หรือไม่
            if not self.mission_pad_detector.detection_enabled:
                print("⚠️ Mission Pad detection disabled - call enable_mission_pads() first")
                return None
            
            if self.use_simulation:
                # ถ่ายภาพและวิเคราะห์ - แค่เมื่อเรียกใช้ฟังก์ชันนี้เท่านั้น
                print("📸 Taking picture for mission pad detection...")
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
            # เริ่มต้นระบบกล้องถ้ายังไม่ได้เริ่ม
            if not self.mission_pad_detector:
                print("📸 Initializing Mission Pad Detector...")
                self._init_camera_system()
            
            if self.mission_pad_detector:
                self.mission_pad_detector.enable_mission_pad_detection()
                print("✅ Mission Pad detection enabled")
            else:
                print("❌ Mission Pad Detector not initialized")
                
        except Exception as e:
            print(f"❌ Failed to enable mission pads: {e}")

    def disable_mission_pads(self):
        """ปิด Mission Pad detection"""
        try:
            if self.mission_pad_detector:
                self.mission_pad_detector.disable_mission_pad_detection()
                print("✅ Mission Pad detection disabled")
            else:
                print("⚠️ Mission Pad Detector not initialized")
        except Exception as e:
            print(f"❌ Failed to disable mission pads: {e}")
            
    def set_mission_pad_confidence(self, threshold):
        """กำหนดค่าเกณฑ์ความเชื่อมั่นสำหรับ Mission Pad detection"""
        try:
            if self.mission_pad_detector:
                self.mission_pad_detector.set_confidence_threshold(threshold)
            else:
                print("⚠️ Mission Pad Detector not initialized")
        except Exception as e:
            print(f"❌ Failed to set confidence threshold: {e}")
            
    def get_mission_pad_templates_info(self):
        """ดึงข้อมูลของ Mission Pad templates"""
        try:
            if self.mission_pad_detector:
                return self.mission_pad_detector.get_template_info()
            else:
                print("⚠️ Mission Pad Detector not initialized")
                return {}
        except Exception as e:
            print(f"❌ Failed to get template info: {e}")
            return {}
            
    def test_mission_pad_detection(self, test_image_path):
        """ทดสอบการตรวจจับ Mission Pad ด้วยรูปภาพทดสอบ"""
        try:
            if not self.mission_pad_detector:
                print("📸 Initializing Mission Pad Detector...")
                self._init_camera_system()
            
            if self.mission_pad_detector:
                return self.mission_pad_detector.test_detection(test_image_path)
            else:
                print("❌ Mission Pad Detector not initialized")
                return None
        except Exception as e:
            print(f"❌ Test detection failed: {e}")
            return None

    def smart_mission_pad_scan(self, image_path=None, use_multiple_methods=True):
        """
        ตรวจจับ Mission Pad ด้วยวิธีการที่ปรับปรุงแล้ว
        
        Args:
            image_path (str): path ของรูปภาพ (ถ้าไม่ระบุจะถ่ายรูปใหม่)
            use_multiple_methods (bool): ใช้วิธีการหลากหลายหรือไม่
            
        Returns:
            int: Mission Pad ID ที่ตรวจพบ
        """
        try:
            # เริ่มต้นระบบถ้ายังไม่ได้เริ่ม
            if not self.mission_pad_detector:
                print("📸 Initializing Mission Pad Detector...")
                self._init_camera_system()
            
            if not self.mission_pad_detector:
                print("❌ Mission Pad Detector not available")
                return None
            
            # เปิดการตรวจจับ
            if not self.mission_pad_detector.detection_enabled:
                self.mission_pad_detector.enable_mission_pad_detection()
            
            # ถ่ายรูปถ้าไม่มี image_path
            if not image_path:
                print("📸 Taking new picture for mission pad detection...")
                image_path = self.take_bottom_picture()
                if not image_path:
                    print("❌ Failed to take picture")
                    return None
            
            # ตรวจสอบว่าไฟล์มีอยู่จริง
            if not os.path.exists(image_path):
                print(f"❌ Image file not found: {image_path}")
                return None
            
            print(f"🔍 Analyzing image: {image_path}")
            
            # ใช้วิธีการตรวจจับ
            if hasattr(self.mission_pad_detector, 'debug_image_analysis'):
                # ถ้าเป็น ImprovedMissionPadDetector
                result = self.mission_pad_detector.get_mission_pad_id(image_path)
                if result is None and use_multiple_methods:
                    print("🔧 Running detailed analysis...")
                    self.mission_pad_detector.debug_image_analysis(image_path)
            else:
                # ถ้าเป็น MissionPadDetector ปกติ
                result = self.mission_pad_detector.get_mission_pad_id(image_path)
            
            return result
            
        except Exception as e:
            print(f"❌ Smart mission pad scan error: {e}")
            return None

    def test_mission_pad_detection_simple(self):
        """ทดสอบการตรวจจับ Mission Pad แบบง่ายๆ"""
        try:
            print("🧪 Testing Mission Pad Detection (Simple Method)")
            
            # ถ่ายรูปทดสอบ
            print("📸 Taking test picture...")
            image_path = self.take_bottom_picture()
            
            if not image_path:
                print("❌ Failed to take test picture")
                return None
            
            # ลองตรวจจับ
            result = self.smart_mission_pad_scan(image_path)
            
            if result:
                print(f"✅ Test successful! Detected Mission Pad: {result}")
                return result
            else:
                print("❌ No Mission Pad detected in test")
                
                # ลองวิธีอื่น
                print("🔄 Trying alternative detection methods...")
                
                # ลองปรับค่า threshold
                original_threshold = self.mission_pad_detector.confidence_threshold
                self.mission_pad_detector.set_confidence_threshold(0.1)  # ลดเกณฑ์
                
                result2 = self.smart_mission_pad_scan(image_path)
                
                # คืนค่าเดิม
                self.mission_pad_detector.set_confidence_threshold(original_threshold)
                
                if result2:
                    print(f"✅ Alternative method successful! Detected Mission Pad: {result2}")
                    return result2
                else:
                    print("❌ All detection methods failed")
                    return None
                    
        except Exception as e:
            print(f"❌ Test error: {e}")
            return None

    def scan_mission_pad_enhanced(self, attempts=3, delay=1.0):
        """
        ตรวจจับ Mission Pad แบบ Enhanced - ลองหลายครั้ง
        
        Args:
            attempts (int): จำนวนครั้งที่จะลอง
            delay (float): ระยะเวลารอระหว่างการลอง
            
        Returns:
            int: Mission Pad ID ที่ตรวจพบ
        """
        try:
            print(f"🔍 Enhanced Mission Pad scanning ({attempts} attempts)...")
            
            results = []
            
            for attempt in range(attempts):
                print(f"  Attempt {attempt + 1}/{attempts}")
                
                # ถ่ายรูปใหม่ในแต่ละครั้ง
                image_path = self.take_bottom_picture()
                
                if image_path:
                    result = self.smart_mission_pad_scan(image_path)
                    if result:
                        results.append(result)
                        print(f"    ✅ Found: {result}")
                    else:
                        print(f"    ❌ No result")
                
                if attempt < attempts - 1:
                    time.sleep(delay)
            
            if results:
                # หา result ที่พบบ่อยที่สุด
                from collections import Counter
                most_common = Counter(results).most_common(1)[0]
                final_result = most_common[0]
                confidence = most_common[1] / len(results)
                
                print(f"🎯 Final result: Mission Pad {final_result} (found {most_common[1]}/{len(results)} times)")
                return final_result
            else:
                print("❌ No Mission Pad detected in any attempt")
                return None
                
        except Exception as e:
            print(f"❌ Enhanced scan error: {e}")
            return None

    def debug_mission_pad_system(self):
        """ตรวจสอบระบบ Mission Pad ทั้งหมด"""
        try:
            print("🔧 === Mission Pad System Debug ===")
            
            # ตรวจสอบการเริ่มต้น
            if not self.mission_pad_detector:
                print("❌ Mission Pad Detector not initialized")
                print("🔄 Trying to initialize...")
                self._init_camera_system()
            
            if not self.mission_pad_detector:
                print("❌ Still no Mission Pad Detector")
                return False
            
            # ตรวจสอบ templates
            if hasattr(self.mission_pad_detector, 'get_template_info'):
                template_info = self.mission_pad_detector.get_template_info()
                print(f"📋 Templates loaded: {len(template_info)}")
                for pad_id, info in template_info.items():
                    print(f"  - Template {pad_id}: {info['name']} ({info['size']})")
            
            # ตรวจสอบสถานะการเปิดใช้งาน
            if hasattr(self.mission_pad_detector, 'detection_enabled'):
                print(f"🔘 Detection enabled: {self.mission_pad_detector.detection_enabled}")
                if not self.mission_pad_detector.detection_enabled:
                    print("🔄 Enabling detection...")
                    self.mission_pad_detector.enable_mission_pad_detection()
            
            # ตรวจสอบ confidence threshold
            if hasattr(self.mission_pad_detector, 'confidence_threshold'):
                print(f"🎯 Confidence threshold: {self.mission_pad_detector.confidence_threshold}")
            
            # ทดสอบการถ่ายรูป
            print("📸 Testing camera...")
            test_image = self.take_bottom_picture()
            
            if test_image:
                print(f"✅ Camera working: {test_image}")
                
                # ทดสอบการตรวจจับ
                if hasattr(self.mission_pad_detector, 'debug_image_analysis'):
                    print("🔍 Running detailed analysis...")
                    self.mission_pad_detector.debug_image_analysis(test_image)
                
                return True
            else:
                print("❌ Camera not working")
                return False
                
        except Exception as e:
            print(f"❌ Debug error: {e}")
            return False

    # ...existing code...

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
# Import MissionPadDetector from separate file
try:
    from mission_pad_detector import MissionPadDetector
    MISSION_PAD_AVAILABLE = True
except ImportError:
    MISSION_PAD_AVAILABLE = False
    print("⚠️ MissionPadDetector not available")

# Import improved mission pad detector
try:
    from improved_mission_pad_detector import ImprovedMissionPadDetector
    IMPROVED_MISSION_PAD_AVAILABLE = True
    print("✅ ImprovedMissionPadDetector available")
except ImportError:
    IMPROVED_MISSION_PAD_AVAILABLE = False
    print("⚠️ ImprovedMissionPadDetector not available")
    
    # Fallback class
    class ImprovedMissionPadDetector:
        def __init__(self, template_folder='mission_pad_templates'):
            self.template_folder = template_folder
            self.templates = {}
            self.detection_enabled = False
            self.confidence_threshold = 0.3
            print("⚠️ Using fallback ImprovedMissionPadDetector")
        
        def enable_mission_pad_detection(self):
            self.detection_enabled = True
            print("✅ Mission Pad detection enabled (fallback)")
        
        def get_mission_pad_id(self, image_path):
            print("❌ Mission pad detection not available (fallback)")
            return None

# Fallback MissionPadDetector class
if not MISSION_PAD_AVAILABLE:
    class MissionPadDetector:
        def __init__(self, template_folder='D:/pythonforcoppelia/mission_pad_templates'):
            self.template_folder = template_folder
            self.templates = {}
            self.detection_enabled = False
            self.confidence_threshold = 0.3
            print("⚠️ Using fallback MissionPadDetector")
        
        def enable_mission_pad_detection(self):
            self.detection_enabled = True
            print("✅ Mission Pad detection enabled (fallback)")
        
        def get_mission_pad_id(self, image_path):
            print("❌ Mission pad detection not available (fallback)")
            return None
