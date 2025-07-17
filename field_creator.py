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
        self.image_texture_path=r".\testpicture.png"
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

    def reinforce_boundary_walls(self):
        """เสริมกำลังกำแพงหลังสร้างเสร็จแล้ว"""
        print("🔧 เสริมกำลังกำแพงป้องกันการทะลุ...")
        
        wall_count = 0
        for obj in self.field_objects:
            if obj.get('type') == 'boundary_wall':
                wall_handle = obj['handle']
                wall_name = obj['name']
                
                try:
                    # ✅ ตั้งค่าใหม่ให้แน่ใจ
                    self.sim.setObjectInt32Parameter(wall_handle, self.sim.shapeintparam_static, 1)
                    self.sim.setObjectInt32Parameter(wall_handle, self.sim.shapeintparam_respondable, 1)
                    
                    # ✅ เพิ่มมวลให้มากขึ้นอีก
                    self.sim.setShapeMass(wall_handle, 20000.0)
                    
                    # ✅ ตั้งค่าพารามิเตอร์ฟิสิกส์เพิ่มเติม
                    try:
                        # ตั้งค่าให้กำแพงไม่ยืดหยุ่น (แข็ง)
                        self.sim.setEngineFloatParam(3007, wall_handle, 1.0)  # friction สูงสุด
                        self.sim.setEngineFloatParam(3008, wall_handle, 0.1)  # restitution ต่ำ (ไม่เด้ง)
                    except:
                        pass
                    
                    wall_count += 1
                    print(f"  ✅ เสริมกำลัง: {wall_name}")
                    
                except Exception as e:
                    print(f"  ❌ ไม่สามารถเสริมกำลัง {wall_name}: {e}")
        
        print(f"🛡️ เสริมกำลังกำแพง {wall_count} ชิ้นเสร็จสิ้น")
        
        # รอให้ physics engine ประมวลผล
        time.sleep(0.5)

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
    def create_custom_ping_pong_balls(self, grid_x, grid_y, ball_config):
        """สร้างลูกปิงปองที่ปรับแต่งได้สำหรับ custom field
        
        Args:
            grid_x, grid_y: ตำแหน่ง grid
            ball_config: dict ที่มีการตั้งค่า
            {
                'count': 7,           # จำนวนลูก (1-10)
                'size': 40,           # ขนาด mm (30-50)
                'mass': 2.7,          # มวล g (1.0-5.0)
                'color': 'orange',    # สี
                'pattern': 'circle',  # รูปแบบการจัด
                'wind_sensitive': True, # ตอบสนองลม
                'bounce': 0.8         # ค่าการเด้ง (0.0-1.0)
            }
        """
        print(f"🏓 Creating custom ping pong balls at {chr(65+grid_x)}{grid_y+1}")
        
        # ค่าเริ่มต้น
        default_config = {
            'count': 7,
            'size': 40,
            'mass': 2.7,
            'color': 'orange',
            'pattern': 'circle',
            'wind_sensitive': True,
            'bounce': 0.8
        }
        
        # รวมการตั้งค่า
        config = {**default_config, **ball_config}
        
        # ตำแหน่งกลางของช่อง
        center_pos = self.grid_to_position(grid_x, grid_y)
        
        # เลือกรูปแบบการจัด
        if config['pattern'] == 'circle':
            positions = self.get_circle_pattern(config['count'])
        elif config['pattern'] == 'line':
            positions = self.get_line_pattern(config['count'])
        elif config['pattern'] == 'random':
            positions = self.get_random_pattern(config['count'])
        else:
            positions = self.get_grid_pattern(config['count'])
        
        created_balls = []
        
        for i, (offset_x, offset_y) in enumerate(positions):
            ball_pos = [
                center_pos[0] + offset_x,
                center_pos[1] + offset_y,
                0.03  # ความสูงเริ่มต้น
            ]
            
            name = f"CustomPingPong_{chr(65+grid_x)}{grid_y+1}_{i+1}"
            
            # สร้างลูกปิงปองที่ปรับแต่งได้
            ball = self.create_customizable_ping_pong_ball(ball_pos, name, config)
            
            if ball:
                ball_info = {
                    'type': 'custom_ping_pong',
                    'handle': ball,
                    'name': name,
                    'grid': f"{chr(65+grid_x)}{grid_y+1}",
                    'position': ball_pos,
                    'config': config
                }
                
                self.field_objects.append(ball_info)
                created_balls.append(ball_info)
        
        print(f"✅ Created {len(created_balls)} custom ping pong balls")
        return created_balls

    def create_customizable_ping_pong_ball(self, position, name, config):
        """สร้างลูกปิงปองที่ปรับแต่งได้"""
        
        # แปลงขนาดจาก mm เป็น m
        diameter = config['size'] / 1000.0
        
        # แปลงมวลจาก g เป็น kg
        mass = config['mass'] / 1000.0
        
        # สร้าง sphere
        ball = self.sim.createPrimitiveShape(
            self.sim.primitiveshape_spheroid,
            [diameter, diameter, diameter]
        )
        
        if ball == -1:
            return None
        
        # ตั้งชื่อและตำแหน่ง
        self.sim.setObjectAlias(ball, name)
        self.sim.setObjectPosition(ball, -1, position)
        
        # ตั้งสี
        color = self.get_ball_color(config['color'])
        self.sim.setShapeColor(ball, None,
            self.sim.colorcomponent_ambient_diffuse, color)
        
        # ตั้งค่ามวล
        self.sim.setShapeMass(ball, mass)
        
        # ตั้งค่าฟิสิกส์
        self.sim.setObjectInt32Parameter(ball, self.sim.shapeintparam_static, 0)
        self.sim.setObjectInt32Parameter(ball, self.sim.shapeintparam_respondable, 1)
        
        # ตั้งค่าการเด้ง
        try:
            self.sim.setEngineFloatParam(3007, ball, 0.5)  # friction
            self.sim.setEngineFloatParam(3008, ball, config['bounce'])  # restitution
        except:
            pass
        
        # ตั้งค่า wind sensitivity
        if config['wind_sensitive']:
            # ลดมวลให้เบาขึ้นเพื่อตอบสนองลม
            adjusted_mass = mass * 0.5
            self.sim.setShapeMass(ball, adjusted_mass)
        
        print(f"✅ Created custom ball: {name} (D={config['size']}mm, M={config['mass']}g)")
        return ball

    def get_circle_pattern(self, count):
        """รูปแบบวงกลม"""
        import math
        positions = []
        radius = 0.12  # รัศมี 12 cm
        
        for i in range(count):
            angle = 2 * math.pi * i / count
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions.append([x, y])
        
        return positions

    def get_line_pattern(self, count):
        """รูปแบบเส้นตรง"""
        positions = []
        spacing = 0.08  # ระยะห่าง 8 cm
        
        for i in range(count):
            x = (i - count/2) * spacing
            y = 0
            positions.append([x, y])
        
        return positions

    def get_random_pattern(self, count):
        """รูปแบบสุ่ม"""
        import random
        positions = []
        
        for i in range(count):
            x = random.uniform(-0.15, 0.15)
            y = random.uniform(-0.15, 0.15)
            positions.append([x, y])
        
        return positions

    def get_grid_pattern(self, count):
        """รูปแบบตาราง"""
        positions = []
        
        # คำนวณจำนวนแถวและคอลัมน์
        import math
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        
        spacing = 0.08
        
        for i in range(count):
            row = i // cols
            col = i % cols
            
            x = (col - cols/2) * spacing
            y = (row - rows/2) * spacing
            positions.append([x, y])
        
        return positions

    def get_ball_color(self, color_name):
        """แปลงชื่อสีเป็น RGB"""
        colors = {
            'orange': [1.0, 0.5, 0.0],
            'white': [1.0, 1.0, 1.0],
            'yellow': [1.0, 1.0, 0.0],
            'red': [1.0, 0.0, 0.0],
            'blue': [0.0, 0.0, 1.0],
            'green': [0.0, 1.0, 0.0],
            'pink': [1.0, 0.0, 1.0]
        }
        
        return colors.get(color_name, [1.0, 0.5, 0.0])  # default = orange

    def get_custom_ping_pong_config(self):
        """รับการตั้งค่าลูกปิงปองจากผู้ใช้ - เพิ่มการเลือกช่อง"""
        print("\n🏓 CUSTOM PING PONG CONFIGURATION")
        print("=" * 40)
        
        config = {}
        
        # เพิ่มส่วนเลือกช่องที่ต้องการ
        print("📍 เลือกช่องที่ต้องการวางลูกปิงปอง:")
        print("   1  2  3  4  5")
        for i in range(5):
            line = f"{chr(65+i)}  "
            for j in range(5):
                pos = f"{chr(65+i)}{j+1}"
                # ตรวจสอบช่องที่ใช้ได้
                if pos in ['B1', 'D1', 'E2', 'E4']:  # ป้ายสีฟ้า
                    line += "🔵 "
                elif pos in ['B2', 'C3', 'D4', 'E5']:  # สิ่งกีดขวาง
                    line += "📦 "
                elif pos in ['D2']:  # กล่องเหลือง
                    line += "🟡 "
                else:
                    line += "⬜ "
            print(line)
        
        print("\n🔵 = ป้ายสีฟ้า | 📦 = สิ่งกีดขวาง | 🟡 = กล่องเหลือง | ⬜ = วางได้")
        
        # ถามช่องที่ต้องการ
        while True:
            grid_position = input("\nเลือกช่องที่ต้องการ (เช่น A1, A2, C1): ").strip().upper()
            
            if len(grid_position) != 2 or grid_position[0] not in 'ABCDE' or grid_position[1] not in '12345':
                print("❌ รูปแบบไม่ถูกต้อง ใช้ A1-E5")
                continue
            
            # ตรวจสอบว่าช่องนี้ใช้ได้หรือไม่
            if grid_position in ['B1', 'D1', 'E2', 'E4']:
                print("❌ ช่องนี้มีป้ายสีฟ้าแล้ว")
                continue
            elif grid_position in ['B2', 'C3', 'D4', 'E5']:
                print("❌ ช่องนี้มีสิ่งกีดขวางแล้ว")
                continue
            elif grid_position in ['D2']:
                print("❌ ช่องนี้มีกล่องเหลืองแล้ว")
                continue
            
            config['grid_position'] = grid_position
            break
        
        # จำนวนลูก
        while True:
            try:
                count = int(input("จำนวนลูกปิงปอง (1-10): "))
                if 1 <= count <= 10:
                    config['count'] = count
                    break
                else:
                    print("❌ จำนวนต้องอยู่ระหว่าง 1-10")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลข")
        
        # ขนาดลูก
        while True:
            try:
                size = int(input("ขนาดลูก (30-50 mm): "))
                if 30 <= size <= 50:
                    config['size'] = size
                    break
                else:
                    print("❌ ขนาดต้องอยู่ระหว่าง 30-50 mm")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลข")
        
        # มวลลูก
        while True:
            try:
                mass = float(input("มวลลูก (1.0-5.0 g): "))
                if 1.0 <= mass <= 5.0:
                    config['mass'] = mass
                    break
                else:
                    print("❌ มวลต้องอยู่ระหว่าง 1.0-5.0 g")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลข")
        
        # สี
        print("\nสีที่ใช้ได้: orange, white, yellow, red, blue, green, pink")
        color = input("สีลูกปิงปอง (orange): ").strip().lower()
        config['color'] = color if color else 'orange'
        
        # รูปแบบการจัด
        print("\nรูปแบบการจัด:")
        print("1. circle (วงกลม)")
        print("2. line (เส้นตรง)")
        print("3. grid (ตาราง)")
        print("4. random (สุ่ม)")
        
        while True:
            pattern_choice = input("เลือกรูปแบบ (1-4): ")
            patterns = {'1': 'circle', '2': 'line', '3': 'grid', '4': 'random'}
            if pattern_choice in patterns:
                config['pattern'] = patterns[pattern_choice]
                break
            else:
                print("❌ กรุณาเลือก 1-4")
        
        # ความไวต่อลม
        wind_sensitive = input("ตอบสนองลม? (y/n): ").strip().lower()
        config['wind_sensitive'] = wind_sensitive in ['y', 'yes']
        
        # ค่าการเด้ง
        while True:
            try:
                bounce = float(input("ค่าการเด้ง (0.0-1.0): "))
                if 0.0 <= bounce <= 1.0:
                    config['bounce'] = bounce
                    break
                else:
                    print("❌ ค่าต้องอยู่ระหว่าง 0.0-1.0")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลข")
        
        return config

    def get_multiple_ping_pong_config(self):
        """รับการตั้งค่าลูกปิงปองหลายช่อง"""
        print("\n🏓 MULTIPLE PING PONG CONFIGURATION")
        print("=" * 40)
        
        configs = []
        
        while True:
            print(f"\n--- การตั้งค่าช่องที่ {len(configs) + 1} ---")
            
            # ใช้ฟังก์ชันเดิม
            config = self.get_custom_ping_pong_config()
            configs.append(config)
            
            # ถามว่าต้องการเพิ่มช่องอื่นหรือไม่
            add_more = input("\nต้องการเพิ่มช่องอื่น? (y/n): ").strip().lower()
            if add_more not in ['y', 'yes']:
                break
        
        return configs

    def create_multiple_ping_pong_areas(self, configs):
        """สร้างลูกปิงปองหลายช่อง"""
        created_areas = []
        
        for i, config in enumerate(configs):
            grid_position = config['grid_position']
            grid_x = ord(grid_position[0]) - ord('A')
            grid_y = int(grid_position[1]) - 1
            
            print(f"\n🏓 Creating ping pong area {i+1} at {grid_position}")
            
            balls = self.create_custom_ping_pong_balls(grid_x, grid_y, config)
            created_areas.append({
                'position': grid_position,
                'balls': balls,
                'config': config
            })
        
        print(f"\n✅ Created {len(created_areas)} ping pong areas!")
        return created_areas


    def create_ping_pong_ball(self, position, name, ultra_sensitive=False):
        """สร้างลูกปิงปองที่ชนรั้วได้อย่างถูกต้อง"""
        
        # ข้อมูลจำเพาะ
        diameter = 0.04  # 4cm
        mass_real = 0.0027
        
        # สร้าง mesh shape (เหมือนเดิม)
        vertices = []
        indices = []
        
        import math
        radius = diameter / 2
        segments = 16
        
        # สร้าง vertices ของ sphere
        for i in range(segments):
            for j in range(segments):
                theta = 2 * math.pi * i / segments
                phi = math.pi * j / segments
                
                x = radius * math.sin(phi) * math.cos(theta)
                y = radius * math.sin(phi) * math.sin(theta)
                z = radius * math.cos(phi)
                
                vertices.extend([x, y, z])
        
        # สร้าง indices สำหรับ triangles
        for i in range(segments - 1):
            for j in range(segments - 1):
                p1 = i * segments + j
                p2 = (i + 1) * segments + j
                p3 = i * segments + (j + 1)
                p4 = (i + 1) * segments + (j + 1)
                
                indices.extend([p1, p2, p3])
                indices.extend([p2, p4, p3])
        
        # สร้าง mesh shape
        ball = self.sim.createMeshShape(2, 0, vertices, indices)
        
        if ball == -1:
            print(f"❌ ไม่สามารถสร้างลูกปิงปอง {name} ได้")
            return None
        
        # ตั้งชื่อและตำแหน่ง
        self.sim.setObjectAlias(ball, name)
        pos = position.copy()
        pos[2] = 0.05  # ลดความสูงเริ่มต้น
        self.sim.setObjectPosition(ball, -1, pos)
        
        # ตั้งสีส้มสด
        self.sim.setShapeColor(ball, None,
            self.sim.colorcomponent_ambient_diffuse, [1.0, 0.5, 0.0])
        
        # ตั้งค่ามวลและฟิสิกส์
        mass = 0.0005 if ultra_sensitive else mass_real
        self.sim.setShapeMass(ball, mass)
        
        # หน่วงเวลา
        time.sleep(0.1)
        
        # ตั้งค่าฟิสิกส์
        self.sim.setObjectInt32Parameter(ball, self.sim.shapeintparam_static, 0)
        self.sim.setObjectInt32Parameter(ball, self.sim.shapeintparam_respondable, 1)
        
        # ตั้งค่า inertia
        inertia = (2/5) * mass * radius**2
        inertia_matrix = [inertia, 0, 0, 0, inertia, 0, 0, 0, inertia]
        transform = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
        self.sim.setShapeInertia(ball, inertia_matrix, transform)
        
        # ✅ ปรับค่าฟิสิกส์เพื่อการชนที่ดีกว่า
        try:
            self.sim.setEngineFloatParam(3007, ball, 0.5)   # เพิ่ม friction
            self.sim.setEngineFloatParam(3008, ball, 0.8)   # เพิ่ม restitution (การเด้ง)
        except:
            pass
        
        # หน่วงเวลาก่อน reset
        time.sleep(0.1)
        self.sim.resetDynamicObject(ball)
        
        print(f"✅ สร้างลูกปิงปอง {name} สำเร็จ (ขนาด: {diameter}m, mesh)")
        return ball

    def verify_ping_pong_shape_type(self):
        """ตรวจสอบประเภทของ Shape ว่าเป็น Sphere จริงหรือไม่"""
        print("🔍 ตรวจสอบประเภท Shape ของลูกปิงปอง...")
        
        for obj in self.field_objects:
            if obj.get('type') == 'wind_responsive_a3':
                ball_handle = obj['handle']
                ball_name = obj['name']
                
                try:
                    # ดึงข้อมูล mesh
                    vertices, indices, normals = self.sim.getShapeMesh(ball_handle)
                    vertex_count = len(vertices) // 3
                    
                    # ตรวจสอบตำแหน่ง
                    pos = self.sim.getObjectPosition(ball_handle, -1)
                    
                    print(f"🏓 {ball_name}:")
                    print(f"   Vertices: {vertex_count}")
                    print(f"   Position: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
                    
                    # วิเคราะห์ประเภท Shape
                    if vertex_count < 10:
                        print(f"   ❌ เป็น Plane หรือ Simple Shape (vertices < 10)")
                        return False
                    elif vertex_count < 50:
                        print(f"   ⚠️ อาจเป็น Low-poly Shape")
                        return False
                    else:
                        print(f"   ✅ เป็น Sphere ที่ถูกต้อง")
                        return True
                        
                except Exception as e:
                    print(f"   ❌ ไม่สามารถตรวจสอบได้: {e}")
                    return False
        
        return False

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
        """แก้ไขลูกปิงปองที่เป็น Plane ให้เป็น Sphere"""
        print("🔍 ตรวจสอบและแก้ไขลูกปิงปองทั้งหมด...")
        
        ping_pong_balls = []
        for obj in self.field_objects:
            if obj.get('type') == 'wind_responsive_a3':
                ping_pong_balls.append(obj)
        
        if not ping_pong_balls:
            print("❌ ไม่พบลูกปิงปอง")
            return
        
        # ตรวจสอบประเภท Shape ก่อน
        is_sphere = self.verify_ping_pong_shape_type()
        
        if not is_sphere:
            print("🔧 พบ Plane แทน Sphere - กำลังสร้างใหม่...")
            
            for ball_info in ping_pong_balls:
                ball_handle = ball_info['handle']
                ball_name = ball_info['name']
                
                try:
                    # ลบวัตถุเก่า
                    self.sim.removeObjects([ball_handle])
                    print(f"🗑️ ลบ Plane {ball_name}")
                    
                    # สร้าง Sphere ใหม่
                    new_position = ball_info['position']
                    new_ball = self.create_ping_pong_ball(new_position, ball_name, False)
                    
                    if new_ball:
                        ball_info['handle'] = new_ball
                        print(f"✅ สร้าง Sphere {ball_name} ใหม่สำเร็จ")
                    else:
                        print(f"❌ ไม่สามารถสร้าง Sphere {ball_name} ได้")
                        
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาดกับ {ball_name}: {e}")
        
        # ตรวจสอบอีกครั้งหลังแก้ไข
        time.sleep(1.0)
        self.verify_ping_pong_shape_type()

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
        """สร้างรั้วสีเขียวตามแผนภาพ - เวอร์ชันป้องกันการทะลุ"""
        # คำนวณตำแหน่งของแต่ละ grid
        a3_pos = self.grid_to_position(0, 2)  # A3
        a4_pos = self.grid_to_position(0, 3)  # A4
        b3_pos = self.grid_to_position(1, 2)  # B3
        b4_pos = self.grid_to_position(1, 3)  # B4
        b5_pos = self.grid_to_position(1, 4)  # B5
        
        half_tile = self.tile_size / 2
        
        # ✅ เพิ่มความสูงรั้วเป็น 10cm
        fence_height = 0.1
        
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
        
        # สร้างรั้วแต่ละส่วนด้วยความสูงและความหนาใหม่
        for start_pos, end_pos, name in fence_segments:
            self.create_boundary_wall(start_pos, end_pos, height=fence_height, name=name)
        
        print(f"🟢 Created livestock fence (shaped boundary) - Height: {fence_height*100:.0f}cm, Thickness: 18cm")

    def check_ping_pong_containment(self):
        """ตรวจสอบว่าลูกปิงปองอยู่ในรั้วหรือไม่"""
        print("🔍 ตรวจสอบการอยู่ในรั้วของลูกปิงปอง...")
        
        # ขอบเขตของพื้นที่รั้ว A3 (ประมาณ)
        a3_pos = self.grid_to_position(0, 2)
        half_tile = self.tile_size / 2
        
        # กำหนดขอบเขตที่ปลอดภัย (ห่างจากรั้ว 5cm)
        safe_margin = 0.05
        bounds = {
            'min_x': a3_pos[0] - half_tile + safe_margin,
            'max_x': a3_pos[0] + half_tile - safe_margin,
            'min_y': a3_pos[1] - half_tile + safe_margin,
            'max_y': a3_pos[1] + half_tile - safe_margin,
            'min_z': 0.01,
            'max_z': 0.35  # ความสูงสูงสุดที่ปลอดภัย
        }
        
        escaped_balls = []
        
        for obj in self.field_objects:
            if obj.get('type') == 'wind_responsive_a3':
                ball_handle = obj['handle']
                ball_name = obj['name']
                
                try:
                    pos = self.sim.getObjectPosition(ball_handle, -1)
                    
                    # ตรวจสอบว่าอยู่ในขอบเขตหรือไม่
                    if (pos[0] < bounds['min_x'] or pos[0] > bounds['max_x'] or
                        pos[1] < bounds['min_y'] or pos[1] > bounds['max_y'] or
                        pos[2] < bounds['min_z'] or pos[2] > bounds['max_z']):
                        
                        escaped_balls.append({
                            'name': ball_name,
                            'handle': ball_handle,
                            'position': pos
                        })
                        print(f"⚠️ {ball_name} อยู่นอกขอบเขต: {pos}")
                    else:
                        print(f"✅ {ball_name} อยู่ในขอบเขตปลอดภัย")
                        
                except Exception as e:
                    print(f"❌ ไม่สามารถตรวจสอบ {ball_name}: {e}")
        
        if escaped_balls:
            print(f"🚨 พบลูกปิงปอง {len(escaped_balls)} ลูกอยู่นอกขอบเขต")
            return escaped_balls
        else:
            print("🎉 ลูกปิงปองทั้งหมดอยู่ในขอบเขตปลอดภัย")
            return []

    def reset_escaped_balls(self, escaped_balls):
        """นำลูกปิงปองที่หลุดกลับมาในขอบเขต"""
        print("🔄 กำลังนำลูกปิงปองกลับเข้าขอบเขต...")
        
        a3_pos = self.grid_to_position(0, 2)
        
        for ball_info in escaped_balls:
            # ตำแหน่งใหม่ในกลางช่อง A3
            new_pos = [a3_pos[0], a3_pos[1], 0.1]
            
            self.sim.setObjectPosition(ball_info['handle'], -1, new_pos)
            
            # หยุดการเคลื่อนที่
            self.sim.setObjectFloatParameter(ball_info['handle'], self.sim.shapefloatparam_init_velocity_x, 0)
            self.sim.setObjectFloatParameter(ball_info['handle'], self.sim.shapefloatparam_init_velocity_y, 0)
            self.sim.setObjectFloatParameter(ball_info['handle'], self.sim.shapefloatparam_init_velocity_z, 0)
            
            self.sim.resetDynamicObject(ball_info['handle'])
            
            print(f"✅ นำ {ball_info['name']} กลับเข้าขอบเขตแล้ว")
        
    def create_movable_ping_pong_area(self, anchor_grid_x, anchor_grid_y):
        """สร้างสนามปิงปองโดยใช้ฟิกแล้วย้าย - ไม่รวมกลุ่ม"""
        print(f"🏓 Creating movable ping pong area at {chr(65+anchor_grid_x)}{anchor_grid_y+1}")
        
        # บันทึก field_objects เดิม
        old_count = len(self.field_objects)
        
        # ✅ แก้ไขจาก create_ping_pong_boundaries() เป็น create_livestock_fence_from_diagram()
        self.create_livestock_fence_from_diagram()
        
        # ส่วนที่เหลือของโค้ดเหมือนเดิม...
        new_fences = self.field_objects[old_count:]
        
        # คำนวณการเลื่อน
        original_pos = self.grid_to_position(0, 3)  # A4
        new_pos = self.grid_to_position(anchor_grid_x, anchor_grid_y)
        
        offset_x = new_pos[0] - original_pos[0]
        offset_y = new_pos[1] - original_pos[1]
        
        # ย้ายรั้วแต่ละชิ้น
        for fence in new_fences:
            if fence.get('type') == 'boundary_wall':
                current_pos = self.sim.getObjectPosition(fence['handle'], -1)
                
                new_fence_pos = [
                    current_pos[0] + offset_x,
                    current_pos[1] + offset_y,
                    current_pos[2]
                ]
                
                self.sim.setObjectPosition(fence['handle'], -1, new_fence_pos)
        
        print(f"✅ Moved {len(new_fences)} fence pieces to new position")
        return new_fences

    # ===============================================================
    # SECTION 8: MISSON PAD MANAGEMENT
    # ===============================================================
    def load_obj_model_safe(self, obj_path, name):
        """โหลด .obj model พร้อมการตั้งค่าการหมุน"""
        try:
            if not os.path.exists(obj_path):
                print(f"❌ .obj file not found: {obj_path}")
                return None
            
            abs_path = os.path.abspath(obj_path)
            print(f"📦 Loading .obj with sim.importShape: {abs_path}")
            
            # โหลด shape
            shape_handle = self.sim.importShape(
                0,          # fileformat (0 = OBJ)
                abs_path,   # pathAndFilename
                0,          # options
                0.0001,     # identicalVerticeTolerance
                1.0         # scalingFactor
            )
            
            if shape_handle != -1:
                # ✅ เพิ่มการตั้งค่าการหมุนให้นอนราบ
                # หมุน 90 องศารอบแกน X เพื่อให้นอนราบ
                self.sim.setObjectOrientation(shape_handle, -1, [-1.5708, 0, 0])  # -90 degrees in radians
                
                print(f"✅ Successfully imported and rotated shape: {shape_handle}")
                return shape_handle
            else:
                print(f"❌ Failed to import shape")
                return None
                
        except Exception as e:
            print(f"❌ Exception with sim.importShape: {e}")
            return None
        
    def create_mission_pad(self, grid_x, grid_y, pad_number, name=None):
        """สร้าง Mission Pad โดยใช้ absolute path"""
        try:
            if name is None:
                name = f"MissionPad_{pad_number}_{chr(65+grid_x)}{grid_y+1}"
            
            # ใช้ absolute path
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            obj_path = os.path.join(current_dir, f"mission_{pad_number}.obj")
            
            # ตรวจสอบไฟล์ก่อนโหลด
            if os.path.exists(obj_path):
                print(f"📦 Loading .obj model: {obj_path}")
                pad_handle = self.load_obj_model(obj_path, name)
                
                # ✅ เพิ่มส่วนนี้ที่ขาดหายไป
                if pad_handle and pad_handle != -1:
                    # ตั้งตำแหน่ง
                    pos = self.grid_to_position(grid_x, grid_y)
                    pos.append(0.01)  # วางบนพื้น
                    
                    self.sim.setObjectPosition(pad_handle, -1, pos)
                    self.sim.setObjectAlias(pad_handle, name)
                    
                    # ตั้งค่าฟิสิกส์
                    self.sim.setObjectInt32Parameter(pad_handle, self.sim.shapeintparam_static, 1)
                    self.sim.setObjectInt32Parameter(pad_handle, self.sim.shapeintparam_respondable, 1)
                    
                    pad_info = {
                        'type': 'mission_pad',
                        'handle': pad_handle,
                        'name': name,
                        'grid': f"{chr(65+grid_x)}{grid_y+1}",
                        'position': pos,
                        'pad_number': pad_number,
                        'source': 'obj_model'
                    }
                    
                    self.field_objects.append(pad_info)
                    print(f"✅ Created Mission Pad {pad_number} from .obj: {name}")
                    return pad_info
                else:
                    print(f"❌ Failed to load .obj, using color fallback")
                    return self.create_mission_pad_color_fallback(grid_x, grid_y, pad_number, name)
            else:
                print(f"❌ .obj file not found at: {obj_path}")
                return self.create_mission_pad_color_fallback(grid_x, grid_y, pad_number, name)
                
        except Exception as e:
            print(f"❌ Failed to create Mission Pad {pad_number}: {e}")
            return self.create_mission_pad_color_fallback(grid_x, grid_y, pad_number, name)

    def create_mission_pad_color_fallback(self, grid_x, grid_y, pad_number, name):
        """สร้าง Mission Pad ด้วยสีเมื่อไม่มี .obj model"""
        try:
            # สร้าง primitive shape
            pad_base = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [0.6, 0.6, 0.02]  # 60x60x2cm
            )
            
            if pad_base == -1:
                print(f"❌ Failed to create primitive shape for {name}")
                return None
            
            # ตั้งตำแหน่ง
            pos = self.grid_to_position(grid_x, grid_y)
            pos.append(0.01)
            
            self.sim.setObjectPosition(pad_base, -1, pos)
            self.sim.setObjectAlias(pad_base, name)
            
            # ใส่สีตามหมายเลข
            self.apply_color_by_number(pad_base, pad_number)
            
            # ตั้งค่าฟิสิกส์
            self.sim.setObjectInt32Parameter(pad_base, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(pad_base, self.sim.shapeintparam_respondable, 1)
            
            pad_info = {
                'type': 'mission_pad',
                'handle': pad_base,
                'name': name,
                'grid': f"{chr(65+grid_x)}{grid_y+1}",
                'position': pos,
                'pad_number': pad_number,
                'source': 'color_fallback'
            }
            
            self.field_objects.append(pad_info)
            print(f"✅ Created Mission Pad {pad_number} with color: {name}")
            return pad_info
            
        except Exception as e:
            print(f"❌ Failed to create color fallback for {name}: {e}")
            return None

    def create_fixed_mission_pads(self):
        """สร้าง Mission Pads ในตำแหน่งฟิกส์ที่ถูกต้อง"""
        print("🎯 Creating Fixed Mission Pads...")
        
        # ✅ แก้ไขตำแหน่งให้ถูกต้อง
        # C2 = grid_x=2, grid_y=1
        # D3 = grid_x=3, grid_y=2  
        # C4 = grid_x=2, grid_y=3
        # D5 = grid_x=3, grid_y=4
        
        fixed_positions = [
            (2, 1, 1),  # C2 - Mission Pad 1
            (3, 2, 2),  # D3 - Mission Pad 2
            (2, 3, 3),  # C4 - Mission Pad 3
            (3, 4, 4),  # D5 - Mission Pad 4
        ]
        
        created_pads = []
        
        for grid_x, grid_y, pad_number in fixed_positions:
            pad = self.create_mission_pad(grid_x, grid_y, pad_number)
            if pad:
                created_pads.append(pad)
        
        print(f"🎯 Created {len(created_pads)} Fixed Mission Pads")
        return created_pads

    def create_interactive_mission_pads(self):
        """สร้าง Mission Pads แบบ interactive"""
        print("\n🎯 MISSION PAD CREATION")
        print("=" * 30)
        
        # แสดงตำแหน่งที่แนะนำ
        print("ตำแหน่งแนะนำ: C2, D3, C4, D5")
        
        pad_configs = []
        used_positions = set()
        
        while True:
            try:
                # ถามจำนวน Mission Pad
                num_pads = int(input("จำนวน Mission Pad (1-8): "))
                if 1 <= num_pads <= 8:
                    break
                else:
                    print("❌ จำนวนต้องอยู่ระหว่าง 1-8")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลข")
        
        for i in range(num_pads):
            print(f"\n--- Mission Pad ที่ {i+1} ---")
            
            # ถามตำแหน่ง
            while True:
                position = input("ตำแหน่ง (เช่น C2, D3): ").strip().upper()
                
                if len(position) < 2 or position[0] not in 'ABCDE' or not position[1:].isdigit():
                    print("❌ รูปแบบไม่ถูกต้อง")
                    continue
                
                if position in used_positions:
                    print("❌ ตำแหน่งนี้ถูกใช้แล้ว")
                    continue
                
                used_positions.add(position)
                break
            
            # ถามหมายเลข
            while True:
                try:
                    pad_number = int(input("หมายเลข Mission Pad (1-8): "))
                    if 1 <= pad_number <= 8:
                        break
                    else:
                        print("❌ หมายเลขต้องอยู่ระหว่าง 1-8")
                except ValueError:
                    print("❌ กรุณาใส่ตัวเลข")
            
            pad_configs.append({
                'grid': position,
                'number': pad_number
            })
        
        # สร้าง Mission Pads
        return self.create_custom_mission_pads(pad_configs)

    def get_mission_pad_input(self):
        """รับ input สำหรับการวาง Mission Pad แบบ interactive"""
        print("\n🎯 Mission Pad Configuration")
        print("Available positions: A1-E5 (e.g., C2, D3)")
        print("Available numbers: 1-8")
        print("Enter 'done' to finish")
        
        pad_configs = []
        
        while True:
            try:
                grid_input = input("\nEnter grid position (or 'done'): ").strip()
                
                if grid_input.lower() == 'done':
                    break
                
                if len(grid_input) < 2:
                    print("❌ Invalid format. Use format like 'C2'")
                    continue
                
                number_input = input("Enter Mission Pad number (1-8): ").strip()
                
                try:
                    pad_number = int(number_input)
                    if pad_number < 1 or pad_number > 8:
                        print("❌ Number must be 1-8")
                        continue
                except ValueError:
                    print("❌ Invalid number")
                    continue
                
                pad_configs.append({
                    'grid': grid_input,
                    'number': pad_number
                })
                
                print(f"✅ Added Mission Pad {pad_number} at {grid_input}")
                
            except KeyboardInterrupt:
                print("\n❌ Input cancelled")
                break
        
        return pad_configs

    def apply_color_by_number(self, handle, pad_number):
        """ใส่สีตามหมายเลข Mission Pad"""
        colors = [
            [1.0, 0.0, 0.0],  # 1 = แดง
            [0.0, 1.0, 0.0],  # 2 = เขียว
            [0.0, 0.0, 1.0],  # 3 = น้ำเงิน
            [1.0, 1.0, 0.0],  # 4 = เหลือง
            [1.0, 0.0, 1.0],  # 5 = ม่วง
            [0.0, 1.0, 1.0],  # 6 = ฟ้า
            [1.0, 0.5, 0.0],  # 7 = ส้ม
            [0.5, 0.5, 0.5],  # 8 = เทา
        ]
        
        color_index = (pad_number - 1) % len(colors)
        self.sim.setShapeColor(handle, None,
            self.sim.colorcomponent_ambient_diffuse, colors[color_index])

    def create_custom_mission_pads(self, pad_configs):
        """สร้าง Mission Pads ตามการตั้งค่าที่กำหนด"""
        print(f"🎯 Creating {len(pad_configs)} custom Mission Pads...")
        
        created_pads = []
        
        for config in pad_configs:
            grid_str = config['grid'].upper()
            pad_number = config['number']
            
            # แปลงตำแหน่ง grid เป็น coordinate
            if len(grid_str) >= 2:
                grid_x = ord(grid_str[0]) - ord('A')  # A=0, B=1, C=2, ...
                grid_y = int(grid_str[1:]) - 1        # 1=0, 2=1, 3=2, ...
                
                # ตรวจสอบขอบเขต
                if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                    pad = self.create_mission_pad(grid_x, grid_y, pad_number)
                    if pad:
                        created_pads.append(pad)
                        print(f"✅ Created Mission Pad {pad_number} at {grid_str}")
                    else:
                        print(f"❌ Failed to create Mission Pad {pad_number} at {grid_str}")
                else:
                    print(f"❌ Invalid grid position: {grid_str}")
            else:
                print(f"❌ Invalid grid format: {grid_str}")
        
        print(f"🎯 Created {len(created_pads)} Mission Pads successfully!")
        return created_pads
    # ===============================================================
    # SECTION 9: COMPLETE FIELD CREATION
    # ===============================================================
    
    def create_complete_field(self):
        """สร้างสนามแข่งขันครบถ้วนพร้อม Mission Pad"""
        print("🏗️ Creating complete Drone Odyssey Challenge field...")
        
        # ล้างสนามก่อน
        self.clear_field()

        # ตั้งค่า physics
        self.diagnose_and_fix_physics_issues()

        # 1. สร้างพื้นสนาม
        self.create_tiled_floor()
        
        # 2. สร้างป้ายสีฟ้า
        print("🔵 Creating blue signs...")
        self.create_edge_image_stand(1, 0, 120)  # B1
        self.create_edge_image_stand(3, 0, 120)  # D1
        self.create_edge_image_stand(4, 1, 120)  # E2
        self.create_edge_image_stand(4, 3, 120)  # E4
        
        # 3. สร้างสิ่งกีดขวาง
        print("🩷 Creating brown boxes...")
        self.create_obstacle_box(1, 1)  # B2
        self.create_obstacle_box(2, 2)  # C3
        self.create_obstacle_box(3, 3)  # D4
        self.create_obstacle_box(4, 4)  # E5
        
        print("🟡 Creating yellow box...")
        self.create_adjustable_obstacle(3, 1, height_multiplier=2, name="YellowBox_D2")
        
        # 4. สร้างรั้วปิงปอง
        print("🟢 Creating green fence...")
        self.create_livestock_fence_from_diagram()
    
        # 5. สร้าง Mission Pad (ตำแหน่งฟิก)
        self.create_fixed_mission_pads()

        # รอให้ physics เสถียร
        time.sleep(1.5)

        # 6. สร้างลูกปิงปอง
        print("🏓 Creating ping pong balls...")
        self.create_ping_pong_in_fenced_area()
        
        print("✅ Complete field with Mission Pads created successfully!")
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
            # รับ input สำหรับ Mission Pad
        pad_configs = self.get_mission_pad_input()
            
        if pad_configs:
            self.create_custom_mission_pads(pad_configs)
        else:
            print("ℹ️ No Mission Pads added")
            
            # รับ input สำหรับสิ่งกีดขวางอื่นๆ (optional)
            
        print("✅ Custom field with Mission Pads created successfully!")  

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

# หลังจากสร้างสนามปิงปองแล้ว

        print("\n🏓 CUSTOM PING PONG BALLS")
        print("=" * 30)

        # ถามว่าต้องการปรับแต่งลูกปิงปองหรือไม่
        customize_balls = input("ต้องการปรับแต่งลูกปิงปอง? (y/n): ").strip().lower()

        if customize_balls in ['y', 'yes']:
            # รับการตั้งค่าที่รวมตำแหน่งด้วย
            ball_config = self.get_custom_ping_pong_config()
            
            # แปลงตำแหน่งที่ผู้ใช้เลือก
            grid_position = ball_config['grid_position']
            grid_x = ord(grid_position[0]) - ord('A')  # A=0, B=1, C=2, ...
            grid_y = int(grid_position[1]) - 1         # 1=0, 2=1, 3=2, ...
            
            # สร้างลูกปิงปองที่ตำแหน่งที่เลือก
            self.create_custom_ping_pong_balls(grid_x, grid_y, ball_config)
            
            print(f"✅ สร้างลูกปิงปองที่ {grid_position} เสร็จสิ้น!")
        else:
            # ใช้ลูกปิงปองมาตรฐานที่ A3
            self.create_ping_pong_in_fenced_area()

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
    # SECTION 10: LEGACY FUNCTIONS (สำหรับความเข้ากันได้)
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
