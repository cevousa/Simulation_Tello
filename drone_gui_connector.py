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
    from drone_controller import NaturalDroneController, DroneTello, QRCodeScanner, DroneCamera, ProximitySensorManager
    import drone_controller  # Import module ทั้งหมดเพื่อใช้ในการ dynamic calling
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
        
        # ตัวแปรสำหรับ proximity sensors
        self.proximity_sensors_enabled = False
        
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
        # ป้องกัน recursive call
        if hasattr(self, '_logging_in_progress') and self._logging_in_progress:
            return
        
        self._logging_in_progress = True
        
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            print(formatted_message)  # แสดงใน console ด้วย
            
            # แสดงใน GUI log widget ถ้ามี
            if hasattr(self, 'log_text_widget') and self.log_text_widget:
                try:
                    # Enable text widget for writing
                    self.log_text_widget.config(state=tk.NORMAL)
                    
                    # Insert new message
                    self.log_text_widget.insert(tk.END, formatted_message + "\n")
                    
                    # Color coding for different message types
                    if "❌" in message or "error" in message.lower() or "failed" in message.lower():
                        # Red for errors
                        start_line = self.log_text_widget.index("end-2l linestart")
                        end_line = self.log_text_widget.index("end-1l lineend")
                        self.log_text_widget.tag_add("error", start_line, end_line)
                        self.log_text_widget.tag_config("error", foreground="#ff4444")
                    elif "✅" in message or "successful" in message.lower() or "complete" in message.lower():
                        # Green for success
                        start_line = self.log_text_widget.index("end-2l linestart")
                        end_line = self.log_text_widget.index("end-1l lineend")
                        self.log_text_widget.tag_add("success", start_line, end_line)
                        self.log_text_widget.tag_config("success", foreground="#44ff44")
                    elif "⚠️" in message or "warning" in message.lower():
                        # Yellow for warnings
                        start_line = self.log_text_widget.index("end-2l linestart")
                        end_line = self.log_text_widget.index("end-1l lineend")
                        self.log_text_widget.tag_add("warning", start_line, end_line)
                        self.log_text_widget.tag_config("warning", foreground="#ffff44")
                    elif "🔄" in message or "connecting" in message.lower() or "processing" in message.lower():
                        # Blue for info/processing
                        start_line = self.log_text_widget.index("end-2l linestart")
                        end_line = self.log_text_widget.index("end-1l lineend")
                        self.log_text_widget.tag_add("info", start_line, end_line)
                        self.log_text_widget.tag_config("info", foreground="#44aaff")
                    
                    # Auto-scroll to bottom if enabled
                    if hasattr(self, 'autoscroll_enabled') and self.autoscroll_enabled:
                        self.log_text_widget.see(tk.END)
                    
                    # Limit log length to prevent memory issues (keep last 1000 lines)
                    line_count = int(self.log_text_widget.index('end-1c').split('.')[0])
                    if line_count > 1000:
                        self.log_text_widget.delete(1.0, f"{line_count-1000}.0")
                    
                    # Disable text widget to make it read-only
                    self.log_text_widget.config(state=tk.DISABLED)
                    
                except Exception as e:
                    print(f"Error updating log widget: {e}")
                    # Fallback to original behavior
                    pass
        
        finally:
            self._logging_in_progress = False
    
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
                
                # เปิด proximity sensors อัตโนมัติ
                self.log_message("📡 Auto-enabling proximity sensors...")
                self.enable_proximity_sensors()
                
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
            try:
                battery = self.real_drone.get_battery()
                self.log_message(f"🔋 Battery: {battery}%")
            except:
                self.log_message("🔋 Battery: Unable to read")
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
            
            # เรียกใช้ฟังก์ชันจาก drone_controller โดยตรง
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
            
            # เรียกใช้ฟังก์ชันจาก drone_controller โดยตรง
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
            if self.drone_mode == "real":
                self.log_message(f"🚁 Hovering for {duration} seconds...")
                time.sleep(duration)
                self.log_message("✅ Hover complete")
                return True
            else:
                # สำหรับ simulation เรียก hover function โดยตรง
                self.log_message(f"🚁 Hovering for {duration} seconds...")
                success = self.current_drone.hover(duration)
                if success:
                    self.log_message("✅ Hover complete")
                else:
                    self.log_message("❌ Hover failed")
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
    
    def move_back(self, distance=0.5):
        """เคลื่อนที่ไปข้างหลัง (ชื่อฟังก์ชันหลัก)"""
        return self._execute_movement("back", distance)
    
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
                # เรียกใช้ฟังก์ชันจาก simulation drone โดยตรง
                if direction == "forward":
                    success = self.current_drone.move_forward(distance)
                elif direction == "backward" or direction == "back":
                    success = self.current_drone.move_back(distance)
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
                # เรียกใช้ฟังก์ชันจาก real drone โดยตรง
                distance_cm = int(distance * 100)
                if direction == "forward":
                    self.current_drone.move_forward(distance_cm)
                elif direction == "backward" or direction == "back":
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
    
    def rotate_counter_clockwise(self, angle=90):
        """หมุนทวนเข็มนาฬิกา"""
        return self._execute_rotation("counterclockwise", angle)
    
    # Alias functions สำหรับ backward compatibility
    def counter_clockwise(self, angle=90):
        """Alias สำหรับ rotate_counter_clockwise เพื่อ backward compatibility"""
        return self.rotate_counter_clockwise(angle)
    
    def rotate_counterclockwise(self, angle=90):
        """Alias สำหรับ rotate_counter_clockwise เพื่อ backward compatibility"""
        return self.rotate_counter_clockwise(angle)
    
    def _execute_rotation(self, direction, angle):
        """ดำเนินการหมุน"""
        if not self.is_flying:
            self.log_message("❌ Drone not flying")
            return False
        
        try:
            self.log_message(f"🔄 Rotating {direction} {angle}°...")
            
            if self.drone_mode == "simulation":
                # แก้ไข: สลับการเรียกใช้เพื่อให้ทิศทางถูกต้อง
                if direction == "clockwise":
                    # ใช้ rotate_counter_clockwise เพื่อให้หมุนตามเข็มนาฬิกาจริง
                    success = self.current_drone.rotate_counter_clockwise(angle)
                elif direction == "counterclockwise":
                    # ใช้ rotate_clockwise เพื่อให้หมุนทวนเข็มนาฬิกาจริง
                    success = self.current_drone.rotate_clockwise(angle)
                else:
                    self.log_message(f"❌ Unknown rotation direction: {direction}")
                    return False
            else:  # real drone
                # สำหรับโดรนจริง ใช้ตามปกติ
                if direction == "clockwise":
                    self.current_drone.rotate_clockwise(int(angle))
                elif direction == "counterclockwise":
                    self.current_drone.rotate_counter_clockwise(int(angle))
                else:
                    self.log_message(f"❌ Unknown rotation direction: {direction}")
                    return False
                success = True
            
            if success:
                self.log_message(f"✅ Rotation {direction} {angle}° complete")
            else:
                self.log_message(f"❌ Rotation {direction} failed")
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ Rotation error: {e}")
            return False
    
    # ==================== CAMERA METHODS ====================
    
    def start_camera_display(self):
        """เริ่มแสดงภาพกล้อง - ตรงกับ drone_controller.start_camera_display()"""
        return self.start_camera()

    def stop_camera_display(self):
        """หยุดแสดงภาพกล้อง - ตรงกับ drone_controller.stop_camera_display()"""
        return self.stop_camera()

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
    
    def capture(self, count=1):
        """ถ่ายรูป - ตรงกับ drone_controller.capture()"""
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
    
    def scan_qr(self, image_path=None):
        """แสกน QR Code - ตรงกับ drone_controller.scan_qr()"""
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
    
    def scan_mission_pad(self, detector_type="auto"):
        """แสกน Mission Pad - ตรงกับ drone_controller.scan_mission_pad()
        
        Args:
            detector_type (str): "auto", "improved", "basic", หรือ "all"
        """
        # เปิด Mission Pads อัตโนมัติถ้ายังไม่ได้เปิด
        if not self.mission_pad_enabled:
            self.log_message("🎯 Mission pads not enabled, enabling automatically...")
            if not self.enable_mission_pads():
                self.log_message("❌ Failed to enable mission pads")
                return []
        
        try:
            self.log_message(f"🔍 Detecting mission pads using {detector_type} method...")
            
            detected_pads = []
            
            # ถ่ายรูปด้วยกล้องล่างก่อน (สำหรับ Mission Pad detection)
            self.log_message("📸 Taking bottom camera picture for mission pad detection...")
            
            # ลองใช้กล้องล่างก่อน (สำหรับ simulation)
            bottom_image = None
            if self.drone_mode == "simulation":
                try:
                    bottom_image = self.take_bottom_picture()
                    if bottom_image:
                        self.log_message(f"✅ Bottom camera image captured: {bottom_image}")
                        image_path = bottom_image
                    else:
                        self.log_message("⚠️ Bottom camera failed, using front camera...")
                        images = self.capture(1)
                        if images:
                            image_path = images[0]
                        else:
                            self.log_message("❌ Failed to capture any image")
                            return []
                except Exception as e:
                    self.log_message(f"⚠️ Bottom camera error: {e}, using front camera...")
                    images = self.capture(1)
                    if images:
                        image_path = images[0]
                    else:
                        self.log_message("❌ Failed to capture fallback image")
                        return []
            else:
                # สำหรับโดรนจริง หรือถ้าไม่มีกล้องล่าง ใช้กล้องหน้า
                images = self.capture(1)
                if not images:
                    self.log_message("❌ Failed to capture image for mission pad detection")
                    return []
                image_path = images[0]
            
            self.log_message(f"📸 Using image for detection: {image_path}")
            
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
    
    def get_mission_pad_id(self):
        """ดึง Mission Pad ID - ตรงกับ drone_controller.get_mission_pad_id()
        จะถ่ายรูปด้วยกล้องล่างก่อนแสกน Mission Pad
        """
        self.log_message("🎯 Getting Mission Pad ID...")
        detected_pads = self.scan_mission_pad()
        if detected_pads:
            # คืนค่า ID ของแผ่นแรกที่พบ
            pad_id = detected_pads[0].get('id', None)
            self.log_message(f"✅ Mission Pad ID found: {pad_id}")
            return pad_id
        else:
            self.log_message("❌ No Mission Pad detected")
            return None
    
    def disable_mission_pads(self):
        """ปิดใช้งาน Mission Pad detection - ตรงกับ drone_controller.disable_mission_pads()"""
        self.mission_pad_enabled = False
        self.log_message("🎯 Mission pads disabled")
        return True
    
    # ==================== PROXIMITY SENSORS METHODS ====================
    
    def enable_proximity_sensors(self):
        """เปิดใช้งาน Proximity Sensors - ตรงกับ drone_controller proximity functions"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return False
        
        try:
            self.log_message("📡 Enabling proximity sensors...")
            
            if self.drone_mode == "simulation":
                # ตรวจสอบว่ามี _init_proximity_sensors หรือไม่
                if hasattr(self.current_drone, '_init_proximity_sensors'):
                    self.log_message("🔍 Found _init_proximity_sensors method")
                    success = self.current_drone._init_proximity_sensors()
                    if success:
                        self.proximity_sensors_enabled = True
                        self.log_message("✅ Proximity sensors enabled successfully")
                        return True
                    else:
                        self.log_message("❌ Failed to initialize proximity sensors")
                        
                # ตรวจสอบว่ามี proximity_manager อยู่แล้วหรือไม่
                elif hasattr(self.current_drone, 'proximity_manager') and self.current_drone.proximity_manager:
                    self.log_message("🔍 Found existing proximity_manager")
                    self.proximity_sensors_enabled = True
                    self.log_message("✅ Using existing proximity sensors")
                    return True
                
                # สร้าง proximity_manager ใหม่
                else:
                    self.log_message("🔧 Creating new proximity manager...")
                    try:
                        if hasattr(self.current_drone, 'sim') and hasattr(self.current_drone, 'drone_handle'):
                            self.log_message(f"🔍 Using sim: {type(self.current_drone.sim)} and drone_handle: {self.current_drone.drone_handle}")
                            
                            # สร้าง ProximitySensorManager ใหม่
                            self.current_drone.proximity_manager = ProximitySensorManager(
                                self.current_drone.sim, 
                                self.current_drone.drone_handle
                            )
                            
                            # เริ่มต้น sensors
                            success = self.current_drone.proximity_manager.setup()
                            if success:
                                self.proximity_sensors_enabled = True
                                self.log_message("✅ Proximity manager created and initialized successfully")
                                return True
                            else:
                                self.log_message("❌ Failed to initialize proximity sensors in new manager")
                        else:
                            self.log_message("❌ Missing sim or drone_handle for proximity manager")
                            self.log_message(f"   sim exists: {hasattr(self.current_drone, 'sim')}")
                            self.log_message(f"   drone_handle exists: {hasattr(self.current_drone, 'drone_handle')}")
                            
                    except Exception as create_error:
                        self.log_message(f"❌ Error creating proximity manager: {create_error}")
                        import traceback
                        self.log_message(f"   Traceback: {traceback.format_exc()}")
                
                # ถ้าไม่มี proximity sensors ก็ยังใช้งานได้ด้วยวิธีอื่น
                self.log_message("⚠️ No proximity sensors found, using fallback methods")
                self.proximity_sensors_enabled = False
                return False
                
            elif self.drone_mode == "real":
                # สำหรับโดรนจริง proximity sensors อาจไม่มี
                self.log_message("⚠️ Proximity sensors not available on real drone")
                self.proximity_sensors_enabled = False
                return False
            else:
                self.log_message("⚠️ Unknown drone mode")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Proximity sensors enable error: {e}")
            return False
    
    def read_distance(self):
        """อ่านระยะห่างจาก proximity sensor - ตรงกับ drone_controller.read_distance()"""
        
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return None
        
        try:
            if hasattr(self.current_drone, 'proximity_manager') and self.current_drone.proximity_manager:
                distance = self.current_drone.proximity_manager.read_distance()
                if distance is not None:
                    self.log_message(f"📏 Distance: {distance:.3f}m")
                    return distance
                else:
                    self.log_message("❌ No object detected by proximity sensor")
                    return None
            else:
                self.log_message("❌ Proximity sensors not available")
                return None
                
        except Exception as e:
            self.log_message(f"❌ Distance read error: {e}")
            return None
    
    def get_distance_tof(self):
        """วัดความสูงจากพื้น - ตรงกับ drone_controller.get_height()
        
        Returns:
            float: ความสูง (เมตร) หรือ None
        """
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return None
        
        try:
            # ตรวจสอบและเปิดใช้งาน proximity sensors อัตโนมัติถ้ายังไม่ได้เปิด (แต่ไม่ loop)
            if not hasattr(self, 'proximity_sensors_enabled') or not self.proximity_sensors_enabled:
                if not hasattr(self, '_trying_to_enable_sensors'):
                    self._trying_to_enable_sensors = True
                    self.log_message("🔧 Auto-enabling proximity sensors...")
                    self.enable_proximity_sensors()
                    delattr(self, '_trying_to_enable_sensors')
            
            # ใช้งานเหมือน drone_controller.py - เรียก read_distance() ผ่าน proximity_manager
            if hasattr(self.current_drone, 'proximity_manager') and self.current_drone.proximity_manager:
                distance = self.current_drone.proximity_manager.read_distance()
                if distance is not None:
                    self.log_message(f"📏 ความสูง: {distance:.2f} เมตร")
                    return distance
                else:
                    self.log_message("❌ วัดความสูงไม่ได้")
                    return None
            
            # Fallback: ใช้ simulation API โดยตรง
            if self.drone_mode == "simulation" and hasattr(self.current_drone, 'sim') and hasattr(self.current_drone, 'drone_handle'):
                try:
                    position = self.current_drone.sim.getObjectPosition(self.current_drone.drone_handle, -1)
                    if position and len(position) >= 3:
                        height = abs(position[2])
                        self.log_message(f"📏 ความสูง (simulation): {height:.2f} เมตร")
                        return height
                except Exception as sim_error:
                    self.log_message(f"⚠️ Simulation height read error: {sim_error}")
            
            self.log_message("❌ ไม่สามารถวัดความสูงได้")
            return None
                
        except Exception as e:
            self.log_message(f"❌ Height measurement error: {e}")
            return None
            if self.drone_mode == "simulation" and hasattr(self.current_drone, 'sim') and hasattr(self.current_drone, 'drone_handle'):
                try:
                    position = self.current_drone.sim.getObjectPosition(self.current_drone.drone_handle, -1)
                    if position and len(position) >= 3:
                        height = abs(position[2])
                        self.log_message(f"📏 Height from simulation: {height:.3f}m")
                        return height
                except Exception as sim_error:
                    self.log_message(f"⚠️ Simulation height read error: {sim_error}")
            
            # 5. ถ้าไม่มีวิธีไหนได้ผล ใช้ค่าประมาณจาก current_position
            if self.current_position and len(self.current_position) >= 3:
                height = abs(self.current_position[2])
                if height > 0:
                    self.log_message(f"📏 Height from cached position: {height:.3f}m")
                    return height
            
            # 6. ถ้าโดรนบินอยู่ ให้ค่าประมาณ
            if self.is_flying:
                estimated_height = 1.0  # ค่าประมาณ 1 เมตร
                self.log_message(f"📏 Estimated height (drone flying): {estimated_height:.3f}m")
                return estimated_height
            
            self.log_message("❌ Height measurement not available - no method worked")
            return None
                
        except Exception as e:
            self.log_message(f"❌ Height read error: {e}")
            return None
    
    def get_altitude(self):
        """วัดความสูงจากพื้น - alias สำหรับ get_height()"""
        return self.get_height()
    
    def is_safe_altitude(self, min_height=0.3):
        """ตรวจสอบว่าอยู่ในระดับความสูงที่ปลอดภัย - ตรงกับ drone_controller.is_safe_altitude()"""
        try:
            if hasattr(self.current_drone, 'is_safe_altitude'):
                safe = self.current_drone.is_safe_altitude(min_height)
                self.log_message(f"🛡️ Safe altitude check (min={min_height}m): {'✅ Safe' if safe else '⚠️ Too low'}")
                return safe
            else:
                # Fallback - ใช้ get_height แทน
                height = self.get_height()
                if height is not None:
                    safe = height >= min_height
                    self.log_message(f"🛡️ Safe altitude check (min={min_height}m): {'✅ Safe' if safe else '⚠️ Too low'}")
                    return safe
                else:
                    self.log_message("❌ Cannot check altitude safety")
                    return False
        except Exception as e:
            self.log_message(f"❌ Safe altitude check error: {e}")
            return False
    
    def read_proximity_sensor(self, sensor_name='bottom'):
        """อ่านข้อมูลจาก proximity sensor - ตรงกับ drone_controller.read_proximity_sensor()"""
        if hasattr(self.current_drone, 'read_proximity_sensor'):
            try:
                result = self.current_drone.read_proximity_sensor(sensor_name)
                if result:
                    self.log_message(f"📡 Proximity sensor {sensor_name}: {result}")
                else:
                    self.log_message(f"❌ No reading from proximity sensor {sensor_name}")
                return result
            except Exception as e:
                self.log_message(f"❌ Proximity sensor read error: {e}")
                return None
        else:
            # Fallback ใช้ read_distance
            return self.read_distance()
    
    def disable_proximity_sensors(self):
        """ปิดใช้งาน Proximity Sensors"""
        self.proximity_sensors_enabled = False
        self.log_message("📡 Proximity sensors disabled")
        return True
    
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
                    self.log_message(f"  📍 ID: {pad['id']}, Method: {pad.get('method', 'unknown')}, Confidence: {pad.get('confidence', 0):.2f}")
            
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
            'proximity_sensors_enabled': self.proximity_sensors_enabled,
            'auto_mission_running': self.auto_mission_running
        }
        
        # เพิ่มข้อมูล proximity sensors ถ้าเปิดใช้งาน
        if self.proximity_sensors_enabled:
            try:
                status['current_height'] = self.get_height()
                status['distance_reading'] = self.read_distance()
            except:
                pass
        
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
    
    # ==================== ADDITIONAL DRONE CONTROLLER FUNCTIONS ====================
    # เพิ่มฟังก์ชันที่สำคัญที่ควรตรงกับ drone_controller.py
    
    def get_battery(self):
        """ดูระดับแบตเตอรี่ - ตรงกับ drone_controller.get_battery()"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return -1
        
        try:
            if hasattr(self.current_drone, 'get_battery'):
                battery = self.current_drone.get_battery()
                self.log_message(f"🔋 Battery: {battery}%")
                return battery
            else:
                self.log_message("⚠️ Battery reading not available")
                return -1
        except Exception as e:
            self.log_message(f"❌ Battery read error: {e}")
            return -1
    
    def get_position(self):
        """ดึงตำแหน่งปัจจุบัน - ตรงกับ drone_controller.get_position()"""
        if not self.is_connected:
            return [0, 0, 0]
        
        try:
            if hasattr(self.current_drone, 'get_position'):
                return self.current_drone.get_position()
            else:
                return self.current_position
        except Exception as e:
            self.log_message(f"❌ Position read error: {e}")
            return [0, 0, 0]
    
    def get_orientation(self):
        """ดึงทิศทางปัจจุบัน - ตรงกับ drone_controller.get_orientation()"""
        if not self.is_connected:
            return [0, 0, 0, 0]
        
        try:
            if hasattr(self.current_drone, 'get_orientation'):
                return self.current_drone.get_orientation()
            else:
                self.log_message("⚠️ Orientation reading not available")
                return [0, 0, 0, 0]
        except Exception as e:
            self.log_message(f"❌ Orientation read error: {e}")
            return [0, 0, 0, 0]
    
    def take_bottom_picture(self):
        """ถ่ายรูปด้วยกล้องล่าง - ตรงกับ drone_controller.take_bottom_picture()"""
        if not self.is_connected:
            self.log_message("❌ Drone not connected")
            return None
        
        try:
            if hasattr(self.current_drone, 'take_bottom_picture'):
                result = self.current_drone.take_bottom_picture()
                if result:
                    self.log_message(f"✅ Bottom picture captured: {result}")
                else:
                    self.log_message("❌ Bottom picture capture failed")
                return result
            else:
                self.log_message("⚠️ Bottom camera not available")
                return None
        except Exception as e:
            self.log_message(f"❌ Bottom picture error: {e}")
            return None
    
    def move_to_position(self, x, y, z):
        """เคลื่อนที่ไปยังตำแหน่งเฉพาะ - ตรงกับ drone_controller.move_to_position()"""
        if not self.is_flying:
            self.log_message("❌ Drone not flying")
            return False
        
        try:
            self.log_message(f"🎯 Moving to position ({x}, {y}, {z})...")
            if hasattr(self.current_drone, 'move_to_position'):
                result = self.current_drone.move_to_position(x, y, z)
                if result:
                    self.log_message("✅ Position reached")
                    self._update_position()
                else:
                    self.log_message("❌ Failed to reach position")
                return result
            else:
                self.log_message("⚠️ Position movement not available")
                return False
        except Exception as e:
            self.log_message(f"❌ Move to position error: {e}")
            return False
    
    def smart_mission_pad_scan(self, image_path=None, use_multiple_methods=True):
        """ตรวจจับ Mission Pad แบบขั้นสูง - ตรงกับ drone_controller.smart_mission_pad_scan()"""
        if hasattr(self.current_drone, 'smart_mission_pad_scan'):
            try:
                result = self.current_drone.smart_mission_pad_scan(image_path, use_multiple_methods)
                if result:
                    self.log_message(f"✅ Smart mission pad scan found: {result}")
                else:
                    self.log_message("❌ No mission pads found")
                return result
            except Exception as e:
                self.log_message(f"❌ Smart mission pad scan error: {e}")
                return None
        else:
            # Fallback ใช้ฟังก์ชันของเรา
            return self.scan_mission_pad("all")
    
    def scan_mission_pad_enhanced(self, attempts=3, delay=1.0):
        """ตรวจจับ Mission Pad แบบลองหลายครั้ง - ตรงกับ drone_controller.scan_mission_pad_enhanced()"""
        if hasattr(self.current_drone, 'scan_mission_pad_enhanced'):
            try:
                result = self.current_drone.scan_mission_pad_enhanced(attempts, delay)
                if result:
                    self.log_message(f"✅ Enhanced mission pad scan found: {result}")
                else:
                    self.log_message("❌ No mission pads found after enhanced scan")
                return result
            except Exception as e:
                self.log_message(f"❌ Enhanced mission pad scan error: {e}")
                return None
        else:
            # Fallback - ลองหลายครั้ง
            for i in range(attempts):
                result = self.scan_mission_pad("auto")
                if result:
                    return result
                if i < attempts - 1:
                    time.sleep(delay)
            return None
    
    def wait(self, seconds):
        """รอเวลา - ตรงกับ drone_controller.wait()"""
        self.log_message(f"⏰ Waiting {seconds} seconds...")
        time.sleep(seconds)
        self.log_message("✅ Wait completed")
    
    def is_close_to_ground(self, threshold=0.3):
        """ตรวจสอบว่าใกล้พื้นหรือไม่ - ตรงกับ drone_controller.is_close_to_ground()
        
        Args:
            threshold: ระยะห่างที่ถือว่าใกล้พื้น (เมตร)
            
        Returns:
            bool: True ถ้าใกล้พื้น
        """
        height = self.get_height()
        if height is not None:
            is_close = height <= threshold
            self.log_message(f"🔍 Close to ground check: {height:.2f}m <= {threshold}m = {is_close}")
            return is_close
        return False
    
    def wait_until_height(self, target_height, timeout=10):
        """รอจนกว่าจะถึงความสูงที่ต้องการ - ตรงกับ drone_controller.wait_until_height()
        
        Args:
            target_height: ความสูงเป้าหมาย (เมตร)
            timeout: เวลาสูงสุดที่จะรอ (วินาที)
            
        Returns:
            bool: True ถ้าถึงความสูงที่ต้องการ
        """
        import time
        start_time = time.time()
        
        self.log_message(f"⏳ Waiting for height {target_height:.2f}m (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            height = self.get_height()
            if height is not None and abs(height - target_height) < 0.1:
                self.log_message(f"✅ ถึงความสูง {target_height:.2f} เมตรแล้ว")
                return True
            
            time.sleep(0.1)
        
        self.log_message(f"⏰ หมดเวลารอ ({timeout} วินาที)")
        return False
    
    def monitor_height(self, duration=5):
        """ตรวจสอบความสูงแบบต่อเนื่อง - ตรงกับ drone_controller.monitor_height()
        
        Args:
            duration: ระยะเวลาที่จะตรวจสอบ (วินาที)
        """
        import time
        start_time = time.time()
        
        self.log_message(f"📡 ตรวจสอบความสูงเป็นเวลา {duration} วินาที...")
        
        while time.time() - start_time < duration:
            height = self.get_height()
            elapsed = time.time() - start_time
            if height is not None:
                self.log_message(f"  ⏱️ {elapsed:.1f}s: {height:.2f}m")
            else:
                self.log_message(f"  ⏱️ {elapsed:.1f}s: ไม่มีข้อมูล")
            
            time.sleep(0.5)
        
        self.log_message("✅ เสร็จสิ้นการตรวจสอบความสูง")
    


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
    
    # Main content frame - split into left and right panels
    main_content_frame = tk.Frame(drone_tab)
    main_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Left panel - Python Code Editor
    code_frame = tk.LabelFrame(main_content_frame, text="🐍 Python Drone Control", font=('Arial', 10, 'bold'))
    code_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    # Right panel - Terminal Output
    log_frame = tk.LabelFrame(main_content_frame, text="📋 Terminal Output / Logs", font=('Arial', 10, 'bold'))
    log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
    
    # Code input area
    code_input_frame = tk.Frame(code_frame)
    code_input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # Label with copy-paste instructions
    help_label = tk.Label(code_input_frame, 
                         text="💡 Copy-Paste Support: Ctrl+C/V/X/A/Z/Y | Right-click for menu | Tab for indent", 
                         font=('Arial', 8), fg='#7f8c8d')
    help_label.pack(anchor=tk.W, padx=5)
    
    tk.Label(code_input_frame, text="Enter Python code to control the drone:", 
             font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=5)
    
    # Text widget with scrollbar and enhanced copy-paste support
    text_frame = tk.Frame(code_input_frame)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    code_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10), 
                       bg='#2c3e50', fg='#ecf0f1', insertbackground='white',
                       selectbackground='#3498db', relief=tk.FLAT, bd=5,
                       undo=True, maxundo=20)  # Enable undo functionality
    
    scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=code_text.yview)
    code_text.configure(yscrollcommand=scrollbar.set)
    
    # Enhanced keyboard shortcuts for better copy-paste experience
    def on_key_press(event):
        """Handle keyboard shortcuts"""
        if event.state & 0x4:  # Ctrl key pressed
            if event.keysym == 'a':  # Ctrl+A - Select All
                code_text.tag_add(tk.SEL, "1.0", tk.END)
                return "break"
            elif event.keysym == 'c':  # Ctrl+C - Copy (default behavior)
                return None
            elif event.keysym == 'v':  # Ctrl+V - Paste (default behavior)
                return None
            elif event.keysym == 'x':  # Ctrl+X - Cut (default behavior)
                return None
            elif event.keysym == 'z':  # Ctrl+Z - Undo
                try:
                    code_text.edit_undo()
                except tk.TclError:
                    pass
                return "break"
            elif event.keysym == 'y':  # Ctrl+Y - Redo
                try:
                    code_text.edit_redo()
                except tk.TclError:
                    pass
                return "break"
        elif event.keysym == 'Tab':  # Tab - Insert 4 spaces for proper Python indentation
            code_text.insert(tk.INSERT, "    ")  # 4 spaces
            return "break"
        elif event.keysym == 'Return':  # Enter - Auto-indent for Python
            # Get current line content to determine indentation
            current_line = code_text.get("insert linestart", "insert")
            indent = ""
            for char in current_line:
                if char in [' ', '\t']:
                    indent += char
                else:
                    break
            
            # Add extra indent if line ends with ':'
            if current_line.rstrip().endswith(':'):
                indent += "    "
            
            code_text.insert(tk.INSERT, f"\n{indent}")
            return "break"
    
    code_text.bind('<Key>', on_key_press)
    
    # Right-click context menu for copy-paste operations
    def show_context_menu(event):
        """Show context menu on right-click"""
        context_menu = tk.Menu(code_text, tearoff=0)
        
        # Copy-paste operations
        context_menu.add_command(label="📋 Cut", command=lambda: code_text.event_generate('<<Cut>>'))
        context_menu.add_command(label="📄 Copy", command=lambda: code_text.event_generate('<<Copy>>'))
        context_menu.add_command(label="📌 Paste", command=lambda: code_text.event_generate('<<Paste>>'))
        context_menu.add_separator()
        context_menu.add_command(label="🔄 Select All", command=lambda: code_text.tag_add(tk.SEL, "1.0", tk.END))
        context_menu.add_separator()
        context_menu.add_command(label="↶ Undo", command=lambda: code_text.edit_undo())
        context_menu.add_command(label="↷ Redo", command=lambda: code_text.edit_redo())
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ Clear All", command=lambda: code_text.delete(1.0, tk.END))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    code_text.bind("<Button-3>", show_context_menu)  # Right-click
    
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
    
    tk.Button(quick_frame, text="🔶 Square Flight", command=quick_square,
             bg='#8e44ad', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
    
    # === Terminal Output Section (Right Panel) ===
    
    # Log text area with scrollbar
    log_text_frame = tk.Frame(log_frame)
    log_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Create scrolled text widget for logs
    log_text = scrolledtext.ScrolledText(
        log_text_frame,
        wrap=tk.WORD,
        font=('Consolas', 9),
        bg='#1e1e1e',
        fg='#00ff00',  # Green terminal-like text
        insertbackground='#00ff00',
        selectbackground='#333333',
        relief=tk.FLAT,
        bd=5,
        height=20,  # Increased height for side panel
        state=tk.DISABLED  # Read-only by default
    )
    log_text.pack(fill=tk.BOTH, expand=True)
    
    # Store reference to log_text in drone_connector for callback
    drone_connector.log_text_widget = log_text
    
    # Log control buttons
    log_button_frame = tk.Frame(log_frame)
    log_button_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def clear_logs():
        """Clear all logs"""
        log_text.config(state=tk.NORMAL)
        log_text.delete(1.0, tk.END)
        log_text.config(state=tk.DISABLED)
        drone_connector.log_message("🗑️ Log cleared")
    
    def save_logs():
        """Save logs to file"""
        try:
            from tkinter import filedialog
            content = log_text.get(1.0, tk.END)
            if content.strip():
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".log",
                    filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
                    initialfilename=f"drone_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                )
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    drone_connector.log_message(f"💾 Logs saved to: {file_path}")
            else:
                drone_connector.log_message("❌ No logs to save")
        except Exception as e:
            drone_connector.log_message(f"❌ Save logs error: {e}")
    
    def toggle_autoscroll():
        """Toggle auto-scroll to bottom"""
        if hasattr(drone_connector, 'autoscroll_enabled'):
            drone_connector.autoscroll_enabled = not drone_connector.autoscroll_enabled
        else:
            drone_connector.autoscroll_enabled = True
        
        status = "enabled" if drone_connector.autoscroll_enabled else "disabled"
        drone_connector.log_message(f"🔄 Auto-scroll {status}")
    
    # Initialize autoscroll as enabled
    drone_connector.autoscroll_enabled = True
    
    # Log control buttons with smaller size for side panel
    tk.Button(log_button_frame, text="🗑️ Clear", command=clear_logs,
             bg='#e74c3c', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
    
    tk.Button(log_button_frame, text="💾 Save", command=save_logs,
             bg='#27ae60', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
    
    tk.Button(log_button_frame, text="🔄 Auto", command=toggle_autoscroll,
             bg='#3498db', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
    
    # Add timestamp to show when log area was created
    initial_message = f"[{datetime.now().strftime('%H:%M:%S')}] 📋 Terminal output initialized - Ready to display logs..."
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, initial_message + "\n")
    log_text.config(state=tk.DISABLED)
    log_text.see(tk.END)
    
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