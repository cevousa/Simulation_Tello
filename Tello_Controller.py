import time
import numpy as np
import cv2
import os
import math
from datetime import datetime
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

class TelloSimulator:
    def __init__(self):
        
        # เชื่อมต่อกับ CoppeliaSim
        self.client = RemoteAPIClient()
        self.sim = self.client.getObject('sim')
        self.camera_handle = None
        
        # รับ handle ของโดรน - ลองหลายชื่อที่เป็นไปได้
        try:
            # ลองชื่อต่างๆ ที่ CoppeliaSim อาจใช้
            possible_names = ['/Quadcopter', '/Quadricopter', '/drone', '/Drone', 'Quadcopter', 'Quadricopter']
            self.drone_handle = None
            
            for name in possible_names:
                try:
                    self.drone_handle = self.sim.getObject(name)
                    print(f"Found drone with name: {name}")
                    break
                except:
                    continue
                    
            if self.drone_handle is None:
                # ถ้ายังไม่เจอ ให้แสดง objects ที่มีอยู่
                print("Could not find drone. Trying to list available objects...")
                try:
                    # ลองค้นหา object ที่อาจเป็นโดรน
                    all_objects = self.sim.getObjectsInTree(self.sim.handle_scene)
                    print(f"Available objects: {len(all_objects)} objects found")
                    
                    # ลองใช้ object แรกที่เจอ (อาจเป็นโดรน)
                    if len(all_objects) > 0:
                        for obj in all_objects:
                            try:
                                obj_name = self.sim.getObjectAlias(obj)
                                if any(keyword in obj_name.lower() for keyword in ['quad', 'drone', 'copter']):
                                    self.drone_handle = obj
                                    print(f"Found potential drone: {obj_name}")
                                    break
                            except:
                                continue
                except Exception as e:
                    print(f"Error listing objects: {e}")
                    
        except Exception as e:
            print(f"Error finding drone: {e}")
            print("Please make sure the drone model is loaded in CoppeliaSim")
            
        # รับ handle ของใบพัด - ลองหลายรูปแบบ
        self.propellers = []
        
        # ลองหาใบพัดด้วยชื่อต่างๆ
        if self.drone_handle:
            propeller_patterns = [
                lambda i: f'/Quadcopter/propeller[{i-1}]',
                lambda i: f'/Quadcopter/respondable[{i-1}]/joint',
                lambda i: f'/Quadcopter/propeller[{i-1}]/respondable/joint',
                lambda i: f'/Quadcopter/Propeller{i}',
                lambda i: f'/Quadricopter/Propeller{i}',
                lambda i: f'/Quadcopter/PropellerRespondable{i}',
                lambda i: f'/Quadricopter/PropellerRespondable{i}',
                lambda i: f'Propeller{i}',
                lambda i: f'PropellerRespondable{i}'
            ]
            
            for pattern in propeller_patterns:
                self.propellers = []
                try:
                    for i in range(1, 5):
                        prop_name = pattern(i)
                        prop = self.sim.getObject(prop_name)
                        self.propellers.append(prop)
                        
                    if len(self.propellers) == 4:
                        print(f"Found propellers with pattern: {pattern(1)}")
                        break
                except:
                    continue
                    
            if len(self.propellers) != 4:
                print(f"Warning: Could not find all 4 propellers. Found {len(self.propellers)}")
        
        # สร้างกล้องและ sensors
        self.setup_camera_system()
        
        # ตัวแปรสถานะ
        self.position = [0, 0, 0]
        self.orientation = [0, 0, 0]
        self.is_flying = False
        self.simulation_running = False
        
        # ตัวแปรสำหรับ Mission Pad
        self.mission_pads = {}
        self.current_detected_pad = None
        self.photo_count = 0
        
        # สร้างโฟลเดอร์สำหรับเก็บรูป
        self.photo_dir = "tello_photos"
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)
        
    def start_simulation(self):
        """เริ่มการจำลอง"""
        try:
            self.sim.startSimulation()
            self.simulation_running = True
            print("✓ Simulation started")
            return True
        except Exception as e:
            print(f"❌ Failed to start simulation: {e}")
            return False
    
    def stop_simulation(self):
        """หยุดการจำลอง"""
        try:
            self.sim.stopSimulation()
            self.simulation_running = False
            print("✓ Simulation stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to stop simulation: {e}")
            return False
    
    def takeoff(self, height=1.0):
        """บินขึ้น"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
            
        try:
            print(f"🚁 Taking off to {height}m...")
            
            # เริ่มหมุนใบพัด
            self.rotate_propellers(speed=30)
            
            # รับตำแหน่งปัจจุบัน
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            target_pos = [current_pos[0], current_pos[1], height]
            
            # บินขึ้นแบบค่อยเป็นค่อยไป
            steps = 50
            for i in range(steps):
                new_height = current_pos[2] + (height - current_pos[2]) * (i + 1) / steps
                new_pos = [current_pos[0], current_pos[1], new_height]
                
                self.sim.setObjectPosition(self.drone_handle, -1, new_pos)
                time.sleep(0.05)
            
            self.is_flying = True
            self.position = target_pos
            print(f"✓ Takeoff complete! Altitude: {height}m")
            return True
            
        except Exception as e:
            print(f"❌ Takeoff failed: {e}")
            return False
    
    def land(self):
        """ลงจอด"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
            
        try:
            print("🛬 Landing...")
            
            # รับตำแหน่งปัจจุบัน
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            
            # ลงจอดแบบค่อยเป็นค่อยไป
            steps = 30
            for i in range(steps):
                new_height = current_pos[2] * (1 - (i + 1) / steps) + 0.1  # ลงไปที่ระดับ 0.1m
                new_pos = [current_pos[0], current_pos[1], new_height]
                
                self.sim.setObjectPosition(self.drone_handle, -1, new_pos)
                time.sleep(0.05)
            
            # หยุดใบพัด
            self.rotate_propellers(speed=0)
            
            self.is_flying = False
            print("✓ Landing complete!")
            return True
            
        except Exception as e:
            print(f"❌ Landing failed: {e}")
            return False
    
    def hover(self, duration=3):
        """บินลอยนิ่งในที่"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
            
        try:
            print(f"🚁 Hovering for {duration} seconds...")
            
            # รักษาตำแหน่งและหมุนใบพัด
            start_time = time.time()
            while time.time() - start_time < duration:
                self.rotate_propellers(speed=20)
                time.sleep(0.1)
            
            print("✓ Hover complete!")
            return True
            
        except Exception as e:
            print(f"❌ Hover failed: {e}")
            return False
    
    def move_to(self, x, y, z, speed=1.0):
        """บินไปยังตำแหน่งที่กำหนด"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
            
        try:
            print(f"🚁 Moving to position ({x}, {y}, {z})...")
            
            # รับตำแหน่งปัจจุบัน
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            target_pos = [x, y, z]
            
            # คำนวณระยะทาง
            distance = ((x - current_pos[0])**2 + (y - current_pos[1])**2 + (z - current_pos[2])**2)**0.5
            steps = max(20, int(distance * 20))  # ปรับจำนวน steps ตามระยะทาง
            
            # บินไปยังตำแหน่งเป้าหมาย
            for i in range(steps):
                progress = (i + 1) / steps
                new_pos = [
                    current_pos[0] + (x - current_pos[0]) * progress,
                    current_pos[1] + (y - current_pos[1]) * progress,
                    current_pos[2] + (z - current_pos[2]) * progress
                ]
                
                self.sim.setObjectPosition(self.drone_handle, -1, new_pos)
                self.rotate_propellers(speed=20)
                time.sleep(0.05 / speed)
            
            self.position = target_pos
            print(f"✓ Moved to ({x}, {y}, {z})")
            return True
            
        except Exception as e:
            print(f"❌ Move failed: {e}")
            return False
    
    def fly_pattern_up_down(self, cycles=3, height_change=0.5):
        """บินขึ้นลงแบบซ้ำๆ เพื่อทดสอบ"""
        if not self.is_flying:
            print("❌ Drone is not flying! Call takeoff() first.")
            return False
            
        try:
            print(f"🚁 Flying up-down pattern for {cycles} cycles...")
            
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            base_height = current_pos[2]
            
            for cycle in range(cycles):
                print(f"  Cycle {cycle + 1}/{cycles}")
                
                # บินขึ้น
                self.move_to(current_pos[0], current_pos[1], base_height + height_change)
                time.sleep(0.5)
                
                # บินลง
                self.move_to(current_pos[0], current_pos[1], base_height)
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
            
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
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
                self.move_to(corner[0], corner[1], corner[2])
                time.sleep(1)
            
            print("✓ Square pattern complete!")
            return True
            
        except Exception as e:
            print(f"❌ Square pattern failed: {e}")
            return False
    
    def test_connection(self):
        """ทดสอบการเชื่อมต่อกับโดรน"""
        print("🔍 Testing drone connection...")
        
        if not self.drone_handle:
            print("❌ Drone handle not found!")
            return False
        
        try:
            # ทดสอบการอ่านตำแหน่ง
            pos = self.sim.getObjectPosition(self.drone_handle, -1)
            print(f"✓ Drone position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            
            # ทดสอบการหมุนใบพัด
            print("✓ Testing propeller rotation...")
            self.rotate_propellers(speed=10)
            time.sleep(2)
            self.rotate_propellers(speed=0)
            
            # ทดสอบกล้อง
            if self.camera_handle:
                img = self.get_camera_image()
                if img is not None:
                    print(f"✓ Camera working! Image size: {img.shape}")
                else:
                    print("⚠️ Camera found but no image received")
            else:
                print("⚠️ Camera not available")
            
            print("✅ Connection test complete!")
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def move_forward(self, distance=1.0, speed=1.0):
        """เดินหน้า - เคลื่อนที่ไปข้างหน้า"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"➡️ Moving forward {distance}m...")
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            current_ori = self.sim.getObjectOrientation(self.drone_handle, -1)
            
            # คำนวณตำแหน่งใหม่ตามทิศทางที่โดรนหัน
            import math
            yaw = current_ori[2]  # มุม Z (yaw)
            new_x = current_pos[0] + distance * math.cos(yaw)
            new_y = current_pos[1] + distance * math.sin(yaw)
            new_z = current_pos[2]
            
            return self.move_to(new_x, new_y, new_z, speed)
            
        except Exception as e:
            print(f"❌ Move forward failed: {e}")
            return False
    
    def move_backward(self, distance=1.0, speed=1.0):
        """ถอยหลัง - เคลื่อนที่ไปข้างหลัง"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"⬅️ Moving backward {distance}m...")
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            current_ori = self.sim.getObjectOrientation(self.drone_handle, -1)
            
            # คำนวณตำแหน่งใหม่ตามทิศทางตรงข้ามที่โดรนหัน
            import math
            yaw = current_ori[2]  # มุม Z (yaw)
            new_x = current_pos[0] - distance * math.cos(yaw)
            new_y = current_pos[1] - distance * math.sin(yaw)
            new_z = current_pos[2]
            
            return self.move_to(new_x, new_y, new_z, speed)
            
        except Exception as e:
            print(f"❌ Move backward failed: {e}")
            return False
    
    def move_left(self, distance=1.0, speed=1.0):
        """ไปซ้าย - เคลื่อนที่ไปทางซ้าย"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"⬅️ Moving left {distance}m...")
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            current_ori = self.sim.getObjectOrientation(self.drone_handle, -1)
            
            # คำนวณตำแหน่งใหม่ไปทางซ้าย (หมุน 90 องศา)
            import math
            yaw = current_ori[2]  # มุม Z (yaw)
            new_x = current_pos[0] + distance * math.cos(yaw + math.pi/2)
            new_y = current_pos[1] + distance * math.sin(yaw + math.pi/2)
            new_z = current_pos[2]
            
            return self.move_to(new_x, new_y, new_z, speed)
            
        except Exception as e:
            print(f"❌ Move left failed: {e}")
            return False
    
    def move_right(self, distance=1.0, speed=1.0):
        """ไปขวา - เคลื่อนที่ไปทางขวา"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"➡️ Moving right {distance}m...")
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            current_ori = self.sim.getObjectOrientation(self.drone_handle, -1)
            
            # คำนวณตำแหน่งใหม่ไปทางขวา (หมุน -90 องศา)
            import math
            yaw = current_ori[2]  # มุม Z (yaw)
            new_x = current_pos[0] + distance * math.cos(yaw - math.pi/2)
            new_y = current_pos[1] + distance * math.sin(yaw - math.pi/2)
            new_z = current_pos[2]
            
            return self.move_to(new_x, new_y, new_z, speed)
            
        except Exception as e:
            print(f"❌ Move right failed: {e}")
            return False
    
    def move_up(self, distance=0.5, speed=1.0):
        """บินขึ้น - เคลื่อนที่ขึ้น"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"⬆️ Moving up {distance}m...")
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            new_x = current_pos[0]
            new_y = current_pos[1]
            new_z = current_pos[2] + distance
            
            return self.move_to(new_x, new_y, new_z, speed)
            
        except Exception as e:
            print(f"❌ Move up failed: {e}")
            return False
    
    def move_down(self, distance=0.5, speed=1.0):
        """บินลง - เคลื่อนที่ลง"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"⬇️ Moving down {distance}m...")
            current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
            new_x = current_pos[0]
            new_y = current_pos[1]
            new_z = max(0.1, current_pos[2] - distance)  # ป้องกันไม่ให้ลงต่ำกว่าพื้น
            
            return self.move_to(new_x, new_y, new_z, speed)
            
        except Exception as e:
            print(f"❌ Move down failed: {e}")
            return False
    
    def rotate_left(self, degrees=45, speed=1.0):
        """หมุนซ้าย - หมุนตัวโดรนไปทางซ้าย"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"🔄 Rotating left {degrees}°...")
            current_ori = self.sim.getObjectOrientation(self.drone_handle, -1)
            
            # แปลงองศาเป็น radian
            import math
            radians = math.radians(degrees)
            new_yaw = current_ori[2] + radians
            
            # ตั้งค่าการหมุนใหม่
            new_orientation = [current_ori[0], current_ori[1], new_yaw]
            
            # หมุนแบบค่อยเป็นค่อยไป
            steps = max(10, int(abs(degrees) / 5))  # ยิ่งหมุนเยอะ steps ยิ่งเยอะ
            
            for i in range(steps):
                progress = (i + 1) / steps
                intermediate_yaw = current_ori[2] + radians * progress
                intermediate_ori = [current_ori[0], current_ori[1], intermediate_yaw]
                
                self.sim.setObjectOrientation(self.drone_handle, -1, intermediate_ori)
                self.rotate_propellers(speed=20)
                time.sleep(0.05 / speed)
            
            self.orientation = new_orientation
            print(f"✓ Rotated left {degrees}°")
            return True
            
        except Exception as e:
            print(f"❌ Rotate left failed: {e}")
            return False
    
    def rotate_right(self, degrees=45, speed=1.0):
        """หมุนขวา - หมุนตัวโดรนไปทางขวา"""
        if not self.drone_handle:
            print("❌ Drone not found!")
            return False
        
        try:
            print(f"🔄 Rotating right {degrees}°...")
            current_ori = self.sim.getObjectOrientation(self.drone_handle, -1)
            
            # แปลงองศาเป็น radian
            import math
            radians = math.radians(degrees)
            new_yaw = current_ori[2] - radians
            
            # ตั้งค่าการหมุนใหม่
            new_orientation = [current_ori[0], current_ori[1], new_yaw]
            
            # หมุนแบบค่อยเป็นค่อยไป
            steps = max(10, int(abs(degrees) / 5))  # ยิ่งหมุนเยอะ steps ยิ่งเยอะ
            
            for i in range(steps):
                progress = (i + 1) / steps
                intermediate_yaw = current_ori[2] - radians * progress
                intermediate_ori = [current_ori[0], current_ori[1], intermediate_yaw]
                
                self.sim.setObjectOrientation(self.drone_handle, -1, intermediate_ori)
                self.rotate_propellers(speed=20)
                time.sleep(0.05 / speed)
            
            self.orientation = new_orientation
            print(f"✓ Rotated right {degrees}°")
            return True
            
        except Exception as e:
            print(f"❌ Rotate right failed: {e}")
            return False

    def get_current_heading(self):
        """ได้ทิศทางปัจจุบันของโดรนในองศา"""
        try:
            orientation = self.get_orientation()
            yaw_degrees = math.degrees(orientation[2])
            # แปลงให้เป็น 0-360 องศา
            if yaw_degrees < 0:
                yaw_degrees += 360
            return yaw_degrees
        except:
            return 0

    def print_drone_status(self):
        """แสดงสถานะปัจจุบันของโดรน"""
        try:
            pos = self.get_position()
            heading = self.get_current_heading()
            print(f"📍 Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            print(f"🧭 Heading: {heading:.1f}°")
        except Exception as e:
            print(f"❌ Status check failed: {e}")


    def rotate_propellers(self, speed=20):
        """หมุนใบพัด"""
        if len(self.propellers) == 4:
            try:
                for i, prop in enumerate(self.propellers):
                    # หมุนใบพัดในทิศทางที่ถูกต้อง (สลับทิศทาง)
                    direction = 1 if i % 2 == 0 else -1
                    self.sim.setJointTargetVelocity(prop, speed * direction)
            except Exception as e:
                print(f"Propeller rotation error: {e}")

    def setup_camera_system(self):
        try:
            # เปลี่ยน path ตามที่ตั้ง alias
            handle = self.sim.getObject('/Quadcopter/visionSensor')  # หรือ '/Quadcopter/FrontCamera'
            if handle != -1:
                obj_type = self.sim.getObjectType(handle)
                if obj_type == self.sim.object_visionsensor_type:
                    self.camera_handle = handle
                    print("✓ Found Vision Sensor and type is correct")
                else:
                    print("⚠️ Found object but not a Vision Sensor")
                    self.camera_handle = None
            else:
                print("❌ ไม่พบกล้องในซีน")
                self.camera_handle = None
        except Exception as e:
            print(f"Camera system setup error: {e}")
            self.camera_handle = None

    def get_camera_image(self):
        if not self.camera_handle:
            print("Camera not available")
            return None

        try:
            time.sleep(0.5)
            result = self.sim.getVisionSensorImg(self.camera_handle)
            print("Raw result from getVisionSensorImg:", result)

            if len(result) == 3:
                status, resolution, image = result
                if status != 1:
                    print("Vision sensor failed to return image")
                    return None
            elif len(result) == 2:
                resolution, image = result
            else:
                print("Unexpected result:", result)
                return None

            print("VisionSensorImg result:", resolution, type(image), len(image) if hasattr(image, '__len__') else image)
            if resolution[0] == 0 or resolution[1] == 0:
                print("❌ กล้องไม่ได้ตั้งค่าความละเอียด หรือ simulation ยังไม่เริ่ม")
                return None

            if isinstance(image, list):
                print("Image is a list. First 10 values:", image[:10])
                image = bytes([min(255, max(0, int(v))) for v in image])
            else:
                print("Image is not a list. Type:", type(image))

            import numpy as np
            import cv2
            img_array = np.frombuffer(image, dtype=np.uint8)
            img = img_array.reshape((resolution[1], resolution[0], 3))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img_bgr = cv2.flip(img_bgr, 0)
            return img_bgr

        except Exception as e:
            print(f"Camera image error: {e}")
            return None
    
    def stream_camera(self, duration=10):
        """แสดงภาพจากกล้องแบบ real-time"""
        print(f"📹 Starting camera stream for {duration} seconds...")
        print("Press 'q' to quit, 'p' to take photo, 'm' to detect mission pad")
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            img = self.get_camera_image()
            
            if img is not None:
                # ตรวจจับ Mission Pad
                detected = self.detect_mission_pad()
                
                # เพิ่มข้อมูลบนภาพ
                if detected:
                    pad_id = detected['id']
                    center = detected['center']
                    distance = detected['distance']
                    
                    # วาดกรอบรอบ Mission Pad
                    cv2.circle(img, center, 20, (0, 255, 0), 3)
                    cv2.putText(img, f"Pad {pad_id}", 
                               (center[0]-20, center[1]-30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(img, f"Dist: {distance:.1f}m", 
                               (center[0]-30, center[1]+50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # เพิ่มข้อมูลโดรน
                if self.drone_handle:
                    pos = self.sim.getObjectPosition(self.drone_handle, -1)
                    cv2.putText(img, f"Alt: {pos[2]:.2f}m", (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # แสดงภาพ
                cv2.imshow("Tello Camera Stream", img)
                
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('p'):
                    self.take_photo()
                elif key == ord('m'):
                    detected = self.detect_mission_pad()
                    if detected:
                        print(f"Mission Pad {detected['id']} detected at distance {detected['distance']:.2f}m")
                    else:
                        print("No Mission Pad detected")
        
        cv2.destroyAllWindows()
        print("Camera stream ended")

    def create_mission_pad(self, pad_id, position, size=1.0):
        """สร้าง Mission Pad ในฉาก"""
        try:
            # สร้างพื้นฐาน pad
            pad = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [size, size, 0.02]
            )
            
            # ตั้งตำแหน่ง
            self.sim.setObjectPosition(pad, -1, [position[0], position[1], 0.01])
            
            # ตั้งค่าสี (แต่ละ pad สีต่างกัน)
            colors = [
                [1, 0, 0],    # แดง - ID 1
                [0, 1, 0],    # เขียว - ID 2  
                [0, 0, 1],    # น้ำเงิน - ID 3
                [1, 1, 0],    # เหลือง - ID 4
                [1, 0, 1],    # ม่วง - ID 5
                [0, 1, 1],    # ฟ้า - ID 6
                [1, 0.5, 0],  # ส้ม - ID 7
                [0.5, 0, 1]   # ม่วงเข้ม - ID 8
            ]
            
            color = colors[(pad_id - 1) % len(colors)]
            self.sim.setShapeColor(pad, None, self.sim.colorcomponent_ambient_diffuse, color)
            
            # สร้างหมายเลข ID บน pad
            self.create_pad_number(pad, pad_id, size)
            
            # ตั้งชื่อ
            self.sim.setObjectAlias(pad, f"MissionPad_{pad_id}")
            
            # เก็บข้อมูล pad
            self.mission_pads[pad_id] = {
                'handle': pad,
                'position': position,
                'size': size,
                'detected': False
            }
            
            print(f"✓ Created Mission Pad {pad_id} at {position}")
            return pad
            
        except Exception as e:
            print(f"Mission pad creation error: {e}")
            return None
    
    def create_pad_number(self, pad_handle, number, pad_size):
        """สร้างหมายเลขบน Mission Pad"""
        try:
            # สร้างข้อความหมายเลข (ใช้ primitive shapes)
            digit_width = pad_size * 0.1
            digit_height = pad_size * 0.3
            
            # สร้างรูปแบบตัวเลขแบบง่าย (7-segment style)
            if number == 1:
                segments = [
                    [0, 0, digit_height*0.7, 0.03]  # เส้นตรงกลาง
                ]
            elif number == 2:
                segments = [
                    [-digit_width/2, digit_height/4, digit_width, 0.03],    # บน
                    [0, 0, digit_width, 0.03],                              # กลาง
                    [digit_width/2, -digit_height/4, digit_width, 0.03]     # ล่าง
                ]
            # เพิ่มตัวเลขอื่นๆ ตามต้องการ
            else:
                # ใช้วงกลมสำหรับตัวเลขอื่นๆ
                segments = [
                    [0, 0, digit_width*2, 0.03]  # วงกลม
                ]
            
            # สร้าง segments
            for i, seg in enumerate(segments):
                segment = self.sim.createPrimitiveShape(
                    self.sim.primitiveshape_cuboid,
                    [seg[2], digit_width/3, seg[3]]
                )
                
                # ตำแหน่งสัมพัทธ์กับ pad
                pad_pos = self.sim.getObjectPosition(pad_handle, -1)
                seg_pos = [pad_pos[0] + seg[0], pad_pos[1] + seg[1], pad_pos[2] + 0.02]
                
                self.sim.setObjectPosition(segment, -1, seg_pos)
                self.sim.setShapeColor(segment, None, self.sim.colorcomponent_ambient_diffuse, [1, 1, 1])
                
        except Exception as e:
            print(f"Pad number creation error: {e}")
    
    def detect_mission_pad(self):
        """ตรวจจับ Mission Pad จากภาพกล้อง"""
        img = self.get_camera_image()
        
        if img is None:
            return None
            
        # วิเคราะห์ภาพเพื่อหา Mission Pad
        detected_pad = self.analyze_image_for_mission_pad(img)
        
        if detected_pad:
            pad_id = detected_pad['id']
            if pad_id != self.current_detected_pad:
                self.current_detected_pad = pad_id
                print(f"🎯 Mission Pad {pad_id} detected!")
                
                # อัพเดทสถานะ
                if pad_id in self.mission_pads:
                    self.mission_pads[pad_id]['detected'] = True
                    
            return detected_pad
        else:
            self.current_detected_pad = None
            return None
    
    def analyze_image_for_mission_pad(self, img):
        """วิเคราะห์ภาพเพื่อหา Mission Pad"""
        try:
            # แปลงเป็น HSV เพื่อตรวจจับสี
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # ตรวจจับสีต่างๆ ของ Mission Pads
            color_ranges = {
                1: ([0, 100, 100], [10, 255, 255]),      # แดง
                2: ([50, 100, 100], [70, 255, 255]),     # เขียว  
                3: ([100, 100, 100], [120, 255, 255]),   # น้ำเงิน
                4: ([20, 100, 100], [30, 255, 255]),     # เหลือง
                5: ([140, 100, 100], [160, 255, 255]),   # ม่วง
                6: ([80, 100, 100], [100, 255, 255]),    # ฟ้า
                7: ([10, 100, 100], [20, 255, 255]),     # ส้ม
                8: ([120, 100, 100], [140, 255, 255])    # ม่วงเข้ม
            }
            
            for pad_id, (lower, upper) in color_ranges.items():
                lower = np.array(lower)
                upper = np.array(upper)
                
                # สร้าง mask
                mask = cv2.inRange(hsv, lower, upper)
                
                # หา contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    
                    # ตรวจสอบขนาดที่เหมาะสม
                    if area > 1000:  # ปรับขนาดตามต้องการ
                        # คำนวณตำแหน่งกลาง
                        M = cv2.moments(contour)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            
                            # คำนวณระยะทางจากกล้อง (ประมาณ)
                            distance = self.estimate_distance_to_pad(area)
                            
                            return {
                                'id': pad_id,
                                'center': (cx, cy),
                                'area': area,
                                'distance': distance,
                                'angle': self.calculate_pad_angle(cx, img.shape[1])
                            }
            
            return None
            
        except Exception as e:
            print(f"Image analysis error: {e}")
            return None
    
    def estimate_distance_to_pad(self, area):
        """ประมาณระยะทางไป Mission Pad จากขนาดในภาพ"""
        # สูตรประมาณ: distance = sqrt(known_area / detected_area) * known_distance
        # ต้องปรับค่าให้เหมาะสมกับขนาดจริง
        if area > 0:
            return max(0.1, 10000 / area)  # ค่าประมาณ
        return 0
    
    def calculate_pad_angle(self, cx, img_width):
        """คำนวณมุมของ Mission Pad เทียบกับแกนกล้อง"""
        center_x = img_width / 2
        angle_per_pixel = 60 / img_width  # 60 องศา field of view
        return (cx - center_x) * angle_per_pixel
    
    def go_to_mission_pad(self, pad_id, height=1.0):
        """บินไปที่ Mission Pad ที่กำหนด"""
        if pad_id not in self.mission_pads:
            print(f"❌ Mission Pad {pad_id} not found")
            return False
            
        pad_info = self.mission_pads[pad_id]
        target_pos = pad_info['position']
        
        print(f"🎯 Flying to Mission Pad {pad_id} at {target_pos}")
        
        # บินขึ้นก่อนถ้ายังไม่บิน
        if not self.is_flying:
            self.takeoff(height)
            
        # บินไปตำแหน่ง pad
        current_pos = self.sim.getObjectPosition(self.drone_handle, -1)
        target_flight_pos = [target_pos[0], target_pos[1], height]
        
        # บินแบบ smooth
        steps = 50
        for i in range(steps):
            interp_pos = [
                current_pos[0] + (target_flight_pos[0] - current_pos[0]) * (i+1) / steps,
                current_pos[1] + (target_flight_pos[1] - current_pos[1]) * (i+1) / steps,
                current_pos[2] + (target_flight_pos[2] - current_pos[2]) * (i+1) / steps
            ]
            
            self.sim.setObjectPosition(self.drone_handle, -1, interp_pos)
            self.rotate_propellers(speed=20)
            
            # ตรวจจับ Mission Pad ระหว่างบิน
            detected = self.detect_mission_pad()
            if detected and detected['id'] == pad_id:
                print(f"✓ Mission Pad {pad_id} detected during flight!")
                
            time.sleep(0.05)
        
        print(f"✓ Arrived at Mission Pad {pad_id}")
        return True


    def setup_camera_system_new(self):
        """ค้นหาและตั้งค่ากล้องที่มีอยู่ในซีน"""
        try:
            print("🔍 Searching for camera...")
            
            # ลิสต์ชื่อกล้องที่เป็นไปได้
            camera_names = [
                '/Quadcopter/visionSensor',
                '/Quadcopter/FrontCamera',
                '/Quadcopter/Camera',
                '/Quadricopter/visionSensor',
                '/Quadricopter/FrontCamera',
                '/Quadricopter/Camera',
                'visionSensor',
                'FrontCamera',
                'Camera'
            ]
            
            self.camera_handle = None
            
            # ลองหากล้องจากชื่อต่างๆ
            for camera_name in camera_names:
                try:
                    handle = self.sim.getObject(camera_name)
                    if handle != -1:
                        # เช็คว่าเป็น vision sensor จริงๆ
                        obj_type = self.sim.getObjectType(handle)
                        if obj_type == self.sim.object_visionsensor_type:
                            self.camera_handle = handle
                            print(f"✓ Found Vision Sensor: {camera_name}")
                            break
                        else:
                            print(f"⚠️ Found object {camera_name} but not a Vision Sensor")
                except:
                    continue
            
            # ถ้าไม่เจอ ลองค้นหาจาก object tree
            if self.camera_handle is None:
                print("🔍 Searching in object tree...")
                try:
                    all_objects = self.sim.getObjectsInTree(self.sim.handle_scene)
                    for obj in all_objects:
                        try:
                            obj_type = self.sim.getObjectType(obj)
                            if obj_type == self.sim.object_visionsensor_type:
                                obj_name = self.sim.getObjectAlias(obj)
                                self.camera_handle = obj
                                print(f"✓ Found Vision Sensor in tree: {obj_name}")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"Error searching object tree: {e}")
            
            if self.camera_handle is None:
                print("❌ No Vision Sensor found in scene")
                print("💡 Please add a Vision Sensor to your scene:")
                print("   1. Right-click in scene hierarchy")
                print("   2. Add > Vision sensor")
                print("   3. Attach it to your drone")
                return False
            
            # ตรวจสอบการตั้งค่ากล้อง
            try:
                # ลองรับภาพเพื่อเช็คว่ากล้องทำงานได้
                result = self.sim.getVisionSensorImg(self.camera_handle)
                print(f"Camera test result: {type(result)}, length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                
                if isinstance(result, (list, tuple)) and len(result) >= 2:
                    if len(result) == 3:
                        status, resolution, _ = result
                        if status != 1:
                            print("⚠️ Vision sensor status not OK")
                    else:
                        resolution, _ = result
                        
                    print(f"Camera resolution: {resolution}")
                    if resolution[0] > 0 and resolution[1] > 0:
                        print("✓ Camera system ready")
                        return True
                    else:
                        print("❌ Invalid camera resolution")
                        return False
                else:
                    print("❌ Unexpected camera result format")
                    return False
                    
            except Exception as e:
                print(f"Camera test error: {e}")
                return False
                
        except Exception as e:
            print(f"Camera system setup error: {e}")
            self.camera_handle = None
            return False

    def get_camera_image_new(self):
        """รับภาพจากกล้อง - ปรับปรุงใหม่"""
        if not self.camera_handle:
            print("❌ Camera not available")
            return None
            
        if not self.simulation_running:
            print("❌ Simulation not running")
            return None

        try:
            print("📸 Capturing image...")
            
            # รอให้ simulation update
            time.sleep(0.1)
            
            # รับภาพจาก vision sensor
            result = self.sim.getVisionSensorImg(self.camera_handle)
            print(f"Raw result type: {type(result)}, length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            
            # จัดการ result ตามรูปแบบที่ได้รับ
            if isinstance(result, (list, tuple)):
                if len(result) == 3:
                    # รูปแบบ: [status, resolution, image_data]
                    status, resolution, image_data = result
                    print(f"Status: {status}, Resolution: {resolution}")
                    
                    if status != 1:
                        print(f"❌ Vision sensor failed with status: {status}")
                        return None
                        
                elif len(result) == 2:
                    # รูปแบบ: [resolution, image_data]
                    resolution, image_data = result
                    print(f"Resolution: {resolution}")
                    
                else:
                    print(f"❌ Unexpected result format: {len(result)} elements")
                    return None
                    
            else:
                print(f"❌ Unexpected result type: {type(result)}")
                return None
            
            # ตรวจสอบ resolution
            if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
                print(f"❌ Invalid resolution format: {resolution}")
                return None
                
            width, height = resolution
            if width <= 0 or height <= 0:
                print(f"❌ Invalid resolution values: {width}x{height}")
                return None
            
            print(f"Image size: {width}x{height}")
            
            # ตรวจสอบข้อมูลภาพ
            if image_data is None:
                print("❌ No image data received")
                return None
                
            print(f"Image data type: {type(image_data)}, length: {len(image_data) if hasattr(image_data, '__len__') else 'N/A'}")
            
            # แปลงข้อมูลภาพ
            if isinstance(image_data, list):
                # แปลง list เป็น bytes
                image_bytes = bytes([min(255, max(0, int(v))) for v in image_data])
            elif isinstance(image_data, (bytes, bytearray)):
                image_bytes = bytes(image_data)
            else:
                print(f"❌ Unsupported image data type: {type(image_data)}")
                return None
            
            expected_size = width * height * 3  # RGB
            actual_size = len(image_bytes)
            print(f"Expected size: {expected_size}, Actual size: {actual_size}")
            
            if actual_size != expected_size:
                print(f"❌ Image size mismatch. Expected: {expected_size}, Got: {actual_size}")
                return None
            
            # สร้าง numpy array
            img_array = np.frombuffer(image_bytes, dtype=np.uint8)
            
            # Reshape เป็นภาพ
            try:
                img = img_array.reshape((height, width, 3))
                print(f"✓ Image reshaped successfully: {img.shape}")
            except ValueError as e:
                print(f"❌ Reshape error: {e}")
                return None
            
            # แปลง RGB เป็น BGR สำหรับ OpenCV
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Flip ภาพให้ถูกต้อง (CoppeliaSim อาจ flip ภาพ)
            img_bgr = cv2.flip(img_bgr, 0)
            
            print("✓ Image processed successfully")
            return img_bgr
            
        except Exception as e:
            print(f"❌ Camera image error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def take_photo_new(self, filename=None):
        """ถ่ายรูปและบันทึก"""
        print("📸 Taking photo...")
        
        img = self.get_camera_image()
        
        if img is not None:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tello_photo_{timestamp}_{self.photo_count:03d}.jpg"
                
            filepath = os.path.join(self.photo_dir, filename)
            
            # เพิ่มข้อมูล overlay
            height, width = img.shape[:2]
            
            # เพิ่มข้อมูลตำแหน่งโดรน
            if self.drone_handle:
                try:
                    pos = self.sim.getObjectPosition(self.drone_handle, -1)
                    info_text = f"Alt: {pos[2]:.2f}m  Pos: ({pos[0]:.1f}, {pos[1]:.1f})"
                    cv2.putText(img, info_text, (10, height-20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                except:
                    pass
                
            # เพิ่มเวลา
            time_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(img, time_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # บันทึกรูป
            success = cv2.imwrite(filepath, img)
            
            if success:
                self.photo_count += 1
                print(f"✓ Photo saved: {filepath}")
                return filepath
            else:
                print("❌ Failed to save photo")
                return None
        else:
            print("❌ No image available")
            return None

    def test_camera(self):
        """ทดสอบกล้องโดยเฉพาะ"""
        print("🔍 Testing camera system...")
        
        if not self.simulation_running:
            print("❌ Please start simulation first")
            return False
        
        # ตั้งค่ากล้อง
        if not self.setup_camera_system():
            return False
        
        # ลองถ่ายรูป
        img = self.get_camera_image()
        if img is not None:
            # แสดงภาพ
            cv2.imshow("Camera Test", img)
            print("✓ Camera test successful! Press any key to close...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return True
        else:
            print("❌ Camera test failed")
            return False

    # ตัวอย่างการใช้งาน
if __name__ == "__main__":
    # สร้าง simulator object
    drone = TelloSimulator()
    
    try:
        # เริ่ม simulation
        drone.start_simulation()
        time.sleep(1)
        
        # บินขึ้น
        drone.takeoff(height=1.5)

        
        # Hover
        drone.hover(duration=2)
        
        # บินขึ้นลง 3 รอบ
        drone.fly_pattern_up_down(cycles=3, height_change=0.5)
        
        # Hover อีกครั้ง
        drone.hover(duration=1)


        
        # ลงจอด
        drone.land()
        
        time.sleep(2)
        
    finally:
        # หยุด simulation
        drone.stop_simulation()
