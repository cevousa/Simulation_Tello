#!/usr/bin/env python3
"""
Drone Odyssey Challenge Field Creator - Organized Version
แยกส่วนโค้ดให้เป็นระเบียบ
"""

import time
import math
import random
import os
try:
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient
except ImportError:
    from zmqRemoteApi import RemoteAPIClient

class DroneOdysseyFieldCreator:
    def __init__(self):
        self.client = RemoteAPIClient()
        self.sim = self.client.getObject('sim')
        
        self.simulation_running = False
        self.field_objects = []
        
        # ขนาดสนามตามมาตรฐาน
        self.field_size = 5.0  # 5×5 เมตร
        self.tile_size = 0.8   # แผ่นขนาด 80×80 ซม.
        self.tile_gap = 0.2    # ช่องว่าง 20 ซม.
        self.border_gap = 0.1  # เว้นจากขอบ 10 ซม.
        
        # ขนาดอุปกรณ์
        self.obstacle_size = [0.6, 0.6, 0.8]  # กล่อง 60×60×80 ซม.
        self.qr_board_size = [0.3, 0.3, 0.02] # ป้าย QR 30×30 ซม.
        self.image_board_size = [0.4, 0.3, 0.02] # ป้ายรูป 40×30 ซม.
        
        # พาธไฟล์ QR Code
        self.qr_texture_path = r".\testqrcode.png"
        self.image_texture_path=r".\testpicture.jpg"
        print("🏟️ Drone Odyssey Challenge Field Creator (Organized)")
        print(f"📏 Field: {self.field_size}×{self.field_size}m")
        print(f"🔲 Tiles: {self.tile_size*100:.0f}×{self.tile_size*100:.0f}cm, Gap: {self.tile_gap*100:.0f}cm")

    # ===============================================================
    # SECTION 1: SIMULATION MANAGEMENT
    # ===============================================================
        
    def start_simulation(self):
        """เริ่มการจำลอง"""
        try:
            # Physics Engine มักจะเปิดอยู่ตามค่าเริ่มต้น
            self.sim.startSimulation()
            self.simulation_running = True
            print("✅ Simulation started")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Failed to start simulation: {e}")
            return False

    def diagnose_and_fix_physics_issues(self):
        """แก้ไขปัญหาฟิสิกส์ - ลดการเรียกซ้ำ"""
        
        # เรียกครั้งเดียวเท่านั้น
        if hasattr(self, '_physics_fixed'):
            return
        
        print("🔍 กำลังตรวจสอบและแก้ไขปัญหาฟิสิกส์...")
        
        # ตั้งค่า physics engine
        try:
            self.sim.setFloatParameter(self.sim.floatparam_simulation_time_step, 0.005)
            self.sim.setBoolParameter(self.sim.boolparam_realtime_simulation, True)
            print("✅ ปรับการตั้งค่า physics engine")
        except Exception as e:
            print(f"⚠️ Physics engine warning: {e}")
        
        # แก้ไขการตั้งค่าพื้น
        floor_handles = []
        for obj in self.field_objects:
            if obj.get('type') == 'floor':
                floor_handles.append(obj['handle'])
        
        for floor_handle in floor_handles:
            self.sim.setObjectInt32Parameter(floor_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(floor_handle, self.sim.shapeintparam_respondable, 1)
            self.sim.setShapeMass(floor_handle, 1000.0)
        
        print("✅ แก้ไขการตั้งค่าพื้นเสร็จสิ้น")
        print("🎯 การแก้ไขปัญหาฟิสิกส์เสร็จสมบูรณ์!")
        
        # ตั้งค่าให้ไม่เรียกซ้ำ
        self._physics_fixed = True




    def clear_field(self):
        """ล้างวัตถุในสนาม - ใช้ API ใหม่"""
        if hasattr(self, 'field_objects') and self.field_objects:
            handles_to_remove = []
            
            for obj in self.field_objects:
                if 'handle' in obj:
                    handles_to_remove.append(obj['handle'])
            
            if handles_to_remove:
                try:
                    # ✅ ใช้ removeObjects แทน removeObject
                    self.sim.removeObjects(handles_to_remove)
                    print(f"🗑️ Cleared {len(handles_to_remove)} field objects")
                except Exception as e:
                    print(f"⚠️ Warning during cleanup: {e}")
            
            self.field_objects.clear()
        else:
            print("🗑️ Cleared 0 field objects")


    def list_field_objects(self):
        """แสดงรายการวัตถุในสนาม"""
        if not self.field_objects:
            print("📭 No field objects found")
            return
        
        object_types = {}
        for obj in self.field_objects:
            obj_type = obj['type']
            if obj_type not in object_types:
                object_types[obj_type] = []
            object_types[obj_type].append(obj)
        
        print(f"\n🏟️ Field objects summary ({len(self.field_objects)} total):")
        for obj_type, objects in object_types.items():
            print(f"  📋 {obj_type.title().replace('_', ' ')}: {len(objects)} objects")
            for obj in objects[:3]:
                if 'grid' in obj:
                    print(f"    - {obj.get('name', 'Unnamed')} at {obj['grid']}")
                else:
                    print(f"    - {obj.get('name', 'Unnamed')}")
            if len(objects) > 3:
                print(f"    - ... และอีก {len(objects)-3} รายการ")
        print()

    # ===============================================================
    # SECTION 2: COORDINATE SYSTEM
    # ===============================================================
    
    def grid_to_position(self, grid_x, grid_y):
        """แปลงตำแหน่ง Grid เป็นพิกัดจริง (A1 = มุมล่างซ้าย)"""
        real_x = self.border_gap + (self.tile_size + self.tile_gap) * grid_x + self.tile_size/2 - self.field_size/2
        real_y = self.border_gap + (self.tile_size + self.tile_gap) * grid_y + self.tile_size/2 - self.field_size/2
        return [real_x, real_y]

    def grid_to_edge_position(self, grid_x, grid_y):
        """แปลงตำแหน่ง Grid เป็นพิกัดขอบ (สำหรับป้ายที่ขอบ)"""
        center_pos = self.grid_to_position(grid_x, grid_y)
        
        # คำนวณตำแหน่งขอบ
        if grid_x == 0:  # ขอบซ้าย (A)
            edge_x = -self.field_size/2 + 0.05
        elif grid_x == 4:  # ขอบขวา (E)
            edge_x = self.field_size/2 - 0.05
        else:
            edge_x = center_pos[0]
        
        if grid_y == 0:  # ขอบล่าง (1)
            edge_y = -self.field_size/2 + 0.05
        elif grid_y == 4:  # ขอบบน (5)
            edge_y = self.field_size/2 - 0.05
        else:
            edge_y = center_pos[1]
        
        return [edge_x, edge_y]

    # ===============================================================
    # SECTION 3: BASIC OBJECTS CREATION
    # ===============================================================
    def fix_floor_settings(self):
        floor_handles = []
        
        # ค้นหาวัตถุพื้นทั้งหมด
        for i in range(25):  # จำนวน floor tiles
            try:
                floor_name = f"FloorTile_{i}"
                floor_handle = self.sim.getObject(floor_name)
                floor_handles.append(floor_handle)
            except:
                continue
        
        # ตั้งค่าพื้นให้เป็น static และ respondable
        for floor_handle in floor_handles:
            # ตั้งค่าให้เป็น static (1) และ respondable (1)
            self.sim.setObjectInt32Parameter(floor_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(floor_handle, self.sim.shapeintparam_respondable, 1)
            
            # ตั้งค่าให้เป็น collidable
            self.sim.setObjectInt32Parameter(floor_handle, self.sim.shapeintparam_collidable, 1)
            
            print(f"Fixed floor: {floor_handle}")    

    def create_tiled_floor(self):
        """สร้างพื้นสนามแบ่งช่อง 5×5"""
        print("🟫 Creating tiled floor (5×5 grid)...")
        
        floor_objects = []
        
        for i in range(5):  # A-E (0-4)
            for j in range(5):  # 1-5 (0-4)
                floor_tile = self.sim.createPrimitiveShape(
                    self.sim.primitiveshape_cuboid,
                    [self.tile_size, self.tile_size, 0.005]  # ลดความหนาเป็น 0.5 ซม.
                )
                
                pos = self.grid_to_position(i, j)
                pos.append(0.0025)  # ปรับความสูงให้เสมอพื้นมากขึ้น
                
                self.sim.setObjectPosition(floor_tile, -1, pos)
                
                grid_name = f"{chr(65+i)}{j+1}"
                self.sim.setObjectAlias(floor_tile, f"Floor_{grid_name}")
                
                # สีขาวอ่อน
                self.sim.setShapeColor(floor_tile, None, 
                    self.sim.colorcomponent_ambient_diffuse, [0.95, 0.95, 0.95])
                
                floor_info = {
                    'type': 'floor',
                    'handle': floor_tile,
                    'grid': grid_name,
                    'position': pos
                }
                floor_objects.append(floor_info)
            self.diagnose_and_fix_physics_issues()
        self.field_objects.extend(floor_objects)
        print(f"✅ Created {len(floor_objects)} floor tiles")
        return floor_objects

    def create_boundary_wall(self, start_pos, end_pos, height=0.12, name="Wall"):
        """สร้างกำแพงกั้น"""
        try:
            length = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
            angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
            
            wall = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [length, 0.06, height]
            )
            
            center_pos = [
                (start_pos[0] + end_pos[0]) / 2,
                (start_pos[1] + end_pos[1]) / 2,
                height/2 + 0.02
            ]
            
            self.sim.setObjectPosition(wall, -1, center_pos)
            self.sim.setObjectOrientation(wall, -1, [0, 0, angle])
            
            # สีเขียว
            self.sim.setShapeColor(wall, None, 
                self.sim.colorcomponent_ambient_diffuse, [0.2, 0.8, 0.2])
            
            self.sim.setObjectSpecialProperty(wall, 
                self.sim.objectspecialproperty_collidable + 
                self.sim.objectspecialproperty_detectable +
                self.sim.objectspecialproperty_renderable
            )
            
            self.sim.setObjectAlias(wall, name)
            
            wall_info = {
                'type': 'boundary_wall',
                'handle': wall,
                'name': name,
                'position': center_pos
            }
            
            self.field_objects.append(wall_info)
            print(f"🟢 Created boundary wall: {name}")
            return wall_info
            
        except Exception as e:
            print(f"❌ Failed to create boundary wall: {e}")
            return None

    # ===============================================================
    # SECTION 4: OBSTACLE CREATION
    # ===============================================================
    
    def create_obstacle_box(self, grid_x, grid_y, name=None):
        """สร้างกล่องสิ่งกีดขวาง 60×60×80 ซม."""
        try:
            if name is None:
                name = f"Obstacle_{chr(65+grid_x)}{grid_y+1}"
            
            obstacle = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                self.obstacle_size
            )
            
            pos = self.grid_to_position(grid_x, grid_y)
            pos.append(self.obstacle_size[2]/2 + 0.02)
            
            self.sim.setObjectPosition(obstacle, -1, pos)
            self.sim.setObjectAlias(obstacle, name)
            
            # สีน้ำตาล
            self.sim.setShapeColor(obstacle, None, 
                self.sim.colorcomponent_ambient_diffuse, [0.6, 0.4, 0.2])
            
            self.sim.setObjectSpecialProperty(obstacle, 
                self.sim.objectspecialproperty_collidable + 
                self.sim.objectspecialproperty_detectable +
                self.sim.objectspecialproperty_renderable
            )
            
            obstacle_info = {
                'type': 'obstacle',
                'handle': obstacle,
                'name': name,
                'grid': f"{chr(65+grid_x)}{grid_y+1}",
                'position': pos
            }
            
            self.field_objects.append(obstacle_info)
            print(f"📦 Created obstacle: {name} at {obstacle_info['grid']}")
            return obstacle_info
            
        except Exception as e:
            print(f"❌ Failed to create obstacle: {e}")
            return None

    def create_adjustable_obstacle(self, grid_x, grid_y, height_multiplier=1, stack_count=1, name=None):
        """สร้างสิ่งกีดขวางที่ปรับความสูงได้"""
        if name is None:
            name = f"Obstacle_{chr(65+grid_x)}{grid_y+1}"
        
        base_height = 0.8  # 80 ซม.
        
        obstacle = self.sim.createPrimitiveShape(
            self.sim.primitiveshape_cuboid,
            [0.6, 0.6, base_height * height_multiplier]
        )
        
        pos = self.grid_to_position(grid_x, grid_y)
        pos.append((base_height * height_multiplier / 2) + 0.02)
        
        self.sim.setObjectPosition(obstacle, -1, pos)
        self.sim.setObjectAlias(obstacle, name)
        
        # สีเหลืองสำหรับกล่องสูง
        if height_multiplier == 2:
            self.sim.setShapeColor(obstacle, None, 
                self.sim.colorcomponent_ambient_diffuse, [1.0, 1.0, 0.0])
        else:
            # สีน้ำตาลสำหรับกล่องปกติ
            self.sim.setShapeColor(obstacle, None, 
                self.sim.colorcomponent_ambient_diffuse, [0.6, 0.4, 0.2])
        
        obstacle_info = {
            'type': 'adjustable_obstacle',
            'handle': obstacle,
            'name': name,
            'grid': f"{chr(65+grid_x)}{grid_y+1}",
            'position': pos,
            'height_multiplier': height_multiplier
        }
        
        self.field_objects.append(obstacle_info)
        return obstacle_info

    def create_obstacle_box_with_qr(self, grid_x, grid_y, name=None):
        """สร้างกล่องสิ่งกีดขวางที่ติดป้าย QR Code"""
        try:
            if name is None:
                name = f"QRBox_{chr(65+grid_x)}{grid_y+1}"
            
            # สร้างกล่อง
            obstacle = self.create_obstacle_box(grid_x, grid_y, name)
            if not obstacle:
                return None
            
            # สร้างป้าย QR Code ติดบนกล่อง
            qr_board = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                self.qr_board_size
            )
            
            # ติดที่ด้านหน้ากล่อง
            box_pos = obstacle['position']
            qr_pos = [
                box_pos[0] + self.obstacle_size[0]/2 + 0.015,
                box_pos[1],
                box_pos[2] + 0.15
            ]
            
            self.sim.setObjectPosition(qr_board, -1, qr_pos)
            self.sim.setObjectOrientation(qr_board, -1, [0, math.pi/2, 0])
            self.sim.setObjectAlias(qr_board, f"QR_{name}")
            
            # สีขาว
            self.sim.setShapeColor(qr_board, None, 
                self.sim.colorcomponent_ambient_diffuse, [1, 1, 1])
            
            # ตรวจสอบ texture
            if os.path.exists(self.qr_texture_path):
                print(f"  ✅ QR texture file found: {name}")
                print(f"  💡 Texture will be white placeholder")
            else:
                print(f"  ⚠️ QR texture file not found: {self.qr_texture_path}")
            
            # อัปเดตข้อมูล obstacle
            obstacle['has_qr'] = True
            obstacle['qr_board'] = qr_board
            obstacle['type'] = 'qr_obstacle'
            
            print(f"📱 Created QR obstacle: {name} at {obstacle['grid']}")
            return obstacle
            
        except Exception as e:
            print(f"❌ Failed to create QR obstacle: {e}")
            return None
        
    def create_custom_obstacle(self, grid_x, grid_y, height_cm=80, name=None):
        """สร้างสิ่งกีดขวางที่ปรับความสูงได้ (custom)
        
        Args:
            grid_x, grid_y: ตำแหน่ง grid
            height_cm: ความสูงเป็นเซนติเมตร (เช่น 80, 160, 240)
            name: ชื่อกำหนดเอง
        """
        try:
            if name is None:
                name = f"CustomObstacle_{chr(65+grid_x)}{grid_y+1}_H{height_cm}"
            
            # แปลงความสูงจาก cm เป็น m
            height_m = height_cm / 100.0
            
            # ตรวจสอบความสูงไม่เกิน 240 cm
            if height_cm > 240:
                print(f"⚠️ Warning: Height {height_cm}cm exceeds maximum 240cm")
                height_cm = 240
                height_m = 2.4
            
            obstacle = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [0.6, 0.6, height_m]  # 60×60×ความสูงที่กำหนด
            )
            
            pos = self.grid_to_position(grid_x, grid_y)
            pos.append(height_m/2 + 0.02)  # วางให้กึ่งกลางความสูง
            
            self.sim.setObjectPosition(obstacle, -1, pos)
            self.sim.setObjectAlias(obstacle, name)
            
            # เลือกสีตามความสูง
            if height_cm <= 80:
                color = [0.6, 0.4, 0.2]  # สีน้ำตาล
            elif height_cm <= 160:
                color = [1.0, 1.0, 0.0]  # สีเหลือง
            else:
                color = [1.0, 0.5, 0.0]  # สีส้ม (สูงมาก)
            
            self.sim.setShapeColor(obstacle, None, 
                self.sim.colorcomponent_ambient_diffuse, color)
            
            self.sim.setObjectSpecialProperty(obstacle, 
                self.sim.objectspecialproperty_collidable + 
                self.sim.objectspecialproperty_detectable +
                self.sim.objectspecialproperty_renderable
            )
            
            obstacle_info = {
                'type': 'custom_obstacle',
                'handle': obstacle,
                'name': name,
                'grid': f"{chr(65+grid_x)}{grid_y+1}",
                'position': pos,
                'height_cm': height_cm,
                'height_m': height_m
            }
            
            self.field_objects.append(obstacle_info)
            print(f"📦 Created custom obstacle: {name} at {obstacle_info['grid']} (H={height_cm}cm)")
            return obstacle_info
            
        except Exception as e:
            print(f"❌ Failed to create custom obstacle: {e}")
            return None

    # ===============================================================
    # SECTION 5: SIGNS AND BOARDS
    # ===============================================================
        
    def create_edge_image_stand(self, grid_x, grid_y, height_cm=120, name=None):
        """สร้างป้ายแบบสี่เหลี่ยมผืนผ้าโง่ๆ ที่หันหน้าไปศูนย์กลาง - แก้ไขการหมุน"""
        try:
            if name is None:
                name = f"EdgeStand_{chr(65+grid_x)}{grid_y+1}"
            
            # ใช้ตำแหน่งขอบ
            pos = self.grid_to_edge_position(grid_x, grid_y)
            
            # แปลงความสูงจาก cm เป็น m
            height_m = height_cm / 100.0
            
            # สร้างสี่เหลี่ยมผืนผ้า - ด้านกว้างเป็น Y, ด้านบางเป็น X
            billboard = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [0.02, 0.50, height_m]  # X=หนา, Y=กว้าง, Z=สูง
            )
            
            # วางป้าย
            billboard_pos = pos.copy()
            billboard_pos.append(height_m/2 + 0.01)  # กึ่งกลางความสูง
            
            self.sim.setObjectPosition(billboard, -1, billboard_pos)
            
            # คำนวณมุมหันเข้าศูนย์กลาง
            center_x, center_y = 0, 0  # จุดศูนย์กลางสนาม
            dx = center_x - pos[0]
            dy = center_y - pos[1]
            yaw = math.atan2(dy, dx)
            
            # ทดสอบหมุนแบบต่างๆ เพื่อให้หน้าป้ายหันเข้าใน
            # ถ้าปกติ cuboid หน้าป้ายอยู่ด้าน +Y (หรือ -Y)
            # ต้องหมุนให้หน้าป้ายชีงไปศูนย์กลาง
            
            # ลองหมุนไม่เพิ่ม π/2 ดู
            self.sim.setObjectOrientation(billboard, -1, [0, 0, yaw])
            
            self.sim.setObjectAlias(billboard, name)
            
            # สีฟ้าสด
            self.sim.setShapeColor(billboard, None, 
                self.sim.colorcomponent_ambient_diffuse, [0.1, 0.5, 1.0])
            
            # ใส่เท็กซ์เจอร์ (ถ้ามี)
            self.apply_texture_to_board(billboard, self.image_texture_path)
            
            stand_info = {
                'type': 'edge_image_stand',
                'handle': billboard,
                'texture_board': billboard,  # เป็นชิ้นเดียวกัน
                'name': name,
                'grid': f"{chr(65+grid_x)}{grid_y+1}",
                'position': pos,
                'height_cm': height_cm,
                'height_m': height_m,
                'facing_angle': yaw
            }
            
            self.field_objects.append(stand_info)
            print(f"🖼️ Created billboard: {name} at {stand_info['grid']} (H={height_cm}cm, angle={math.degrees(yaw):.1f}°)")
            return stand_info
            
        except Exception as e:
            print(f"❌ Failed to create billboard: {e}")
            return None

    def apply_texture_to_board(self, board_handle, texture_path):
        """แก้ไขการโหลด texture สำหรับ CoppeliaSim 4.10"""
        try:
            if not os.path.exists(texture_path):
                return False
            
            # ใช้วิธีง่ายๆ - ข้าม texture loading
            print(f"📁 Texture file found: {texture_path}")
            print(f"💡 Using default color (texture loading skipped)")
            return True
            
        except Exception as e:
            print(f"⚠️ Texture error: {e}")
            return False

    # ===============================================================
    # SECTION 6: PING PONG SYSTEM
    # ===============================================================
        
    def create_ping_pong_ball(self, position, name, ultra_sensitive=False):
        """สร้างลูกปิงปองที่มีขนาดและน้ำหนักตามจริง"""
        
        # ข้อมูลจำเพาะลูกปิงปอง
        diameter = 0.08  # เพิ่มขนาดเป็น 8cm เพื่อให้เห็นชัดเจน
        mass_real = 0.0027  # 2.7g
        
        # ✅ สร้างทรงกลมด้วยตัวเลขโดยตรง
        options = 0  # ไม่ใส่ options พิเศษ
        ball = self.sim.createPrimitiveShape(
            1,  # 1 = sphere (แทน self.sim.primitiveshape_sphere)
            [diameter, diameter, diameter],
            options
        )
        
        if ball == -1:
            print(f"❌ ไม่สามารถสร้างลูกปิงปอง {name} ได้")
            return None
        
        # ตั้งชื่อและตำแหน่ง
        self.sim.setObjectAlias(ball, name)
        pos = position.copy()
        pos[2] = 0.1  # วางสูง 10cm
        self.sim.setObjectPosition(ball, -1, pos)
        
        # ตั้งสีส้มสด
        self.sim.setShapeColor(ball, None,
            self.sim.colorcomponent_ambient_diffuse, [1.0, 0.5, 0.0])
        
        # ตั้งค่ามวล
        mass = 0.001 if ultra_sensitive else mass_real
        self.sim.setShapeMass(ball, mass)
        
        # ตั้งค่าให้เป็น dynamic object
        self.sim.setObjectInt32Parameter(ball, self.sim.shapeintparam_static, 0)
        self.sim.setObjectInt32Parameter(ball, self.sim.shapeintparam_respondable, 1)
        
        # ตั้งค่า moment of inertia
        inertia = (2/5) * mass * (diameter/2)**2
        inertia_matrix = [inertia, 0, 0, 0, inertia, 0, 0, 0, inertia]
        transform = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
        self.sim.setShapeInertia(ball, inertia_matrix, transform)
        
        # ตั้งค่าฟิสิกส์
        try:
            self.sim.setEngineFloatParam(3007, ball, 0.3)   # friction
            self.sim.setEngineFloatParam(3008, ball, 0.7)   # restitution
        except:
            pass  # ถ้าไม่สามารถตั้งค่าได้ ให้ข้าม
        
        # รีเซ็ตวัตถุไดนามิกเป็นขั้นตอนสุดท้าย
        self.sim.resetDynamicObject(ball)
        
        print(f"✅ สร้างลูกปิงปอง {name} สำเร็จ (ขนาด: {diameter}m)")
        return ball

    def verify_ping_pong_shape(self):
        """ตรวจสอบรูปร่างของลูกปิงปองที่สร้าง"""
        print("🔍 ตรวจสอบรูปร่างลูกปิงปอง...")
        
        for obj in self.field_objects:
            if obj.get('type') == 'wind_responsive_a3':
                ball_handle = obj['handle']
                ball_name = obj['name']
                
                try:
                    # ตรวจสอบตำแหน่ง
                    pos = self.sim.getObjectPosition(ball_handle, -1)
                    
                    # ตรวจสอบสถานะฟิสิกส์
                    is_static = self.sim.getObjectInt32Parameter(ball_handle, self.sim.shapeintparam_static)
                    is_respondable = self.sim.getObjectInt32Parameter(ball_handle, self.sim.shapeintparam_respondable)
                    
                    print(f"🏓 {ball_name}:")
                    print(f"   Position: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
                    print(f"   Static: {is_static}, Respondable: {is_respondable}")
                    
                    # ตรวจสอบว่าลูกปิงปองอยู่เหนือพื้นหรือไม่
                    if pos[2] > 0.02:
                        print(f"   ✅ ตำแหน่งปกติ")
                    else:
                        print(f"   ⚠️ ตำแหน่งต่ำเกินไป")
                        
                except Exception as e:
                    print(f"   ❌ ไม่สามารถตรวจสอบได้: {e}")


    def create_ping_pong_in_fenced_area(self):
        """สร้างลูกปิงปองหลายลูกในช่อง A3 - เวอร์ชันแก้ไขแล้ว"""
        grid_x, grid_y = 0, 2  # A3
        
        # ตำแหน่งกลางของช่อง A3
        center_pos = self.grid_to_position(grid_x, grid_y)
        
        # จัดลูกปิงปองหลายลูกในช่องเดียว
        ball_patterns = [
            [0, 0],        # กลาง
            [-0.15, 0],    # ซ้าย
            [0.15, 0],     # ขวา  
            [0, -0.15],    # ล่าง
            [0, 0.15],     # บน
            [-0.1, -0.1],  # ซ้ายล่าง
            [0.1, 0.1],    # ขวาบน
        ]
        
        created_balls = []
        
        for i, (offset_x, offset_y) in enumerate(ball_patterns):
            ball_pos = [
                center_pos[0] + offset_x,
                center_pos[1] + offset_y,
                0.05  # เริ่มต้นที่ความสูง 5cm
            ]
            
            name = f"PingPong_A3_{i+1}"
            
            # ใช้ฟังก์ชันที่แก้ไขแล้ว
            ball = self.create_ping_pong_ball(ball_pos, name, ultra_sensitive=False)
            
            if ball:
                ball_info = {
                    'type': 'wind_responsive_a3',
                    'handle': ball,
                    'name': name,
                    'grid': 'A3',
                    'position': ball_pos,
                    'mass_g': 2.7,
                    'diameter_mm': 40,
                    'dynamic': True,
                    'wind_responsive': True,
                    'color': 'orange'
                }
                
                self.field_objects.append(ball_info)
                created_balls.append(ball_info)
        
        print(f"🏓 Created {len(created_balls)} wind-responsive ping pong balls in A3")
        return created_balls

    def check_ping_pong_visibility(self):
        """ตรวจสอบและแก้ไขลูกปิงปอง - เวอร์ชันแก้ไข deprecated"""
        print("🔍 ตรวจสอบลูกปิงปองทั้งหมด...")
        
        ping_pong_balls = []
        for obj in self.field_objects:
            if obj.get('type') == 'wind_responsive_a3':
                ping_pong_balls.append(obj)
        
        if not ping_pong_balls:
            print("❌ ไม่พบลูกปิงปอง")
            return
        
        for ball_info in ping_pong_balls:
            ball_handle = ball_info['handle']
            ball_name = ball_info['name']
            
            # ✅ ใช้ removeObjects แทน removeObject
            try:
                self.sim.removeObjects([ball_handle])  # เปลี่ยนจาก removeObject
                print(f"🗑️ ลบลูกปิงปอง {ball_name} เก่า")
                
                # สร้างใหม่ด้วยฟังก์ชันที่แก้ไขแล้ว
                new_position = ball_info['position']
                new_ball = self.create_ping_pong_ball(new_position, ball_name, False)
                
                if new_ball:
                    ball_info['handle'] = new_ball
                    print(f"✅ สร้างลูกปิงปอง {ball_name} ใหม่สำเร็จ")
                else:
                    print(f"❌ ไม่สามารถสร้างลูกปิงปอง {ball_name} ใหม่ได้")
                    
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดกับ {ball_name}: {e}")
        
        # ตรวจสอบรูปร่างหลังสร้างใหม่
        self.verify_ping_pong_shape()

    def create_ping_pong_balls_in_grid(self, grid_x, grid_y, num_balls=7, name_prefix=None):
        """สร้างลูกปิงปองหลายลูกในช่องที่กำหนด - ตอบสนองแรงลม"""
        if name_prefix is None:
            name_prefix = f"PingPong_{chr(65+grid_x)}{grid_y+1}"
        
        # ตำแหน่งกลางของช่อง
        center_pos = self.grid_to_position(grid_x, grid_y)
        
        # รูปแบบการจัดลูกในช่อง (สูงสุด 7 ลูก)
        ball_patterns = [
            [0, 0],        # 1. กลาง
            [-0.15, 0],    # 2. ซ้าย
            [0.15, 0],     # 3. ขวา  
            [0, -0.15],    # 4. ล่าง
            [0, 0.15],     # 5. บน
            [-0.1, -0.1],  # 6. ซ้ายล่าง
            [0.1, 0.1],    # 7. ขวาบน
        ]
        
        created_balls = []
        
        for i in range(min(num_balls, len(ball_patterns))):
            offset_x, offset_y = ball_patterns[i]
            
            # คำนวณตำแหน่งในช่อง
            ball_pos = [
                center_pos[0] + offset_x,
                center_pos[1] + offset_y,
                0.025  # วางบนพื้น
            ]
            
            name = f"{name_prefix}_{i+1}"
            
            # สร้างลูกปิงปองที่ตอบสนองแรงลม
            ball = self.create_ping_pong_ball(ball_pos, name, ultra_sensitive=False)
            
            if ball:
                ball_info = {
                    'type': 'wind_responsive_ping_pong',
                    'handle': ball,
                    'name': name,
                    'grid': f"{chr(65+grid_x)}{grid_y+1}",
                    'position': ball_pos,
                    'mass_g': 2.7,
                    'diameter_mm': 40,
                    'dynamic': True,
                    'wind_responsive': True
                }
                
                self.field_objects.append(ball_info)
                created_balls.append(ball_info)
        
        grid_name = f"{chr(65+grid_x)}{grid_y+1}"
        print(f"🏓 Created {len(created_balls)} wind-responsive ping pong balls in {grid_name}")
        return created_balls
    # ===============================================================
    # SECTION 7: FENCE SYSTEMS
    # ===============================================================
    

    def create_livestock_fence_from_diagram(self):
        """สร้างรั้วสีเขียวตามแผนภาพ (รูปตัว L กลับด้าน)"""
        # คำนวณตำแหน่งของแต่ละ grid
        a3_pos = self.grid_to_position(0, 2)  # A3
        a4_pos = self.grid_to_position(0, 3)  # A4
        b3_pos = self.grid_to_position(1, 2)  # B3
        b4_pos = self.grid_to_position(1, 3)  # B4
        b5_pos = self.grid_to_position(1, 4)  # B5
        
        half_tile = self.tile_size / 2
        
        # สร้างรั้วตามแผนภาพ
        fence_segments = [
            # รั้วล่าง A3-B3
            ([a3_pos[0] - half_tile, a3_pos[1] - half_tile], 
             [b3_pos[0] + half_tile, b3_pos[1] - half_tile], "A3_B3_Bottom"),
            
            # รั้วซ้าย A3-A4
            ([a3_pos[0] - half_tile, a3_pos[1] - half_tile], 
             [a4_pos[0] - half_tile, a4_pos[1] + half_tile], "A3_A4_Left"),
            
            # รั้วบน A4
            ([a4_pos[0] - half_tile, a4_pos[1] + half_tile], 
             [b4_pos[0] - half_tile, b4_pos[1] + half_tile], "A4_Top"),
            
            # รั้วขวา B5-B4
            ([b5_pos[0] + half_tile, b5_pos[1] + half_tile], 
             [b4_pos[0] + half_tile, b4_pos[1] - half_tile], "B5_B4_Right"),
            
            # รั้วซ้าย B5
            ([b4_pos[0] - half_tile, b4_pos[1] + half_tile], 
             [b4_pos[0] - half_tile, b5_pos[1] + half_tile], "B5_Left"),
            
            # รั้วบน B5
            ([b4_pos[0] - half_tile, b5_pos[1] + half_tile], 
             [b5_pos[0] + half_tile, b5_pos[1] + half_tile], "B5_Top"),
            
            # รั้วล่าง B4-B3
            ([b4_pos[0] + half_tile, b4_pos[1] - half_tile], 
             [b3_pos[0] + half_tile, b3_pos[1] - half_tile], "B4_B3_Bottom"),
            
            ([a3_pos[0] + half_tile, a3_pos[1] - half_tile], 
             [a4_pos[0] + half_tile, a4_pos[1] - half_tile], "A3_Right"),
            
            ([b3_pos[0] - half_tile, b3_pos[1] - half_tile], 
             [b4_pos[0] - half_tile, b4_pos[1] - half_tile], "B3_Left"),
            
            # รั้วบน B3 (ไปหา A3)
            ([a4_pos[0] + half_tile, a4_pos[1] - half_tile], 
             [b4_pos[0] - half_tile, b4_pos[1] - half_tile], "B3_A3_Top"),
            
            # รั้วซ้าย A3 (ส่วนที่ปิด)
            ([a3_pos[0] - half_tile, a3_pos[1] + half_tile], 
             [a3_pos[0] - half_tile, a3_pos[1] - half_tile], "A3_Left"),
        ]
        
        # สร้างรั้วแต่ละส่วน
        for start_pos, end_pos, name in fence_segments:
            self.create_boundary_wall(start_pos, end_pos, height=0.1, name=name)
        
        print("🟢 Created livestock fence (shaped boundary)")


    def create_movable_ping_pong_area(self, anchor_grid_x, anchor_grid_y):
        """สร้างสนามปิงปองโดยใช้ฟิกแล้วย้าย - ไม่รวมกลุ่ม"""
        print(f"🏓 Creating movable ping pong area at {chr(65+anchor_grid_x)}{anchor_grid_y+1}")
        
        # บันทึก field_objects เดิม
        old_count = len(self.field_objects)
        
        # สร้างสนามฟิกที่ A4 (0,3)
        self.create_ping_pong_boundaries()
        
        # ดูรั้วที่เพิ่งสร้างใหม่
        new_fences = self.field_objects[old_count:]
        
        # คำนวณการเลื่อน
        original_pos = self.grid_to_position(0, 3)  # A4
        new_pos = self.grid_to_position(anchor_grid_x, anchor_grid_y)
        
        offset_x = new_pos[0] - original_pos[0]
        offset_y = new_pos[1] - original_pos[1]
        
        # ย้ายรั้วแต่ละชิ้น
        for fence in new_fences:
            if fence.get('type') == 'boundary_wall':
                # ดึงตำแหน่งปัจจุบัน
                current_pos = self.sim.getObjectPosition(fence['handle'], -1)
                
                # ย้ายตำแหน่งใหม่
                new_fence_pos = [
                    current_pos[0] + offset_x,
                    current_pos[1] + offset_y,
                    current_pos[2]
                ]
                
                self.sim.setObjectPosition(fence['handle'], -1, new_fence_pos)
        
        print(f"✅ Moved {len(new_fences)} fence pieces to new position")
        return new_fences


    # ===============================================================
    # SECTION 8: COMPLETE FIELD CREATION
    # ===============================================================
    
    def create_complete_field(self):
        """สร้างสนามแข่งขันครบถ้วนตามแผนภาพ"""
        print("🏗️ Creating complete Drone Odyssey Challenge field...")
        
        # ล้างสนามก่อน
        self.clear_field()

        #  ตั้งค่า physics ก่อนสร้างวัตถุ
        self.diagnose_and_fix_physics_issues()

        # 1. สร้างพื้นสนาม
        self.create_tiled_floor()
        
        # 2. สร้างป้ายสีฟ้า (ความสูง 120 ซม. - fixed)
        print("🔵 Creating blue signs (120cm height, facing center)...")
        self.create_edge_image_stand(1, 0, 120)  # B1
        self.create_edge_image_stand(3, 0, 120)  # D1
        self.create_edge_image_stand(4, 1, 120)  # E2
        self.create_edge_image_stand(4, 3, 120)  # E4
        
        # 3-6. ส่วนอื่นๆ เหมือนเดิม...
        print("🩷 Creating brown boxes (60×60×80 cm)...")
        self.create_obstacle_box(1, 1)  # B2
        self.create_obstacle_box(2, 2)  # C3
        self.create_obstacle_box(3, 3)  # D4
        self.create_obstacle_box(4, 4)  # E5
        
        print("🟡 Creating yellow box (60×60×160 cm)...")
        self.create_adjustable_obstacle(3, 1, height_multiplier=2, name="YellowBox_D2")  # D2
        
        print("🟢 Creating green fence (ping pong boundary)...")
        self.create_livestock_fence_from_diagram()
     
         # รอให้ physics เสถียร
        time.sleep(1.5)

        # 6. สร้างลูกปิงปอง
        print("🏓 Creating ping pong balls...")
        self.create_ping_pong_in_fenced_area()
        
        # ✅ เพิ่มการตรวจสอบและแก้ไข
        self.check_ping_pong_visibility()
        
        print("✅ Complete field created successfully!")
        self.list_field_objects()
        
        print("✅ Complete field created successfully!")
        self.list_field_objects()

    def create_custom_field_with_heights(self, obstacle_config=None):
        """สร้างสนาม custom ที่ปรับความสูงสิ่งกีดขวางได้
        
        Args:
            obstacle_config: dict ของการตั้งค่าสิ่งกีดขวาง
            เช่น {'B2': 120, 'C3': 200, 'D4': 80}
        """
        print("🏗️ Creating custom field with adjustable obstacles...")
        
        # ล้างสนามก่อน
        self.clear_field()
        
        # 1. สร้างพื้นสนาม
        self.create_tiled_floor()
        
        # 2. สร้างป้ายสีฟ้า (เหมือนเดิม)
        print("🔵 Creating blue signs (facing center)...")
        self.create_edge_image_stand(1, 0)  # B1
        self.create_edge_image_stand(3, 0)  # D1
        self.create_edge_image_stand(4, 1)  # E2
        self.create_edge_image_stand(4, 3)  # E4
        
        # 3. สร้างสิ่งกีดขวางตามการตั้งค่า
        if obstacle_config is None:
            # ค่าเริ่มต้น
            obstacle_config = {
                'B2': 80,   # B2 สูง 80 cm
                'C3': 120,  # C3 สูง 120 cm
                'D4': 160,  # D4 สูง 160 cm
                'E5': 240   # E5 สูง 240 cm (สูงสุด)
            }
        
        print("📦 Creating custom obstacles with heights...")
        for grid_name, height in obstacle_config.items():
            grid_x = ord(grid_name[0]) - 65  # A=0, B=1, C=2, ...
            grid_y = int(grid_name[1:]) - 1  # 1=0, 2=1, 3=2, ...
            
            self.create_custom_obstacle(grid_x, grid_y, height)
        
        # 4. สร้างรั้วและลูกปิงปอง (เหมือนเดิม)
        print("🟢 Creating green fence...")
        self.create_livestock_fence_from_diagram()
        
        print("🏓 Creating ping pong balls...")
        self.create_ping_pong_in_fenced_area()
        
        print("✅ Custom field created successfully!")
        self.list_field_objects()

    def create_interactive_custom_field(self):
        """สร้างสนาม custom แบบ interactive - ใช้เฉพาะ compound object"""
        print("🎨 Interactive Custom Field Creator")
        print("=" * 50)
        
        # ล้างสนามก่อน
        self.clear_field()
        
        # 1. สร้างพื้นสนาม
        self.create_tiled_floor()
        
        # 2. สร้างป้ายสีฟ้า
        self.create_interactive_signs()
        
        # 3. สร้างสิ่งกีดขวาง
        self.create_interactive_obstacles()
        
        # 4. สร้างสนามปิงปอง compound object
        print("\n🏓 สร้างสนามปิงปอง (Compound Object)")
        print("=" * 40)
        
        # แสดงตำแหน่งที่วางได้
        print("📍 ตำแหน่งที่สามารถวางได้:")
        print("   1  2  3  4  5")
        for i in range(5):
            line = f"{chr(65+i)}  "
            for j in range(5):
                # ตรวจสอบพื้นที่ 3×2 สำหรับรูปเลข 4 กลับด้าน
                can_place = (i + 2 < 5 and j + 1 < 5)
                line += "🟢 " if can_place else "❌ "
            print(line)
        
        # ถามตำแหน่งที่ต้องการ
        while True:
            position = input("\nตำแหน่งมุมล่างซ้าย (A4) ของสนามปิงปอง: ").strip().upper()
            
            if len(position) != 2 or position[0] not in 'ABCDE' or position[1] not in '12345':
                print("❌ รูปแบบไม่ถูกต้อง")
                continue
            
            grid_x = ord(position[0]) - ord('A')
            grid_y = int(position[1]) - 1
            
            if grid_x + 2 >= 5 or grid_y + 1 >= 5:
                print("❌ ไม่สามารถวางได้ - เกินขอบสนาม")
                continue
            
            # สร้างสนามปิงปอง compound object
            result = self.create_movable_ping_pong_area(grid_x, grid_y)
            if result:
                print(f"✅ สร้างสนามปิงปองที่ {position} เสร็จสิ้น!")
                break
        
        print("✅ Interactive custom field created successfully!")
        self.list_field_objects()

    def create_interactive_obstacles(self):
        """สร้างสิ่งกีดขวางแบบ interactive"""
        print("\n📦 OBSTACLE CREATION")
        print("=" * 30)
        
        # ถามจำนวนสิ่งกีดขวาง
        while True:
            try:
                num_obstacles = int(input("จำนวนสิ่งกีดขวางที่ต้องการ (1-10): "))
                if 1 <= num_obstacles <= 10:
                    break
                else:
                    print("❌ กรุณาใส่จำนวน 1-10")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลข")
        
        # แสดงตารางตำแหน่งที่ใช้ได้
        print("\n📍 ตำแหน่งที่สามารถวางได้:")
        print("   1  2  3  4  5")
        for i in range(5):
            line = f"{chr(65+i)}  "
            for j in range(5):
                pos = f"{chr(65+i)}{j+1}"
                # ตรวจสอบตำแหน่งที่ไม่ควรวาง
                if pos in ['B1', 'D1', 'E2', 'E4']:  # ป้ายสีฟ้า
                    line += "🔵 "
                elif pos in ['A3', 'A4', 'A5', 'B3', 'B4', 'B5']:  # พื้นที่ปิงปอง
                    line += "🏓 "
                else:
                    line += "⬜ "
            print(line)
        
        print("\n🔵 = ป้ายสีฟ้า (ห้ามวาง)")
        print("🏓 = พื้นที่ปิงปอง (ห้ามวาง)")
        print("⬜ = วางได้")
        
        # วนลูปถามรายละเอียดแต่ละสิ่งกีดขวาง
        created_obstacles = []
        used_positions = set()
        
        for i in range(num_obstacles):
            print(f"\n--- สิ่งกีดขวางที่ {i+1} ---")
            
            # ถามตำแหน่ง
            while True:
                position = input(f"ตำแหน่ง (เช่น A1, B2, C3): ").strip().upper()
                
                # ตรวจสอบรูปแบบ
                if len(position) != 2 or position[0] not in 'ABCDE' or position[1] not in '12345':
                    print("❌ รูปแบบไม่ถูกต้อง ใช้ A1-E5")
                    continue
                
                # ตรวจสอบตำแหน่งที่ห้ามวาง
                if position in ['B1', 'D1', 'E2', 'E4']:
                    print("❌ ตำแหน่งนี้มีป้ายสีฟ้าแล้ว")
                    continue
                
                if position in ['A3', 'A4', 'A5', 'B3', 'B4', 'B5']:
                    print("❌ ตำแหน่งนี้เป็นพื้นที่ปิงปอง")
                    continue
                
                # ตรวจสอบตำแหน่งซ้ำ
                if position in used_positions:
                    print("❌ ตำแหน่งนี้ถูกใช้แล้ว")
                    continue
                
                used_positions.add(position)
                break
            
            # ถามความสูง
            while True:
                try:
                    height = int(input(f"ความสูง (60-240 ซม.): "))
                    if 60 <= height <= 240:
                        break
                    else:
                        print("❌ ความสูงต้องอยู่ระหว่าง 60-240 ซม.")
                except ValueError:
                    print("❌ กรุณาใส่ตัวเลข")
            
            # แปลงตำแหน่งเป็น grid
            grid_x = ord(position[0]) - ord('A')
            grid_y = int(position[1]) - 1
            
            # สร้างสิ่งกีดขวาง
            obstacle = self.create_custom_obstacle(grid_x, grid_y, height)
            if obstacle:
                created_obstacles.append(obstacle)
                print(f"✅ สร้างสิ่งกีดขวางที่ {position} สูง {height} ซม.")
            else:
                print(f"❌ ไม่สามารถสร้างสิ่งกีดขวางที่ {position} ได้")
        
        print(f"\n🎉 สร้างสิ่งกีดขวาง {len(created_obstacles)} ชิ้นเสร็จสิ้น!")
        return created_obstacles

    def create_interactive_signs(self):
        """สร้างป้ายแบบ interactive"""
        print("\n🖼️ SIGN CREATION")
        print("=" * 30)
        
        # ตำแหน่งป้ายที่แนะนำ
        recommended_positions = ['B1', 'D1', 'E2', 'E4']
        
        print("ตำแหน่งป้ายแนะนำ: B1, D1, E2, E4")
        
        while True:
            try:
                use_recommended = input("ใช้ตำแหน่งแนะนำ? (y/n): ").strip().lower()
                if use_recommended in ['y', 'yes']:
                    positions = recommended_positions
                    break
                elif use_recommended in ['n', 'no']:
                    # ให้ผู้ใช้เลือกเอง
                    positions = []
                    while True:
                        pos = input("ตำแหน่งป้าย (หรือ 'done' เพื่อจบ): ").strip().upper()
                        if pos == 'DONE':
                            break
                        if len(pos) == 2 and pos[0] in 'ABCDE' and pos[1] in '12345':
                            positions.append(pos)
                        else:
                            print("❌ รูปแบบไม่ถูกต้อง")
                    break
                else:
                    print("❌ กรุณาตอบ y หรือ n")
            except:
                print("❌ กรุณาตอบ y หรือ n")
        
        # ถามความสูงป้าย
        while True:
            try:
                height = int(input("ความสูงป้าย (80-200 ซม.): "))
                if 80 <= height <= 200:
                    break
                else:
                    print("❌ ความสูงต้องอยู่ระหว่าง 80-200 ซม.")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลข")
        
        # สร้างป้าย
        created_signs = []
        for pos in positions:
            grid_x = ord(pos[0]) - ord('A')
            grid_y = int(pos[1]) - 1
            
            sign = self.create_edge_image_stand(grid_x, grid_y, height)
            if sign:
                created_signs.append(sign)
                print(f"✅ สร้างป้ายที่ {pos} สูง {height} ซม.")
        
        return created_signs

    def create_interactive_ping_pong_area(self):
        """สร้างสนามปิงปองแบบ interactive - ใช้โค้ดฟิกที่แก้ไขแล้ว"""
        print("\n🏓 PING PONG AREA CREATION")
        print("=" * 35)
        
        # แสดงตำแหน่งที่วางได้
        print("📍 ตำแหน่งที่สามารถวางได้:")
        print("   1  2  3  4  5")
        for i in range(5):
            line = f"{chr(65+i)}  "
            for j in range(5):
                can_place = (i + 2 < 5 and j + 1 < 5)
                line += "🟢 " if can_place else "❌ "
            print(line)
        
        # ถามตำแหน่งที่ต้องการ
        while True:
            position = input("\nตำแหน่งมุมล่างซ้าย (A4) ของสนามปิงปอง: ").strip().upper()
            
            if len(position) != 2 or position[0] not in 'ABCDE' or position[1] not in '12345':
                print("❌ รูปแบบไม่ถูกต้อง")
                continue
            
            grid_x = ord(position[0]) - ord('A')
            grid_y = int(position[1]) - 1
            
            if grid_x + 2 >= 5 or grid_y + 1 >= 5:
                print("❌ ไม่สามารถวางได้ - เกินขอบสนาม")
                continue
            
            # สร้างสนามปิงปอง compound object
            result = self.create_ping_pong_compound_object(grid_x, grid_y)
            if result:
                print(f"✅ สร้างสนามปิงปองที่ {position} เสร็จสิ้น!")
                return result
            else:
                print("❌ ไม่สามารถสร้างสนามปิงปองได้")

    # ===============================================================
    # SECTION 9: LEGACY FUNCTIONS (สำหรับความเข้ากันได้)
    # ===============================================================
    
    def create_field_from_diagram(self):
        """สร้างสนามตามแผนภาพที่แนบมา (เหมือน create_complete_field)"""
        return self.create_complete_field()

# ===============================================================
# MAIN PROGRAM
# ===============================================================

def quick_create_mode():
    """โหมดสร้างเร็ว"""
    print("⚡ Quick Field Create Mode")
    print("Select field type:")
    print("1. Complete field (fixed heights)")
    print("2. Interactive custom field (ask for details)")
    print("3. Field base only")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    creator = DroneOdysseyFieldCreator()
    
    if choice in ["1", "2", "3"]:
        if creator.start_simulation():
            time.sleep(1)
            
            if choice == "1":
                creator.create_complete_field()
            elif choice == "2":
                creator.create_interactive_custom_field()  # ฟังก์ชันใหม่
            elif choice == "3":
                creator.create_tiled_floor()
            
            print("\n✅ Field created successfully!")
            print("💡 Use your drone controller to test missions")
            print("🛑 Field will remain until you stop the simulation")
            
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    print("🏟️ Drone Odyssey Challenge Field Creator (Organized)")
    print("=" * 70)
    print("🔧 Fixed: AttributeError, Texture Error, Board orientation, Wind physics")
    print("🏓 Layout: B1,D1,E2,E4=Blue Signs | B2,C3,D4,E5=Brown Boxes | D2=Yellow Box")
    print("🟢 Ping Pong: A3,A4,A5,B3,B4,B5 in L-shaped fence")
    print("=" * 70)
    
    quick_create_mode()
