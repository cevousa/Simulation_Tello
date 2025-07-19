#!/usr/bin/env python3
"""
Drone Commands Wrapper - รวมและจัดการคำสั่งโดรนทั้งหมด
ไฟล์นี้เป็นตัวกลางที่นำเข้าและจัดการคำสั่งจากไฟล์ drone_controller.py
ทำให้ GUI สามารถใช้คำสั่งโดรนได้โดยไม่ต้องกังวลเรื่องการเปลี่ยนชื่อฟังก์ชัน
"""

import sys
import os
import time

# เพิ่ม path สำหรับ import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from drone_controller import NaturalDroneController, DroneTello, QRCodeScanner, DroneCamera
    import drone_controller
except ImportError as e:
    print(f"❌ Error importing drone controller: {e}")
    NaturalDroneController = None
    DroneTello = None
    QRCodeScanner = None
    DroneCamera = None

class DroneCommandsWrapper:
    """คลาสสำหรับ wrap คำสั่งโดรนทั้งหมด"""
    
    def __init__(self):
        # ตัวแปรสำหรับโดรน
        self.sim_drone = None          # Simulation drone controller
        self.real_drone = None         # Real drone controller
        self.current_drone = None      # ตัวที่ใช้งานอยู่
        self.drone_mode = "simulation" # "simulation" หรือ "real"
        
        # ตัวแปรสถานะ
        self._is_connected = False
        self._is_flying = False
        self._camera_active = False
        self.current_position = [0.0, 0.0, 0.0]
        
        # ตัวแปรสำหรับ QR
        self.qr_scanner = None
        
        print("✅ Drone Commands Wrapper initialized")
    
    # ==================== CONNECTION COMMANDS ====================
    
    def connect_simulation(self):
        """เชื่อมต่อกับโดรนใน Simulation"""
        try:
            if NaturalDroneController is None:
                print("❌ NaturalDroneController not available")
                return False
                
            if self.sim_drone is None:
                self.sim_drone = NaturalDroneController(use_simulation=True)
            
            if self.sim_drone.use_simulation:
                self.current_drone = self.sim_drone
                self.drone_mode = "simulation"
                self._is_connected = True
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Simulation connection error: {e}")
            return False
    
    def connect_real_drone(self):
        """เชื่อมต่อกับโดรนจริง"""
        try:
            if DroneTello is None:
                print("❌ DroneTello not available")
                return False
                
            if self.real_drone is None:
                self.real_drone = DroneTello(show_cam=False, enable_mission_pad=False)
            
            self.current_drone = self.real_drone
            self.drone_mode = "real"
            self._is_connected = True
            return True
            
        except Exception as e:
            print(f"❌ Real drone connection error: {e}")
            return False
    
    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        try:
            # ลงจอดถ้ากำลังบินอยู่
            if self._is_flying:
                self.land()
            
            # หยุดกล้องถ้าเปิดอยู่
            if self._camera_active:
                self.stop_camera()
            
            # ปิดการเชื่อมต่อ
            if self.current_drone:
                if hasattr(self.current_drone, 'disconnect'):
                    self.current_drone.disconnect()
                elif hasattr(self.current_drone, 'end'):
                    self.current_drone.end()
                elif hasattr(self.current_drone, 'cleanup'):
                    self.current_drone.cleanup()
            
            self.current_drone = None
            self._is_connected = False
            self._is_flying = False
            return True
            
        except Exception as e:
            print(f"❌ Disconnect error: {e}")
            return False
    
    # ==================== UTILITY METHODS ====================
    
    def _call_drone_function(self, function_name, *args, **kwargs):
        """เรียกใช้ฟังก์ชันจาก drone controller โดยอัตโนมัติ"""
        if not self.current_drone:
            return None
        
        try:
            # ลองหาฟังก์ชันใน current_drone object
            if hasattr(self.current_drone, function_name):
                func = getattr(self.current_drone, function_name)
                return func(*args, **kwargs)
            else:
                print(f"❌ Function '{function_name}' not found in drone controller")
                return None
        except Exception as e:
            print(f"❌ Error calling function '{function_name}': {e}")
            return None
    
    def _get_alternative_function_names(self, command_name):
        """หาชื่อฟังก์ชันทางเลือกสำหรับคำสั่งต่างๆ"""
        alternatives = {
            'takeoff': ['takeoff', 'take_off', 'startTakeoff'],
            'land': ['land', 'landing', 'startLanding'],
            'hover': ['hover', 'stay', 'wait'],
            'move_forward': ['move_forward', 'moveForward', 'forward'],
            'move_backward': ['move_backward', 'move_back', 'moveBackward', 'backward'],
            'move_left': ['move_left', 'moveLeft', 'left'],
            'move_right': ['move_right', 'moveRight', 'right'],
            'move_up': ['move_up', 'moveUp', 'up'],
            'move_down': ['move_down', 'moveDown', 'down'],
            'rotate_clockwise': ['rotate_clockwise', 'rotateClockwise', 'rotate_cw', 'cw'],
            'rotate_counterclockwise': ['rotate_counterclockwise', 'rotate_counter_clockwise', 'rotateCounterClockwise', 'rotate_ccw', 'ccw']
        }
        
        return alternatives.get(command_name.lower(), [command_name.lower()])
    
    def _try_function_with_alternatives(self, primary_name, *args, **kwargs):
        """ลองเรียกใช้ฟังก์ชันหลัก หากไม่ได้ผลให้ลองชื่อทางเลือก"""
        # ลองเรียกฟังก์ชันหลัก
        result = self._call_drone_function(primary_name, *args, **kwargs)
        if result is not None:
            return result
        
        # ลองเรียกฟังก์ชันทางเลือก
        alternatives = self._get_alternative_function_names(primary_name)
        for alt_name in alternatives[1:]:  # ข้าม index 0 เพราะเป็นชื่อหลัก
            result = self._call_drone_function(alt_name, *args, **kwargs)
            if result is not None:
                return result
        
        return None
    
    # ==================== FLIGHT COMMANDS ====================
    
    def takeoff(self):
        """ขึ้นบิน"""
        if not self._is_connected:
            return False
        
        try:
            result = self._try_function_with_alternatives("takeoff")
            if result is not None:
                self._is_flying = True
                self._update_position()
                return True
            return False
            
        except Exception as e:
            print(f"❌ Takeoff error: {e}")
            return False
    
    def land(self):
        """ลงจอด"""
        if not self._is_connected:
            return False
        
        try:
            result = self._try_function_with_alternatives("land")
            if result is not None:
                self._is_flying = False
                self.current_position = [0.0, 0.0, 0.0]
                return True
            return False
            
        except Exception as e:
            print(f"❌ Land error: {e}")
            return False
    
    def hover(self, duration=3):
        """โฮเวอร์ (อยู่กับที่)"""
        if not self._is_flying:
            return False
        
        try:
            if self.drone_mode == "real":
                # สำหรับ real drone ใช้ sleep
                time.sleep(duration)
                return True
            else:
                # สำหรับ simulation ลองเรียกฟังก์ชัน hover
                result = self._try_function_with_alternatives("hover", duration)
                return result is not None
            
        except Exception as e:
            print(f"❌ Hover error: {e}")
            return False
    
    # ==================== MOVEMENT COMMANDS ====================
    
    def move_forward(self, distance=0.5):
        """เคลื่อนที่ไปข้างหน้า"""
        return self._execute_movement("move_forward", distance)
    
    def move_backward(self, distance=0.5):
        """เคลื่อนที่ไปข้างหลัง"""
        return self._execute_movement("move_backward", distance)
    
    def move_back(self, distance=0.5):
        """เคลื่อนที่ไปข้างหลัง (ชื่อทางเลือก)"""
        return self._execute_movement("move_back", distance)
    
    def move_left(self, distance=0.5):
        """เคลื่อนที่ไปทางซ้าย"""
        return self._execute_movement("move_left", distance)
    
    def move_right(self, distance=0.5):
        """เคลื่อนที่ไปทางขวา"""
        return self._execute_movement("move_right", distance)
    
    def move_up(self, distance=0.5):
        """เคลื่อนที่ขึ้น"""
        return self._execute_movement("move_up", distance)
    
    def move_down(self, distance=0.5):
        """เคลื่อนที่ลง"""
        return self._execute_movement("move_down", distance)
    
    def _execute_movement(self, movement_func, distance):
        """ดำเนินการเคลื่อนที่"""
        if not self._is_flying:
            return False
        
        try:
            # สำหรับ real drone แปลงเป็น cm
            if self.drone_mode == "real":
                distance_param = int(distance * 100)
            else:
                distance_param = distance
            
            result = self._try_function_with_alternatives(movement_func, distance_param)
            if result is not None:
                self._update_position()
                return True
            return False
            
        except Exception as e:
            print(f"❌ Movement error: {e}")
            return False
    
    # ==================== ROTATION COMMANDS ====================
    
    def rotate_clockwise(self, angle=90):
        """หมุนตามเข็มนาฬิกา"""
        return self._execute_rotation("rotate_clockwise", angle)
    
    def rotate_counterclockwise(self, angle=90):
        """หมุนทวนเข็มนาฬิกา"""
        return self._execute_rotation("rotate_counterclockwise", angle)
    
    def rotate_counter_clockwise(self, angle=90):
        """หมุนทวนเข็มนาฬิกา (ชื่อทางเลือก)"""
        return self._execute_rotation("rotate_counter_clockwise", angle)
    
    def _execute_rotation(self, rotation_func, angle):
        """ดำเนินการหมุน"""
        if not self._is_flying:
            return False
        
        try:
            # สำหรับ real drone แปลงเป็น int
            if self.drone_mode == "real":
                angle_param = int(angle)
            else:
                angle_param = angle
            
            result = self._try_function_with_alternatives(rotation_func, angle_param)
            return result is not None
            
        except Exception as e:
            print(f"❌ Rotation error: {e}")
            return False
    
    # ==================== CAMERA COMMANDS ====================
    
    def start_camera(self):
        """เปิดกล้อง"""
        try:
            if self.drone_mode == "simulation":
                # สำหรับ simulation ใช้ DroneCamera
                if not hasattr(self.current_drone, 'camera') and DroneCamera:
                    self.current_drone.camera = DroneCamera(self.current_drone.sim)
                self._camera_active = True
            else:
                # สำหรับ real drone
                result = self._try_function_with_alternatives("streamon")
                if result is None:
                    result = self._try_function_with_alternatives("start_camera_display")
                self._camera_active = True
            
            return True
            
        except Exception as e:
            print(f"❌ Start camera error: {e}")
            return False
    
    def stop_camera(self):
        """ปิดกล้อง"""
        try:
            if self.drone_mode == "real":
                self._try_function_with_alternatives("streamoff")
            
            self._camera_active = False
            return True
            
        except Exception as e:
            print(f"❌ Stop camera error: {e}")
            return False
    
    def capture_image(self):
        """ถ่ายภาพ"""
        if not self._camera_active:
            return None
        
        try:
            if self.drone_mode == "simulation":
                if hasattr(self.current_drone, 'camera'):
                    return self.current_drone.camera.simcapture()
            else:
                # สำหรับ real drone
                result = self._try_function_with_alternatives("get_frame_read")
                if result and hasattr(result, 'frame'):
                    import cv2
                    frame = result.frame
                    timestamp = int(time.time())
                    filename = f"captured_image_{timestamp}.jpg"
                    filepath = os.path.join("captured_images", filename)
                    os.makedirs("captured_images", exist_ok=True)
                    cv2.imwrite(filepath, frame)
                    return filepath
            
            return None
            
        except Exception as e:
            print(f"❌ Capture image error: {e}")
            return None
    
    def capture_bottom_image(self):
        """ถ่ายภาพจากกล้องล่าง (สำหรับ simulation)"""
        if not self._camera_active or self.drone_mode != "simulation":
            return None
        
        try:
            if hasattr(self.current_drone, 'camera'):
                return self.current_drone.camera.simcapturebottom()
            return None
            
        except Exception as e:
            print(f"❌ Capture bottom image error: {e}")
            return None
    
    # ==================== QR CODE COMMANDS ====================
    
    def scan_qr_code(self, image_path):
        """แสกน QR Code จากไฟล์ภาพ"""
        try:
            if self.qr_scanner is None and QRCodeScanner:
                self.qr_scanner = QRCodeScanner()
            
            if self.qr_scanner:
                return self.qr_scanner.scan_qr_code(image_path)
            return None
            
        except Exception as e:
            print(f"❌ QR scan error: {e}")
            return None
    
    # ==================== STATUS COMMANDS ====================
    
    def get_battery(self):
        """อ่านแบตเตอรี่"""
        try:
            if self.drone_mode == "real":
                result = self._try_function_with_alternatives("get_battery")
                return result if result is not None else 0
            return 100  # สำหรับ simulation
            
        except Exception as e:
            print(f"❌ Get battery error: {e}")
            return 0
    
    def get_position(self):
        """อ่านตำแหน่งปัจจุบัน"""
        return self.current_position.copy()
    
    def _update_position(self):
        """อัพเดทตำแหน่งปัจจุบัน"""
        try:
            if self.drone_mode == "simulation":
                result = self._try_function_with_alternatives("get_position")
                if result:
                    self.current_position = result
            
        except Exception as e:
            print(f"❌ Update position error: {e}")
    
    # ==================== STATUS PROPERTIES ====================
    
    def is_drone_connected(self):
        """ตรวจสอบการเชื่อมต่อ"""
        return self._is_connected
    
    def is_drone_flying(self):
        """ตรวจสอบสถานะการบิน"""
        return self._is_flying
    
    def is_camera_active(self):
        """ตรวจสอบสถานะกล้อง"""
        return self._camera_active
    
    def get_drone_mode(self):
        """อ่านโหมดโดรน"""
        return self.drone_mode

# สร้าง instance เดียวสำหรับใช้งาน
drone_commands = DroneCommandsWrapper()
