#!/usr/bin/env python3
"""
Drone GUI Connector - เชื่อมต่อระหว่าง GUI และ Drone Controller
ไฟล์นี้จะทำหน้าที่เป็นตัวกลางระหว่าง field_creator_gui_advanced.py และ drone_controller.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import sys
import os
from datetime import datetime

# เพิ่ม path สำหรับ import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from drone_controller import NaturalDroneController, DroneTello, QRCodeScanner, DroneCamera
except ImportError as e:
    print(f"❌ Error importing drone controller: {e}")
    sys.exit(1)

try:
    from improved_mission_pad_detector import ImprovedMissionPadDetector
    IMPROVED_MISSION_PAD_AVAILABLE = True
except ImportError:
    print("⚠️ ImprovedMissionPadDetector not available")
    IMPROVED_MISSION_PAD_AVAILABLE = False

try:
    from mission_pad_detector import MissionPadDetector
    MISSION_PAD_AVAILABLE = True
except ImportError:
    print("⚠️ MissionPadDetector not available")
    MISSION_PAD_AVAILABLE = False

class DroneGUIConnector:
    """คลาสสำหรับเชื่อมต่อโดรนกับ GUI"""
    
    def __init__(self):
        # ตัวแปรสำหรับโดรน
        self.sim_drone = None          # Simulation drone controller
        self.real_drone = None         # Real drone controller
        self.current_drone = None      # ตัวที่ใช้งานอยู่
        self.drone_mode = "simulation" # "simulation" หรือ "real"
        
        # ตัวแปรสถานะ
        self.is_connected = False
        self.is_flying = False
        self.auto_mission_running = False
        self.current_position = [0.0, 0.0, 0.0]
        
        # ตัวแปรสำหรับกล้องและ QR
        self.camera_active = False
        self.qr_scanner = None
        self.last_captured_images = []
        self.last_qr_results = []
        
        # ตัวแปรสำหรับ mission pads
        self.detected_mission_pads = []
        self.mission_pad_enabled = False
        self.improved_mission_pad_detector = None
        self.basic_mission_pad_detector = None
        
        # Log callback function (initialize before using log_message)
        self.log_callback = None
        
        # เริ่มต้น Mission Pad Detectors
        self._initialize_mission_pad_detectors()
        
        # เริ่มต้น QR Scanner
        self.qr_scanner = QRCodeScanner()
        
        print("✅ Drone GUI Connector initialized")
    
    def set_log_callback(self, callback_function):
        """ตั้งค่า callback function สำหรับ log"""
        self.log_callback = callback_function
    
    def log_message(self, message):
        """ส่งข้อความไปยัง GUI log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)  # แสดงใน console ด้วย
        
        if hasattr(self, 'log_callback') and self.log_callback:
            self.log_callback(formatted_message)
    
    # ==================== CONNECTION METHODS ====================
    
    def connect_simulation(self):
        """เชื่อมต่อกับโดรนใน Simulation"""
        try:
            self.log_message("🔄 Connecting to simulation drone...")
            
            if self.sim_drone is None:
                self.sim_drone = NaturalDroneController(use_simulation=True)
            
            if self.sim_drone.use_simulation:
                self.current_drone = self.sim_drone
                self.drone_mode = "simulation"
                self.is_connected = True
                self.log_message("✅ Connected to simulation drone")
                return True
            else:
                self.log_message("❌ Failed to connect to simulation")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Simulation connection error: {e}")
            return False
    
    def connect_real_drone(self):
        """เชื่อมต่อกับโดรนจริง"""
        try:
            self.log_message("🔄 Connecting to real drone...")
            
            if self.real_drone is None:
                self.real_drone = DroneTello(show_cam=False, enable_mission_pad=False)
            
            self.current_drone = self.real_drone
            self.drone_mode = "real"
            self.is_connected = True
            self.log_message("✅ Connected to real drone")
            self.log_message(f"🔋 Battery: {self.real_drone.get_battery()}%")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Real drone connection error: {e}")
            return False
    
    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        try:
            self.log_message("🔄 Disconnecting drone...")
            
            # หยุด auto mission ถ้ากำลังทำงานอยู่
            if self.auto_mission_running:
                self.stop_auto_mission()
            
            # ลงจอดถ้ากำลังบินอยู่
            if self.is_flying:
                self.land()
            
            # หยุดกล้องถ้าเปิดอยู่
            if self.camera_active:
                self.stop_camera()
            
            # ปิดการเชื่อมต่อ
            if self.real_drone:
                self.real_drone.cleanup()
                self.real_drone = None
            
            if self.sim_drone:
                self.sim_drone.stop_simulation()
                self.sim_drone = None
            
            self.current_drone = None
            self.is_connected = False
            self.log_message("✅ Drone disconnected")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Disconnect error: {e}")
            return False
    
    # ==================== BASIC FLIGHT METHODS ====================
    
    def takeoff(self):
        """ขึ้นบิน"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return False
        
        try:
            self.log_message("🚁 Taking off...")
            
            if self.drone_mode == "simulation":
                success = self.current_drone.takeoff()
            else:  # real drone
                self.current_drone.takeoff()
                success = True
            
            if success:
                self.is_flying = True
                self.log_message("✅ Takeoff successful")
                self._update_position()
            else:
                self.log_message("❌ Takeoff failed")
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ Takeoff error: {e}")
            return False
    
    def land(self):
        """ลงจอด"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return False
        
        try:
            self.log_message("🛬 Landing...")
            
            if self.drone_mode == "simulation":
                success = self.current_drone.land()
            else:  # real drone
                self.current_drone.land()
                success = True
            
            if success:
                self.is_flying = False
                self.log_message("✅ Landing successful")
            else:
                self.log_message("❌ Landing failed")
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ Landing error: {e}")
            return False
    
    def hover(self, duration=3):
        """ลอยอยู่กับที่"""
        if not self.is_flying:
            self.log_message("❌ Drone not flying")
            return False
        
        try:
            self.log_message(f"🚁 Hovering for {duration} seconds...")
            
            if self.drone_mode == "simulation":
                success = self.current_drone.hover(duration)
            else:  # real drone
                time.sleep(duration)
                success = True
            
            if success:
                self.log_message("✅ Hover complete")
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ Hover error: {e}")
            return False
    
    # ==================== MOVEMENT METHODS ====================
    
    def move_forward(self, distance=0.5):
        """เคลื่อนที่ไปข้างหน้า"""
        return self._execute_movement("forward", distance)
    
    def move_backward(self, distance=0.5):
        """เคลื่อนที่ไปข้างหลัง"""
        return self._execute_movement("backward", distance)
    
    def move_left(self, distance=0.5):
        """เคลื่อนที่ไปทางซ้าย"""
        return self._execute_movement("left", distance)
    
    def move_right(self, distance=0.5):
        """เคลื่อนที่ไปทางขวา"""
        return self._execute_movement("right", distance)
    
    def move_up(self, distance=0.5):
        """เคลื่อนที่ขึ้น"""
        return self._execute_movement("up", distance)
    
    def move_down(self, distance=0.5):
        """เคลื่อนที่ลง"""
        return self._execute_movement("down", distance)
    
    def _execute_movement(self, direction, distance):
        """ดำเนินการเคลื่อนที่"""
        if not self.is_flying:
            self.log_message("❌ Drone not flying")
            return False
        
        try:
            self.log_message(f"🚁 Moving {direction} {distance}m...")
            
            if self.drone_mode == "simulation":
                if direction == "forward":
                    success = self.current_drone.move_forward(distance)
                elif direction == "backward":
                    success = self.current_drone.move_backward(distance)
                elif direction == "left":
                    success = self.current_drone.move_left(distance)
                elif direction == "right":
                    success = self.current_drone.move_right(distance)
                elif direction == "up":
                    success = self.current_drone.move_up(distance)
                elif direction == "down":
                    success = self.current_drone.move_down(distance)
                else:
                    success = False
            else:  # real drone
                distance_cm = int(distance * 100)
                if direction == "forward":
                    self.current_drone.move_forward(distance_cm)
                elif direction == "backward":
                    self.current_drone.move_back(distance_cm)
                elif direction == "left":
                    self.current_drone.move_left(distance_cm)
                elif direction == "right":
                    self.current_drone.move_right(distance_cm)
                elif direction == "up":
                    self.current_drone.move_up(distance_cm)
                elif direction == "down":
                    self.current_drone.move_down(distance_cm)
                success = True
            
            if success:
                self.log_message(f"✅ Move {direction} complete")
                self._update_position()
            else:
                self.log_message(f"❌ Move {direction} failed")
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ Movement error: {e}")
            return False
    
    def rotate_clockwise(self, angle=90):
        """หมุนตามเข็มนาฬิกา"""
        return self._execute_rotation("clockwise", angle)
    
    def rotate_counterclockwise(self, angle=90):
        """หมุนทวนเข็มนาฬิกา"""
        return self._execute_rotation("counterclockwise", angle)
    
    def _execute_rotation(self, direction, angle):
        """ดำเนินการหมุน"""
        if not self.is_flying:
            self.log_message("❌ Drone not flying")
            return False
        
        try:
            self.log_message(f"🔄 Rotating {direction} {angle}°...")
            
            if self.drone_mode == "simulation":
                if direction == "clockwise":
                    success = self.current_drone.rotate_clockwise(angle)
                else:
                    success = self.current_drone.rotate_counterclockwise(angle)
            else:  # real drone
                if direction == "clockwise":
                    self.current_drone.rotate_clockwise(int(angle))
                else:
                    self.current_drone.rotate_counter_clockwise(int(angle))
                success = True
            
            if success:
                self.log_message(f"✅ Rotation {direction} complete")
            else:
                self.log_message(f"❌ Rotation {direction} failed")
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ Rotation error: {e}")
            return False
    
    # ==================== CAMERA METHODS ====================
    
    def start_camera(self):
        """เริ่มกล้อง"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return False
        
        try:
            self.log_message("📸 Starting camera...")
            
            if self.drone_mode == "simulation":
                if hasattr(self.current_drone, 'camera') and self.current_drone.camera:
                    self.camera_active = True
                    self.log_message("✅ Simulation camera ready")
                    return True
                else:
                    self.log_message("❌ Simulation camera not available")
                    return False
            else:  # real drone
                self.current_drone.start_camera_display()
                self.camera_active = True
                self.log_message("✅ Real drone camera started")
                return True
                
        except Exception as e:
            self.log_message(f"❌ Camera start error: {e}")
            return False
    
    def stop_camera(self):
        """หยุดกล้อง"""
        try:
            self.log_message("📸 Stopping camera...")
            
            if self.drone_mode == "real" and self.real_drone:
                self.real_drone.stop_camera_display()
            
            self.camera_active = False
            self.log_message("✅ Camera stopped")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Camera stop error: {e}")
            return False
    
    def take_picture(self, count=1):
        """ถ่ายรูป"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return []
        
        try:
            self.log_message(f"📸 Taking {count} picture(s)...")
            
            captured_files = []
            
            if self.drone_mode == "simulation":
                for i in range(count):
                    if hasattr(self.current_drone, 'camera') and self.current_drone.camera:
                        filename = self.current_drone.camera.simcapture()
                        if filename:
                            captured_files.append(filename)
                            self.log_message(f"✅ Captured: {filename}")
                    else:
                        self.log_message("❌ Simulation camera not available")
                        break
            else:  # real drone
                folder = "captured_images/"
                if not os.path.exists(folder):
                    os.makedirs(folder)
                captured_files = self.real_drone.capture(count=count, folder=folder)
            
            self.last_captured_images = captured_files
            self.log_message(f"✅ Captured {len(captured_files)} images")
            
            return captured_files
            
        except Exception as e:
            self.log_message(f"❌ Picture taking error: {e}")
            return []
    
    def scan_qr_code(self, image_path=None):
        """แสกน QR Code"""
        try:
            if image_path is None:
                if not self.last_captured_images:
                    self.log_message("❌ No images to scan. Take a picture first.")
                    return []
                image_path = self.last_captured_images[-1]  # ใช้รูปล่าสุด
            
            self.log_message(f"🔍 Scanning QR code in: {image_path}")
            
            results = self.qr_scanner.scan_qr_code(image_path)
            
            if results:
                self.last_qr_results = results
                for result in results:
                    self.log_message(f"📱 QR Code found: {result['data']}")
                return results
            else:
                self.log_message("❌ No QR codes found")
                return []
                
        except Exception as e:
            self.log_message(f"❌ QR scanning error: {e}")
            return []
    
    # ==================== MISSION PAD METHODS ====================
    
    def enable_mission_pads(self):
        """เปิดใช้งาน Mission Pads"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return False
        
        try:
            self.log_message("🎯 Enabling mission pads...")
            
            # เปิดใช้งาน Mission Pad Detectors
            success_improved = False
            success_basic = False
            
            if self.improved_mission_pad_detector:
                try:
                    self.improved_mission_pad_detector.enable_mission_pad_detection()
                    success_improved = True
                    self.log_message("✅ Improved Mission Pad Detector enabled")
                except Exception as e:
                    self.log_message(f"⚠️ Improved detector error: {e}")
            
            if self.basic_mission_pad_detector:
                try:
                    # Basic detector ไม่มี enable method - ใช้งานได้ทันที
                    success_basic = True
                    self.log_message("✅ Basic Mission Pad Detector ready")
                except Exception as e:
                    self.log_message(f"⚠️ Basic detector error: {e}")
            
            # เปิดใช้งาน Mission Pads บนโดรน (ถ้าเป็นโดรนจริง)
            if self.drone_mode == "real" and self.real_drone:
                try:
                    self.real_drone.enable_mission_pads()
                    self.log_message("✅ Real drone mission pads enabled")
                except Exception as e:
                    self.log_message(f"⚠️ Real drone mission pad error: {e}")
            
            # ตรวจสอบว่ามี detector อย่างน้อยหนึ่งตัวที่ใช้งานได้
            if success_improved or success_basic:
                self.mission_pad_enabled = True
                self.log_message("✅ Mission pads enabled successfully")
                return True
            else:
                self.log_message("❌ No mission pad detectors available")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Mission pad enable error: {e}")
            return False
    
    def detect_mission_pads(self, detector_type="auto"):
        """ตรวจหา Mission Pads
        
        Args:
            detector_type (str): "auto", "improved", "basic", หรือ "all"
        """
        if not self.mission_pad_enabled:
            self.log_message("❌ Mission pads not enabled")
            return []
        
        try:
            self.log_message(f"🔍 Detecting mission pads using {detector_type} method...")
            
            detected_pads = []
            
            # ถ่ายรูปก่อน
            images = self.take_picture(1)
            if not images:
                self.log_message("❌ Failed to capture image for mission pad detection")
                return []
            
            image_path = images[0]
            self.log_message(f"📸 Using image: {image_path}")
            
            # ใช้ detector ตามที่เลือก
            if detector_type == "auto" or detector_type == "all":
                # ลองใช้ Improved Detector ก่อน
                if self.improved_mission_pad_detector:
                    improved_result = self._detect_with_improved(image_path)
                    if improved_result:
                        detected_pads.extend(improved_result)
                
                # ถ้าไม่เจอ หรือต้องการใช้ทั้งหมด ก็ลอง Basic Detector
                if (not detected_pads and detector_type == "auto") or detector_type == "all":
                    if self.basic_mission_pad_detector:
                        basic_result = self._detect_with_basic(image_path)
                        if basic_result:
                            detected_pads.extend(basic_result)
            
            elif detector_type == "improved":
                if self.improved_mission_pad_detector:
                    improved_result = self._detect_with_improved(image_path)
                    if improved_result:
                        detected_pads.extend(improved_result)
                else:
                    self.log_message("❌ Improved detector not available")
            
            elif detector_type == "basic":
                if self.basic_mission_pad_detector:
                    basic_result = self._detect_with_basic(image_path)
                    if basic_result:
                        detected_pads.extend(basic_result)
                else:
                    self.log_message("❌ Basic detector not available")
            
            # ลองใช้ Real Drone API (ถ้าเป็นโดรนจริง)
            if self.drone_mode == "real" and self.real_drone:
                try:
                    pad_id = self.real_drone.get_mission_pad_id()
                    if pad_id != -1:
                        detected_pads.append({
                            'id': str(pad_id),
                            'method': 'real_drone_api',
                            'confidence': 1.0
                        })
                        self.log_message(f"🎯 Real drone detected mission pad: {pad_id}")
                except Exception as e:
                    self.log_message(f"⚠️ Real drone detection error: {e}")
            
            # ลบ duplicates และจัดเรียง
            unique_pads = self._remove_duplicate_pads(detected_pads)
            self.detected_mission_pads = unique_pads
            
            if unique_pads:
                for pad in unique_pads:
                    self.log_message(f"🎯 Mission pad detected: ID={pad['id']}, Method={pad.get('method', 'unknown')}, Confidence={pad.get('confidence', 0):.2f}")
            else:
                self.log_message("❌ No mission pads detected")
            
            return unique_pads
            
        except Exception as e:
            self.log_message(f"❌ Mission pad detection error: {e}")
            return []
    
    def _detect_with_improved(self, image_path):
        """ใช้ Improved Mission Pad Detector"""
        try:
            detected_id = self.improved_mission_pad_detector.get_mission_pad_id(image_path)
            
            if detected_id is not None:
                return [{
                    'id': str(detected_id),
                    'method': 'improved_detector',
                    'confidence': 0.8,  # สามารถปรับปรุงให้ได้ confidence จริงได้
                    'image_path': image_path
                }]
            return []
            
        except Exception as e:
            self.log_message(f"❌ Improved detector error: {e}")
            return []
    
    def _detect_with_basic(self, image_path):
        """ใช้ Basic Mission Pad Detector"""
        try:
            detected_id = self.basic_mission_pad_detector.detect_mission_pad(image_path)
            
            if detected_id is not None:
                return [{
                    'id': str(detected_id),
                    'method': 'basic_detector', 
                    'confidence': 0.7,  # สามารถปรับปรุงให้ได้ confidence จริงได้
                    'image_path': image_path
                }]
            return []
            
        except Exception as e:
            self.log_message(f"❌ Basic detector error: {e}")
            return []
    
    def _remove_duplicate_pads(self, detected_pads):
        """ลบ Mission Pads ที่ซ้ำกัน โดยเก็บที่มี confidence สูงสุด"""
        if not detected_pads:
            return []
        
        # จัดกลุ่มตาม ID
        pad_groups = {}
        for pad in detected_pads:
            pad_id = pad['id']
            if pad_id not in pad_groups:
                pad_groups[pad_id] = []
            pad_groups[pad_id].append(pad)
        
        # เลือก pad ที่มี confidence สูงสุดในแต่ละกลุ่ม
        unique_pads = []
        for pad_id, pads in pad_groups.items():
            best_pad = max(pads, key=lambda x: x.get('confidence', 0))
            unique_pads.append(best_pad)
        
        return unique_pads
    
    def _initialize_mission_pad_detectors(self):
        """เริ่มต้น Mission Pad Detectors"""
        try:
            # เริ่มต้น Improved Mission Pad Detector
            if IMPROVED_MISSION_PAD_AVAILABLE:
                self.improved_mission_pad_detector = ImprovedMissionPadDetector()
                self.log_message("✅ Improved Mission Pad Detector initialized")
            
            # เริ่มต้น Basic Mission Pad Detector
            if MISSION_PAD_AVAILABLE:
                self.basic_mission_pad_detector = MissionPadDetector()
                self.log_message("✅ Basic Mission Pad Detector initialized")
            
            if not (IMPROVED_MISSION_PAD_AVAILABLE or MISSION_PAD_AVAILABLE):
                self.log_message("⚠️ No Mission Pad Detectors available")
            
        except Exception as e:
            self.log_message(f"❌ Mission Pad Detector initialization error: {e}")
    
    def get_available_mission_pad_detectors(self):
        """รับรายการ Mission Pad Detectors ที่พร้อมใช้งาน"""
        detectors = []
        if self.improved_mission_pad_detector:
            detectors.append("improved")
        if self.basic_mission_pad_detector:
            detectors.append("basic")
        return detectors
    
    # ==================== AUTO MISSION METHODS ====================
    
    def start_auto_mission(self, mission_type="basic"):
        """เริ่ม Auto Mission"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return False
        
        if self.auto_mission_running:
            self.log_message("❌ Auto mission already running")
            return False
        
        try:
            self.log_message(f"🚀 Starting auto mission: {mission_type}")
            self.auto_mission_running = True
            
            # รัน mission ใน thread แยก
            mission_thread = threading.Thread(
                target=self._run_auto_mission, 
                args=(mission_type,), 
                daemon=True
            )
            mission_thread.start()
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Auto mission start error: {e}")
            self.auto_mission_running = False
            return False
    
    def stop_auto_mission(self):
        """หยุด Auto Mission"""
        self.auto_mission_running = False
        self.log_message("🛑 Auto mission stopped")
    
    def _run_auto_mission(self, mission_type):
        """รัน Auto Mission (ทำงานใน background thread)"""
        try:
            if mission_type == "basic":
                self._basic_mission()
            elif mission_type == "scan_area":
                self._scan_area_mission()
            elif mission_type == "find_mission_pads":
                self._find_mission_pads_mission()
            elif mission_type == "custom":
                self._custom_mission()
            else:
                self.log_message(f"❌ Unknown mission type: {mission_type}")
            
        except Exception as e:
            self.log_message(f"❌ Auto mission error: {e}")
        finally:
            self.auto_mission_running = False
            self.log_message("✅ Auto mission completed")
    
    def _basic_mission(self):
        """Basic Auto Mission"""
        self.log_message("🚀 Executing basic mission...")
        
        # 1. ขึ้นบิน
        if not self.is_flying:
            self.takeoff()
            time.sleep(2)
        
        # 2. เคลื่อนที่ไปรอบๆ
        movements = [
            ("forward", 1.0),
            ("right", 1.0),
            ("backward", 1.0),
            ("left", 1.0)
        ]
        
        for direction, distance in movements:
            if not self.auto_mission_running:
                break
            
            self._execute_movement(direction, distance)
            time.sleep(1)
        
        # 3. ลงจอด
        self.land()
    
    def _scan_area_mission(self):
        """Scan Area Mission"""
        self.log_message("🔍 Executing scan area mission...")
        
        # 1. ขึ้นบิน
        if not self.is_flying:
            self.takeoff()
            time.sleep(2)
        
        # 2. สแกนรอบตัว
        for i in range(4):
            if not self.auto_mission_running:
                break
            
            # ถ่ายรูป
            self.take_picture(1)
            time.sleep(1)
            
            # หมุน 90 องศา
            self.rotate_clockwise(90)
            time.sleep(1)
        
        # 3. ลงจอด
        self.land()
    
    def _find_mission_pads_mission(self):
        """Find Mission Pads Mission - ปรับปรุงใหม่"""
        self.log_message("🎯 Executing find mission pads mission...")
        
        # 1. เปิด Mission Pads
        self.enable_mission_pads()
        time.sleep(1)
        
        # 2. ขึ้นบิน
        if not self.is_flying:
            self.takeoff()
            time.sleep(2)
        
        # 3. ค้นหา Mission Pads แบบรอบคอบ
        found_pads = []
        search_positions = [
            # ตำแหน่งปัจจุบัน
            (0, 0),
            # เคลื่อนที่ไปรอบๆ
            (0.5, 0), (1.0, 0), (1.0, 0.5), (1.0, 1.0),
            (0.5, 1.0), (0, 1.0), (-0.5, 1.0), (-1.0, 1.0),
            (-1.0, 0.5), (-1.0, 0), (-1.0, -0.5), (-1.0, -1.0),
            (-0.5, -1.0), (0, -1.0), (0.5, -1.0), (1.0, -1.0),
            (1.0, -0.5), (0.5, -0.5), (0, -0.5)
        ]
        
        current_pos = [0, 0]  # ติดตามตำแหน่งปัจจุบัน
        
        for i, (target_x, target_y) in enumerate(search_positions):
            if not self.auto_mission_running:
                break
            
            self.log_message(f"🔍 Search position {i+1}/{len(search_positions)}: ({target_x}, {target_y})")
            
            # เคลื่อนที่ไปยังตำแหน่งเป้าหมาย
            dx = target_x - current_pos[0]
            dy = target_y - current_pos[1]
            
            if abs(dx) > 0.1:  # เคลื่อนที่ในแกน X
                if dx > 0:
                    self._execute_movement("right", abs(dx))
                else:
                    self._execute_movement("left", abs(dx))
            
            if abs(dy) > 0.1:  # เคลื่อนที่ในแกน Y
                if dy > 0:
                    self._execute_movement("forward", abs(dy))
                else:
                    self._execute_movement("backward", abs(dy))
            
            current_pos = [target_x, target_y]
            time.sleep(1)
            
            # ตรวจหา Mission Pads ด้วยทุกวิธี
            pads_auto = self.detect_mission_pads("auto")
            pads_all = self.detect_mission_pads("all")
            
            # รวมผลลัพธ์
            all_pads = pads_auto + pads_all
            found_pads.extend(all_pads)
            
            if all_pads:
                self.log_message(f"🎯 Found {len(all_pads)} mission pad(s) at position ({target_x}, {target_y})")
                for pad in all_pads:
                    self.log_message(f"  📍 ID: {pad['id']}, Method: {pad.get('method', 'unknown')}")
            
            # หมุนรอบตัวเพื่อค้นหา
            for angle in [90, 90, 90, 90]:  # หมุน 360 องศา
                if not self.auto_mission_running:
                    break
                
                self.rotate_clockwise(angle)
                time.sleep(1)
                
                # ตรวจหาอีกครั้งหลังหมุน
                pads_rotated = self.detect_mission_pads("auto")
                found_pads.extend(pads_rotated)
                
                if pads_rotated:
                    self.log_message(f"🔄 Found additional pads after rotation: {len(pads_rotated)}")
        
        # 4. สรุปผลและกลับไปยังตำแหน่งเริ่มต้น
        self.log_message("🏠 Returning to start position...")
        self._execute_movement("right", -current_pos[0]) if current_pos[0] < 0 else self._execute_movement("left", current_pos[0])
        self._execute_movement("forward", -current_pos[1]) if current_pos[1] < 0 else self._execute_movement("backward", current_pos[1])
        
        # 5. สรุปผล
        unique_pads = self._remove_duplicate_pads(found_pads)
        unique_ids = list(set([pad['id'] for pad in unique_pads]))
        
        self.log_message(f"📊 Mission Pad Search Summary:")
        self.log_message(f"  Total detections: {len(found_pads)}")
        self.log_message(f"  Unique mission pads: {len(unique_ids)}")
        self.log_message(f"  Found IDs: {sorted(unique_ids)}")
        
        for pad_id in sorted(unique_ids):
            pad_detections = [p for p in found_pads if p['id'] == pad_id]
            methods = list(set([p.get('method', 'unknown') for p in pad_detections]))
            self.log_message(f"  🎯 Mission Pad {pad_id}: {len(pad_detections)} detections, methods: {methods}")
        
        # 6. ลงจอด
        self.land()
    
    def _custom_mission(self):
        """Custom Mission - สามารถปรับแต่งได้"""
        self.log_message("🎨 Executing custom mission...")
        
        # ตัวอย่างภารกิจปรับแต่งได้
        # สามารถแก้ไขตรงนี้ตามต้องการ
        
        # 1. ขึ้นบิน
        if not self.is_flying:
            self.takeoff()
            time.sleep(2)
        
        # 2. ทำภารกิจตามต้องการ
        # เช่น เคลื่อนที่ไปยังตำแหน่งต่างๆ, ถ่ายรูป, แสกน QR Code
        
        custom_tasks = [
            lambda: self.move_up(0.5),
            lambda: self.take_picture(1),
            lambda: self.rotate_clockwise(180),
            lambda: self.take_picture(1),
            lambda: self.move_down(0.5)
        ]
        
        for task in custom_tasks:
            if not self.auto_mission_running:
                break
            task()
            time.sleep(1)
        
        # 3. ลงจอด
        self.land()
    
    # ==================== UTILITY METHODS ====================
    
    def get_status(self):
        """รับสถานะปัจจุบัน"""
        status = {
            'connected': self.is_connected,
            'mode': self.drone_mode,
            'flying': self.is_flying,
            'position': self.current_position,
            'camera_active': self.camera_active,
            'mission_pad_enabled': self.mission_pad_enabled,
            'auto_mission_running': self.auto_mission_running
        }
        
        if self.drone_mode == "real" and self.real_drone:
            try:
                status['battery'] = self.real_drone.get_battery()
                status['temperature'] = self.real_drone.get_temperature()
            except:
                pass
        
        return status
    
    def _update_position(self):
        """อัปเดตตำแหน่งปัจจุบัน"""
        try:
            if self.drone_mode == "simulation" and self.current_drone:
                if hasattr(self.current_drone, 'get_position'):
                    self.current_position = self.current_drone.get_position()
            # สำหรับโดรนจริง ไม่มี position tracking โดยตรง
        except:
            pass
    
    def get_wind_status(self):
        """รับสถานะลม (simulation เท่านั้น)"""
        if self.drone_mode == "simulation" and self.current_drone:
            try:
                if hasattr(self.current_drone, 'get_wind_status'):
                    return self.current_drone.get_wind_status()
            except:
                pass
        return None
    
    def set_wind_conditions(self, strength=0, direction=[0,0,0], turbulence=False, gusts=False):
        """ตั้งค่าสภาพลม (simulation เท่านั้น)"""
        if self.drone_mode == "simulation" and self.current_drone:
            try:
                if hasattr(self.current_drone, 'set_wind_strength'):
                    self.current_drone.set_wind_strength(strength)
                    self.current_drone.set_wind_direction(*direction)
                    self.current_drone.enable_turbulence(turbulence)
                    self.current_drone.enable_wind_gusts(gusts)
                    self.log_message(f"🌪️ Wind conditions set: strength={strength}, turbulence={turbulence}")
                    return True
            except Exception as e:
                self.log_message(f"❌ Wind setting error: {e}")
        return False


