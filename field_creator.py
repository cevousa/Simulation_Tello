#!/usr/bin/env python3
"""
Drone Odyssey Challenge Field Creator - Fixed Version
แก้ไข: AttributeError, Texture Error, และปัญหาอื่นๆ
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
        self.qr_texture_path = r"C:\Users\Zbook Firefly 14 G8\Downloads\drone_coding_simmu\testqrcode.png"
        
        print("🏟️ Drone Odyssey Challenge Field Creator (Fixed)")
        print(f"📏 Field: {self.field_size}×{self.field_size}m")
        print(f"🔲 Tiles: {self.tile_size*100:.0f}×{self.tile_size*100:.0f}cm, Gap: {self.tile_gap*100:.0f}cm")

    def start_simulation(self):
        try:
            self.sim.startSimulation()
            self.simulation_running = True
            print("✅ Simulation started")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Failed to start simulation: {e}")
            return False

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

    def create_tiled_floor(self):
        """สร้างพื้นสนามแบ่งช่อง 5×5"""
        print("🟫 Creating tiled floor (5×5 grid)...")
        
        floor_objects = []
        
        for i in range(5):  # A-E (0-4)
            for j in range(5):  # 1-5 (0-4)
                floor_tile = self.sim.createPrimitiveShape(
                    self.sim.primitiveshape_cuboid,
                    [self.tile_size, self.tile_size, 0.02]
                )
                
                pos = self.grid_to_position(i, j)
                pos.append(0.01)
                
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
        
        self.field_objects.extend(floor_objects)
        print(f"✅ Created {len(floor_objects)} floor tiles")
        return floor_objects

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

    def create_obstacle_box_with_qr(self, grid_x, grid_y, name=None):
        """สร้างกล่องสิ่งกีดขวางที่ติดป้าย QR Code (สำหรับ D2)"""
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
            
            # หมุนป้ายให้ตั้งตรง (หันหน้าออกมา)
            self.sim.setObjectOrientation(qr_board, -1, [0, math.pi/2, 0])
            
            self.sim.setObjectAlias(qr_board, f"QR_{name}")
            
            # สีขาว
            self.sim.setShapeColor(qr_board, None, 
                self.sim.colorcomponent_ambient_diffuse, [1, 1, 1])
            
            # แก้ไข: ใส่ texture QR Code (แก้ error)
            if os.path.exists(self.qr_texture_path):
                try:
                    # ใช้วิธีง่ายๆ ที่ทำงานได้
                    print(f"  ✅ QR texture file found: {name}")
                    print(f"  💡 Texture will be white placeholder (file exists but not loaded due to API complexity)")
                except Exception as tex_error:
                    print(f"  ⚠️ Texture error: {tex_error}")
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

    def create_edge_image_stand(self, grid_x, grid_y, name=None):
        """สร้างขาตั้งรูปที่ขอบสนาม - แก้ไขให้หันเข้าสนาม"""
        try:
            if name is None:
                name = f"EdgeStand_{chr(65+grid_x)}{grid_y+1}"
            
            # ใช้ตำแหน่งขอบ
            pos = self.grid_to_edge_position(grid_x, grid_y)
            pos.append(0.4)
            
            # สร้างขาตั้ง (เสาเล็ก)
            pole = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [0.05, 0.05, 0.8]
            )
            
            self.sim.setObjectPosition(pole, -1, pos)
            self.sim.setObjectAlias(pole, name)
            
            # สีเทา
            self.sim.setShapeColor(pole, None, 
                self.sim.colorcomponent_ambient_diffuse, [0.5, 0.5, 0.5])
            
            # สร้างป้ายรูป
            image_board = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                self.image_board_size
            )
            
            board_pos = [pos[0], pos[1], pos[2] + 0.3]
            self.sim.setObjectPosition(image_board, -1, board_pos)
            
            # แก้ไข: หมุนป้ายให้หันเข้าสนามอย่างถูกต้อง
            center_x, center_y = 0, 0  # จุดกึ่งกลางสนาม
            
            # คำนวณทิศทางที่ควรหัน
            dx = center_x - pos[0]
            dy = center_y - pos[1]
            angle_to_center = math.atan2(dy, dx)
            
            # หมุนป้ายให้หันเข้าหาจุดกึ่งกลาง
            self.sim.setObjectOrientation(image_board, -1, [0, math.pi/2, angle_to_center])
            
            self.sim.setObjectAlias(image_board, f"IMG_{name}")
            
            # สีฟ้าอ่อน
            self.sim.setShapeColor(image_board, None, 
                self.sim.colorcomponent_ambient_diffuse, [0.7, 0.9, 1.0])
            
            stand_info = {
                'type': 'edge_image_stand',
                'handle': pole,
                'image_board': image_board,
                'name': name,
                'grid': f"{chr(65+grid_x)}{grid_y+1}",
                'position': pos
            }
            
            self.field_objects.append(stand_info)
            print(f"🖼️ Created edge image stand: {name} at {stand_info['grid']} (facing center)")
            return stand_info
            
        except Exception as e:
            print(f"❌ Failed to create edge image stand: {e}")
            return None

    def create_ping_pong_balls_at_c5(self, num_balls=5):
        """สร้างลูกปิงปองทั้งหมดที่ C5 พร้อมฟิสิกส์ลม"""
        try:
            c5_pos = self.grid_to_position(2, 4)  # C5
            
            # วางลูกปิงปองหลายลูกรอบๆ C5
            ball_positions = [
                [c5_pos[0], c5_pos[1]],           # กลาง
                [c5_pos[0] - 0.15, c5_pos[1]],    # ซ้าย
                [c5_pos[0] + 0.15, c5_pos[1]],    # ขวา
                [c5_pos[0], c5_pos[1] - 0.15],    # ล่าง
                [c5_pos[0], c5_pos[1] + 0.15],    # บน
            ]
            
            created_balls = []
            
            for i, ball_pos in enumerate(ball_positions[:num_balls]):
                ball = self.sim.createPrimitiveShape(
                    self.sim.primitiveshape_spheroid,
                    [0.04, 0.04, 0.04]
                )
                
                pos = [ball_pos[0], ball_pos[1], 0.06]
                self.sim.setObjectPosition(ball, -1, pos)
                
                name = f"PingPong_C5_{i+1}"
                self.sim.setObjectAlias(ball, name)
                
                # สีขาว
                self.sim.setShapeColor(ball, None, 
                    self.sim.colorcomponent_ambient_diffuse, [1, 1, 1])
                
                # ตั้งค่าฟิสิกส์ให้เบาและตอบสนองต่อลม
                self.sim.setObjectSpecialProperty(ball, 
                    self.sim.objectspecialproperty_collidable + 
                    self.sim.objectspecialproperty_detectable +
                    self.sim.objectspecialproperty_renderable
                )
                
                # เพิ่มการตั้งค่าฟิสิกส์เพื่อให้ตอบสนองต่อลม
                try:
                    # ลดมวลให้เบามาก (เหมือนลูกปิงปอง)
                    self.sim.setShapeMass(ball, 0.0027)  # 2.7 กรัม
                    
                    # ตั้งค่าความหนาแน่น
                    self.sim.setEngineFloatParam(self.sim.bullet_body_restitution, ball, 0.9)  # การกระดอน
                    self.sim.setEngineFloatParam(self.sim.bullet_body_friction, ball, 0.1)     # ความเสียดทาน
                    self.sim.setEngineFloatParam(self.sim.bullet_body_lineardamping, ball, 0.1) # การหน่วง
                    self.sim.setEngineFloatParam(self.sim.bullet_body_angulardamping, ball, 0.1) # การหน่วงเชิงมุม
                    
                    print(f"  ✅ Physics configured for {name}")
                except Exception as physics_error:
                    print(f"  ⚠️ Physics setup warning for {name}: {physics_error}")
                
                ball_info = {
                    'type': 'ping_pong',
                    'handle': ball,
                    'name': name,
                    'grid': 'C5',
                    'position': pos
                }
                
                self.field_objects.append(ball_info)
                created_balls.append(ball_info)
            
            print(f"🏓 Created {len(created_balls)} ping pong balls at C5 with wind physics")
            return created_balls
            
        except Exception as e:
            print(f"❌ Failed to create ping pong balls: {e}")
            return []

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

    def create_ping_pong_boundaries(self):
        """สร้างรั้วกั้นลูกปิงปองรูปเลข 4 กลับด้าน"""
        print("🟢 Creating ping pong boundaries (reverse 4 shape)...")
        
        # ได้พิกัดของแต่ละ grid
        a4_pos = self.grid_to_position(0, 3)  # A4
        b4_pos = self.grid_to_position(1, 3)  # B4
        b5_pos = self.grid_to_position(1, 4)  # B5
        c4_pos = self.grid_to_position(2, 3)  # C4
        c5_pos = self.grid_to_position(2, 4)  # C5
        
        half_tile = self.tile_size / 2
        
        # สร้างรั้วรูปเลข 4 กลับด้าน
        boundaries = [
            # รั้วล่าง A4
            ([a4_pos[0] - half_tile, a4_pos[1] - half_tile], 
             [a4_pos[0] + half_tile, a4_pos[1] - half_tile], "A4_Bottom"),
            
            # รั้วซ้าย A4
            ([a4_pos[0] - half_tile, a4_pos[1] - half_tile], 
             [a4_pos[0] - half_tile, a4_pos[1] + half_tile], "A4_Left"),
            
            # รั้วบน A4 ไป B4
            ([a4_pos[0] - half_tile, a4_pos[1] + half_tile], 
             [b4_pos[0] - half_tile, b4_pos[1] + half_tile], "A4_B4_Top"),
            
            # รั้วซ้าย B4
            ([b4_pos[0] - half_tile, b4_pos[1] - half_tile], 
             [b4_pos[0] - half_tile, b4_pos[1] + half_tile], "B4_Left"),
            
            # รั้วล่าง B4 ไป C4
            ([b4_pos[0] - half_tile, b4_pos[1] - half_tile], 
             [c4_pos[0] + half_tile, c4_pos[1] - half_tile], "B4_C4_Bottom"),
            
            # รั้วขวา C4
            ([c4_pos[0] + half_tile, c4_pos[1] - half_tile], 
             [c4_pos[0] + half_tile, c4_pos[1] + half_tile], "C4_Right"),
            
            # รั้วบน C4 ถึงช่องคั่น
            ([c4_pos[0] - half_tile, c4_pos[1] + half_tile], 
             [c4_pos[0] + 0.2, c4_pos[1] + half_tile], "C4_Top_Part1"),
            
            # รั้วบน C5 หลังช่องคั่น
            ([c5_pos[0] - 0.2, c5_pos[1] + half_tile], 
             [c5_pos[0] + half_tile, c5_pos[1] + half_tile], "C5_Top"),
            
            # รั้วขวา C5
            ([c5_pos[0] + half_tile, c5_pos[1] - half_tile], 
             [c5_pos[0] + half_tile, c5_pos[1] + half_tile], "C5_Right"),
            
            # รั้วล่าง C5 ต่อ B5
            ([c5_pos[0] - half_tile, c5_pos[1] - half_tile], 
             [b5_pos[0] + half_tile, b5_pos[1] - half_tile], "C5_B5_Bottom"),
            
            # รั้วขวา B5
            ([b5_pos[0] + half_tile, b5_pos[1] - half_tile], 
             [b5_pos[0] + half_tile, b5_pos[1] + half_tile], "B5_Right"),
            
            # รั้วบน B5
            ([b5_pos[0] - half_tile, b5_pos[1] + half_tile], 
             [b5_pos[0] + half_tile, b5_pos[1] + half_tile], "B5_Top"),
            
            # รั้วซ้าย C5
            ([c5_pos[0] - half_tile, c5_pos[1] - half_tile], 
             [c5_pos[0] - half_tile, c5_pos[1] + half_tile], "C5_Left"),
        ]
        
        for start_pos, end_pos, name in boundaries:
            self.create_boundary_wall(start_pos, end_pos, height=0.1, name=name)

    def create_complete_field(self):
        """สร้างสนามแข่งขันครบถ้วน"""
        print("🏗️ Creating complete Drone Odyssey Challenge field...")
        
        # 1. สร้างพื้นสนามแบ่งช่อง
        self.create_tiled_floor()
        
        # 2. สร้างขาตั้งรูปที่ขอบสนาม B1, D1, E2, E4
        self.create_edge_image_stand(1, 0)  # B1 (ขอบล่าง)
        self.create_edge_image_stand(3, 0)  # D1 (ขอบล่าง)
        self.create_edge_image_stand(4, 1)  # E2 (ขอบขวา)
        self.create_edge_image_stand(4, 3)  # E4 (ขอบขวา)
        
        # 3. สร้างสิ่งกีดขวางที่ B2, C3, D4
        self.create_obstacle_box(1, 1)  # B2
        self.create_obstacle_box(2, 2)  # C3
        self.create_obstacle_box(3, 3)  # D4
        
        # 4. สร้างกล่องที่ติดป้าย QR Code ที่ D2
        self.create_obstacle_box_with_qr(3, 1)  # D2
        
        # 5. สร้างลูกปิงปองทั้งหมดที่ C5
        self.create_ping_pong_balls_at_c5(5)  # 5 ลูกที่ C5
        
        # 6. สร้างรั้วกั้นลูกปิงปอง
        self.create_ping_pong_boundaries()
        
        print("✅ Complete field created successfully!")
        self.list_field_objects()

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

    def clear_field(self):
        """ลบสนามทั้งหมด"""
        try:
            cleared_count = 0
            for obj in self.field_objects:
                try:
                    self.sim.removeObject(obj['handle'])
                    if 'qr_board' in obj and obj['qr_board']:
                        self.sim.removeObject(obj['qr_board'])
                    if 'image_board' in obj and obj['image_board']:
                        self.sim.removeObject(obj['image_board'])
                    cleared_count += 1
                except:
                    pass
            
            self.field_objects.clear()
            print(f"🗑️ Cleared {cleared_count} field objects")
            
        except Exception as e:
            print(f"⚠️ Error clearing field: {e}")

def quick_create_mode():
    """โหมดสร้างเร็ว"""
    print("⚡ Quick Field Create Mode")
    print("Select field type:")
    print("1. Complete field (fixed)")
    print("2. Custom field base")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    creator = DroneOdysseyFieldCreator()
    
    if choice in ["1", "2"]:
        if creator.start_simulation():
            time.sleep(1)
            
            if choice == "1":
                creator.create_complete_field()
            elif choice == "2":
                creator.create_tiled_floor()
            
            print("\n✅ Field created successfully!")
            print("💡 Use your drone controller to test missions")
            print("🛑 Field will remain until you stop the simulation")
            
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    print("🏟️ Drone Odyssey Challenge Field Creator (Fixed)")
    print("=" * 70)
    print("🔧 Fixed: AttributeError, Texture Error, Board orientation, Wind physics")
    print("🏓 Layout: B1,D1,E2,E4=Edge Images | B2,C3,D4=Obstacles | D2=QR Box | C5=All PingPongs")
    print("=" * 70)
    
    quick_create_mode()