# ==================== GUI INTEGRATION FUNCTIONS ====================

def create_drone_control_tab(notebook, drone_connector):
    """สร้าง Tab สำหรับควบคุมโดรน"""
    drone_tab = ttk.Frame(notebook)
    notebook.add(drone_tab, text="🚁 Drone Control")
    
    # Connection frame
    conn_frame = tk.LabelFrame(drone_tab, text="🔌 Connection", font=('Arial', 10, 'bold'))
    conn_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Button(conn_frame, text="📡 Connect Simulation", 
             command=drone_connector.connect_simulation,
             bg='#3498db', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5, pady=5)
    
    tk.Button(conn_frame, text="📱 Connect Real Drone", 
             command=drone_connector.connect_real_drone,
             bg='#e67e22', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5, pady=5)
    
    tk.Button(conn_frame, text="❌ Disconnect", 
             command=drone_connector.disconnect,
             bg='#e74c3c', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5, pady=5)
    
    # Python Code Editor Frame
    code_frame = tk.LabelFrame(drone_tab, text="🐍 Python Drone Control", font=('Arial', 10, 'bold'))
    code_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Code input area
    code_input_frame = tk.Frame(code_frame)
    code_input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # Label
    tk.Label(code_input_frame, text="Enter Python code to control the drone:", 
             font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=5)
    
    # Text widget with scrollbar
    text_frame = tk.Frame(code_input_frame)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    code_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10), 
                       bg='#2c3e50', fg='#ecf0f1', insertbackground='white',
                       selectbackground='#3498db', relief=tk.FLAT, bd=5)
    
    scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=code_text.yview)
    code_text.configure(yscrollcommand=scrollbar.set)
    
    code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Add default example code
    default_code = """# 🚁 Python Drone Control - Simple Examples
# Available drone object: 'drone'

# 1. Basic Flight Test
drone.takeoff()                    # Take off
print("✅ Takeoff successful!")
drone.hover(3)                     # Hover for 3 seconds
drone.move_forward(1.0)           # Move forward 1 meter
drone.rotate_clockwise(90)        # Rotate 90 degrees
drone.land()                      # Land
print("✅ Basic flight completed!")

# 2. Square Flight Pattern (uncomment to use)
# drone.takeoff()
# for i in range(4):
#     drone.move_forward(1.0)
#     drone.rotate_clockwise(90)
#     print(f"Completed side {i+1}")
# drone.land()

# 3. Camera and Detection (uncomment to use)
# drone.start_camera()
# drone.enable_mission_pads()
# drone.takeoff()
# images = drone.take_picture(1)
# pads = drone.detect_mission_pads("auto")
# print(f"Found {len(pads)} mission pads")
# drone.land()

# 4. Status Check
print("=== Current Status ===")
print(f"Connected: {drone.is_connected}")
print(f"Flying: {drone.is_flying}")
print(f"Position: {drone.current_position}")
"""
    
    code_text.insert(tk.END, default_code)
    
    # Control buttons
    button_frame = tk.Frame(code_frame)
    button_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def execute_code():
        """Execute the Python code in the text area"""
        try:
            code = code_text.get(1.0, tk.END).strip()
            if not code:
                drone_connector.log_message("❌ No code to execute")
                return
            
            drone_connector.log_message("🐍 Executing Python code...")
            
            # Create a safe execution environment
            exec_globals = {
                'drone': drone_connector,
                'print': lambda *args: drone_connector.log_message(" ".join(str(arg) for arg in args)),
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'sum': sum,
                    'any': any,
                    'all': all,
                }
            }
            
            # Execute the code
            exec(code, exec_globals)
            drone_connector.log_message("✅ Code executed successfully")
            
        except Exception as e:
            drone_connector.log_message(f"❌ Code execution error: {e}")
    
    def clear_code():
        """Clear the code text area"""
        code_text.delete(1.0, tk.END)
        drone_connector.log_message("🗑️ Code area cleared")
    
    def load_example():
        """Load example code"""
        code_text.delete(1.0, tk.END)
        code_text.insert(tk.END, default_code)
        drone_connector.log_message("📝 Example code loaded")
    
    def save_code():
        """Save code to file"""
        try:
            from tkinter import filedialog
            code = code_text.get(1.0, tk.END)
            file_path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                drone_connector.log_message(f"💾 Code saved to: {file_path}")
        except Exception as e:
            drone_connector.log_message(f"❌ Save error: {e}")
    
    def load_code():
        """Load code from file"""
        try:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                filetypes=[("Python files", "*.py"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                code_text.delete(1.0, tk.END)
                code_text.insert(tk.END, code)
                drone_connector.log_message(f"� Code loaded from: {file_path}")
        except Exception as e:
            drone_connector.log_message(f"❌ Load error: {e}")
    
    def load_examples_file():
        """Load comprehensive examples from file"""
        try:
            examples_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drone_code_examples.py")
            if os.path.exists(examples_path):
                with open(examples_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                code_text.delete(1.0, tk.END)
                code_text.insert(tk.END, code)
                drone_connector.log_message("📚 Comprehensive examples loaded")
            else:
                drone_connector.log_message("❌ Examples file not found")
        except Exception as e:
            drone_connector.log_message(f"❌ Examples load error: {e}")
    
    # Buttons
    tk.Button(button_frame, text="▶️ Execute Code", command=execute_code,
             bg='#27ae60', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
    
    tk.Button(button_frame, text="�️ Clear", command=clear_code,
             bg='#e74c3c', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
    
    tk.Button(button_frame, text="� Load Example", command=load_example,
             bg='#3498db', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
    
    tk.Button(button_frame, text="� Save Code", command=save_code,
             bg='#9b59b6', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
    
    tk.Button(button_frame, text="📂 Load Code", command=load_code,
             bg='#e67e22', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
    
    tk.Button(button_frame, text="📚 All Examples", command=load_examples_file,
             bg='#2c3e50', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
    
    # Quick action buttons
    quick_frame = tk.Frame(code_frame)
    quick_frame.pack(fill=tk.X, padx=5, pady=5)
    
    tk.Label(quick_frame, text="Quick Actions:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
    
    def quick_takeoff():
        code_text.delete(1.0, tk.END)
        code_text.insert(tk.END, "drone.takeoff()\nprint('Drone took off!')")
    
    def quick_land():
        code_text.delete(1.0, tk.END)
        code_text.insert(tk.END, "drone.land()\nprint('Drone landed!')")
    
    def quick_square():
        code_text.delete(1.0, tk.END)
        code_text.insert(tk.END, """# Fly in a square pattern
drone.takeoff()
drone.move_forward(1.0)
drone.rotate_clockwise(90)
drone.move_forward(1.0)
drone.rotate_clockwise(90)
drone.move_forward(1.0)
drone.rotate_clockwise(90)
drone.move_forward(1.0)
drone.rotate_clockwise(90)
drone.land()
print('Square flight completed!')""")
    
    tk.Button(quick_frame, text="🚁 Takeoff", command=quick_takeoff,
             bg='#1abc9c', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
    
    tk.Button(quick_frame, text="🛬 Land", command=quick_land,
             bg='#f39c12', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
    
    tk.Button(quick_frame, text="� Square Flight", command=quick_square,
             bg='#8e44ad', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
    
    return drone_tab


# ==================== MAIN TEST FUNCTION ====================

def main():
    """ฟังก์ชันทดสอบ DroneGUIConnector"""
    print("🚁 Testing Drone GUI Connector...")
    
    # สร้าง connector
    connector = DroneGUIConnector()
    
    # ตั้งค่า log callback (สำหรับทดสอบ)
    connector.set_log_callback(lambda msg: print(f"GUI LOG: {msg}"))
    
    # ทดสอบการเชื่อมต่อ
    print("\n1. Testing connection...")
    success = connector.connect_simulation()
    print(f"Connection result: {success}")
    
    # ทดสอบสถานะ
    print("\n2. Testing status...")
    status = connector.get_status()
    print(f"Status: {status}")
    
    # ทดสอบ GUI Tab creation (จำลอง)
    print("\n3. Testing GUI components...")
    try:
        root = tk.Tk()
        root.title("Drone Connector Test")
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # สร้าง tab
        drone_tab = create_drone_control_tab(notebook, connector)
        
        print("✅ GUI components created successfully")
        
        # ไม่รัน mainloop ในการทดสอบ
        root.destroy()
        
    except Exception as e:
        print(f"❌ GUI test error: {e}")
    
    # ปิดการเชื่อมต่อ
    print("\n4. Testing disconnection...")
    connector.disconnect()
    
    print("\n✅ Drone GUI Connector test completed!")


if __name__ == "__main__":
    main()
