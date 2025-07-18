"""
Basic Objects Creator Module
สร้างวัตถุพื้นฐานต่างๆ ในสนาม
"""

import os
import math

class BasicObjectsCreator:
    """คลาสสำหรับสร้างวัตถุพื้นฐาน"""
    
    def __init__(self, sim_manager, config):
        self.sim = sim_manager.sim
        self.config = config
        
    def create_floor_tile(self, grid_x, grid_y, tile_index):
        """สร้างแผ่นพื้นหนึ่งแผ่น"""
        try:
            position = self.config.get_grid_position(grid_x, grid_y)
            position.append(0.0010)  # ความสูง 2cm
            
            tile_handle = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [self.config.tile_size, self.config.tile_size, 0.002]
            )
            
            self.sim.setObjectPosition(tile_handle, position)
            
            # ตั้งชื่อ
            tile_name = f"FloorTile_{grid_x}_{grid_y}"
            self.sim.setObjectAlias(tile_handle, tile_name)
            
            # ตั้งค่าคุณสมบัติ
            self.sim.setObjectInt32Parameter(tile_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(tile_handle, self.sim.shapeintparam_respondable, 1)
            # Note: shapeintparam_collidable ไม่มีใน CoppeliaSim version นี้
            
            # ตั้งสี
            self.sim.setShapeColor(tile_handle, None, self.sim.colorcomponent_ambient_diffuse, 
                                 self.config.colors['floor'])
            
            # สร้างข้อมูลวัตถุ
            tile_info = {
                'handle': tile_handle,
                'type': 'floor',
                'name': tile_name,
                'grid': self.config.grid_to_string(grid_x, grid_y),
                'position': position
            }
            
            return tile_info
            
        except Exception as e:
            print(f"❌ Error creating floor tile at ({grid_x},{grid_y}): {e}")
            return None
    
    def create_obstacle_box(self, grid_x, grid_y, height_cm=80, texture_side=None):
        """สร้างกล่องสิ่งกีดขวาง"""
        try:
            position = self.config.get_grid_position(grid_x, grid_y)
            height_m = height_cm / 100.0
            position.append(height_m / 2)  # ความสูงครึ่งหนึ่งจากพื้น
            
            # สร้างกล่อง - ปรับขนาดสำหรับกล่องที่มีรูปภาพ
            if texture_side:
                # กล่องที่มีรูปภาพ - ลดความหนาลง
                size = [0.4, 0.4, height_m]  # 40×40cm แทน 60×60cm
            else:
                # กล่องปกติ - ใช้ขนาดเดิม
                size = [self.config.obstacle_size[0], self.config.obstacle_size[1], height_m]
            
            box_handle = self.sim.createPrimitiveShape(self.sim.primitiveshape_cuboid, size)
            self.sim.setObjectPosition(box_handle, position)
            
            # ตั้งชื่อ
            box_name = f"Box_{height_cm}cm_{self.config.grid_to_string(grid_x, grid_y)}"
            self.sim.setObjectAlias(box_handle, box_name)
            
            # ตั้งค่าคุณสมบัติ
            self.sim.setObjectInt32Parameter(box_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(box_handle, self.sim.shapeintparam_respondable, 1)
            
            # ตั้งสี
            color = self._get_box_color(height_cm)
            self.sim.setShapeColor(box_handle, None, self.sim.colorcomponent_ambient_diffuse, color)
            
            # เพิ่ม texture ถ้ามี
            if texture_side:
                self._create_image_board_for_box(grid_x, grid_y, texture_side, height_cm)
            
            # สร้างข้อมูลวัตถุ
            box_info = {
                'handle': box_handle,
                'type': 'obstacle',
                'name': box_name,
                'grid': self.config.grid_to_string(grid_x, grid_y),
                'height': height_cm,
                'texture_side': texture_side,
                'position': position
            }
            
            print(f"📦 Created {height_cm}cm box at {self.config.grid_to_string(grid_x, grid_y)}")
            return box_info
            
        except Exception as e:
            print(f"❌ Error creating obstacle box: {e}")
            return None
    
    def create_mission_pad(self, grid_x, grid_y, pad_number):
        """สร้าง Mission Pad"""
        try:
            position = self.config.get_grid_position(grid_x, grid_y)
            position.append(0.021)  # วางบนพื้น
            
            # สร้างป้าย
            pad_handle = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid, 
                self.config.qr_board_size
            )
            self.sim.setObjectPosition(pad_handle, position)
            
            # หมุนให้หันขึ้น
            self.sim.setObjectOrientation(pad_handle, [0, 0, 0])
            
            # ตั้งชื่อ
            pad_name = f"MissionPad_{pad_number}_{self.config.grid_to_string(grid_x, grid_y)}"
            self.sim.setObjectAlias(pad_handle, pad_name)
            
            # ตั้งค่าคุณสมบัติ
            self.sim.setObjectInt32Parameter(pad_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(pad_handle, self.sim.shapeintparam_respondable, 1)
            
            # ตั้งสี
            color = self.config.get_mission_pad_color(pad_number)
            self.sim.setShapeColor(pad_handle, None, self.sim.colorcomponent_ambient_diffuse, color)
            
            # ใส่ texture QR Code
            self._add_qr_texture(pad_handle, pad_number)
            
            # สร้างข้อมูลวัตถุ
            pad_info = {
                'handle': pad_handle,
                'type': 'mission_pad',
                'name': pad_name,
                'grid': self.config.grid_to_string(grid_x, grid_y),
                'pad_number': pad_number,
                'position': position
            }
            
            print(f"🎯 Created Mission Pad {pad_number} at {self.config.grid_to_string(grid_x, grid_y)}")
            return pad_info
            
        except Exception as e:
            print(f"❌ Error creating mission pad: {e}")
            return None
    
    def create_qrcode_box(self, grid_x, grid_y, qr_image_path=None):
        """สร้างกล่อง QR code ความสูง 230cm พร้อมแผ่นป้ายสีขาว
        
        Args:
            grid_x: ตำแหน่ง X ในกริด
            grid_y: ตำแหน่ง Y ในกริด  
            qr_image_path: path ของไฟล์ QR code (ถ้าไม่ระบุจะใช้ default)
        """
        try:
            # ใช้ default path ถ้าไม่ระบุ
            if qr_image_path is None:
                qr_image_path = r"D:\pythonforcoppelia\Qrcode\testqrcode.png"
            
            position = self.config.get_grid_position(grid_x, grid_y)
            height_m = 2.30  # 230cm
            position.append(height_m / 2)  # ความสูงครึ่งหนึ่งจากพื้น
            
            # สร้างกล่อง
            size = [self.config.obstacle_size[0], self.config.obstacle_size[1], height_m]
            box_handle = self.sim.createPrimitiveShape(self.sim.primitiveshape_cuboid, size)
            self.sim.setObjectPosition(box_handle, position)
            
            # ตั้งชื่อ
            box_name = f"QRBox_230cm_{self.config.grid_to_string(grid_x, grid_y)}"
            self.sim.setObjectAlias(box_handle, box_name)
            
            # ตั้งค่าคุณสมบัติ
            self.sim.setObjectInt32Parameter(box_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(box_handle, self.sim.shapeintparam_respondable, 1)
            
            # ตั้งสีกล่องเป็นสีเทา
            self.sim.setShapeColor(box_handle, None, self.sim.colorcomponent_ambient_diffuse, [0.5, 0.5, 0.5])
            
            # สร้างแผ่นป้าย QR code สีขาวข้างกล่อง
            qr_board_handle = self._create_qr_board_on_side(grid_x, grid_y, height_m, qr_image_path)
            
            # สร้างข้อมูลวัตถุ
            box_info = {
                'handle': box_handle,
                'qr_board_handle': qr_board_handle,
                'type': 'qrcode_box',
                'name': box_name,
                'grid': self.config.grid_to_string(grid_x, grid_y),
                'height': 230,
                'qr_path': qr_image_path,
                'position': position
            }
            
            print(f"📦 Created QR code box (230cm) at {self.config.grid_to_string(grid_x, grid_y)}")
            if qr_board_handle:
                print(f"🎯 Added white QR board on side with image: {qr_image_path}")
            
            return box_info
            
        except Exception as e:
            print(f"❌ Error creating QR code box: {e}")
            return None
    
    def _create_qr_board_on_side(self, grid_x, grid_y, box_height, qr_image_path):
        """สร้างแผ่นป้าย QR code สีขาวข้างกล่อง"""
        try:
            # คำนวณตำแหน่งแผ่นป้าย (ติดข้างกล่อง)
            box_pos = self.config.get_grid_position(grid_x, grid_y)
            
            # ขนาดกล่อง
            box_width = 0.6   # 60cm
            
            # ขนาดแผ่นป้าย - ขนาดใหญ่เพื่อให้โดรนเห็นชัดเจน
            board_width = 0.5   # 50cm
            board_height = 0.5  # 50cm  
            board_thickness = 0.02  # 2cm (หนาขึ้นเพื่อให้เด่นชัด)
            
            # ตำแหน่ง - ติดข้างกล่อง (ด้านหน้า) เลื่อนขึ้นด้านบน
            board_x = box_pos[0]
            board_y = box_pos[1] + (box_width/2) + (board_thickness/2)  # ข้างหน้ากล่อง
            board_z = box_height * 0.75  # เลื่อนขึ้นไปด้านบน (3/4 ของความสูงกล่อง)
            
            # สร้างแผ่นป้าย
            board_handle = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid, 
                [board_width, board_thickness, board_height]
            )
            
            if board_handle == -1:
                print("❌ Failed to create QR board")
                return None
            
            self.sim.setObjectPosition(board_handle, [board_x, board_y, board_z])
            self.sim.setObjectOrientation(board_handle, [0, 0, 0])  # หันหน้าออกจากกล่อง
            
            # ตั้งชื่อ
            grid_name = self.config.grid_to_string(grid_x, grid_y)
            board_name = f"QRBoard_{grid_name}_side"
            self.sim.setObjectAlias(board_handle, board_name)
            
            # ตั้งสีขาว
            self.sim.setShapeColor(board_handle, None, 
                self.sim.colorcomponent_ambient_diffuse, [1.0, 1.0, 1.0])  # สีขาวสะอาด
            
            # ตั้งค่าฟิสิกส์
            self.sim.setObjectInt32Parameter(board_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(board_handle, self.sim.shapeintparam_respondable, 1)
            
            # เพิ่ม QR code texture ถ้ามีไฟล์
            if os.path.exists(qr_image_path):
                texture_id = self.sim.loadTexture(qr_image_path)
                if texture_id != -1:
                    # ใช้ texture บนหน้าหน้า (face ที่หันออกจากกล่อง)
                    self.sim.setShapeTexture(board_handle, texture_id, self.sim.texturemap_plane, 0, [1.0, 1.0])
                    print(f"✅ Added QR texture to white board: {qr_image_path}")
                else:
                    print(f"⚠️ Failed to load QR texture: {qr_image_path}")
            else:
                print(f"⚠️ QR image file not found: {qr_image_path}")
                print("📋 White board created without QR texture")
            
            print(f"⬜ Created white QR board on side at ({board_x:.3f}, {board_y:.3f}, {board_z:.3f})")
            
            return board_handle
            
        except Exception as e:
            print(f"❌ Error creating QR board on side: {e}")
            return None

    def _get_box_color(self, height_cm):
        """ดึงสีกล่องตามความสูง"""
        if height_cm <= 80:
            return self.config.colors['obstacle']  # สีน้ำตาล
        elif height_cm <= 160:
            return [1.0, 1.0, 0.0]  # สีเหลือง
        else:
            return [1.0, 0.5, 0.0]  # สีส้ม (สูงมาก)
    
    def _create_image_board_for_box(self, grid_x, grid_y, direction, height_cm=80):
        """สร้างป้ายรูปข้างกล่อง - แก้ไขการหมุนบนล่าง"""
        # คำนวณตำแหน่งป้าย
        box_pos = self.config.get_grid_position(grid_x, grid_y)
        
        # ขนาดกล่องที่มีรูปภาพ (ตรงกับใน create_obstacle_box)
        box_width = 0.4   # 40cm (ลดลงจาก 60cm สำหรับกล่องที่มีรูปภาพ)
        box_depth = 0.4   # 40cm (ลดลงจาก 60cm สำหรับกล่องที่มีรูปภาพ)  
        box_height = height_cm / 100.0  # แปลง cm เป็ m
        
        # ขนาดป้าย
        board_width = 0.35   # 35cm (เล็กกว่าหน้ากล่อง)
        board_height = 0.25  # 25cm
        board_thickness = 0.008  # 8mm (บางลง)
        
        # แปลงทิศทางตามแบบเดิม
        direction_mapping = {
            ']': 'right',  # ขวา
            '[': 'left',   # ซ้าย
            '^': 'up',     # บน
            '_': 'down'    # ล่าง
        }
        actual_direction = direction_mapping.get(direction, direction)
        
        # คำนวณตำแหน่งและการหมุนให้ป้ายหันหลังเข้าหากล่อง
        if actual_direction == 'right':
            # ป้ายด้านขวาของกล่อง - หันหลังเข้าหาซ้าย (เข้าหากล่อง)
            image_x = box_pos[0] + (box_width/2) + (board_thickness/2)
            image_y = box_pos[1]
            image_z = box_height/2
            rotation = [0, 0, math.pi]  # หมุน 180° หันหลังเข้าหากล่อง
            board_size = [board_thickness, board_width, board_height]
            
        elif actual_direction == 'left':
            # ป้ายด้านซ้ายของกล่อง - หันหลังเข้าหาขวา (เข้าหากล่อง)
            image_x = box_pos[0] - (box_width/2) - (board_thickness/2)
            image_y = box_pos[1]
            image_z = box_height/2
            rotation = [0, 0, 0]  # ไม่หมุน หันหลังเข้าหากล่อง
            board_size = [board_thickness, board_width, board_height]
            
        elif actual_direction == 'up':
            # ป้ายด้านหน้า (บน) ของกล่อง - หันหลังเข้าหาหลัง (เข้าหากล่อง)
            image_x = box_pos[0]
            image_y = box_pos[1] + (box_depth/2) + (board_thickness/2)
            image_z = box_height/2
            rotation = [0, 0, -math.pi]  # หมุน -180° หันหลังเข้าหากล่อง
            board_size = [board_width, board_thickness, board_height]
            
        elif actual_direction == 'down':
            # ป้ายด้านหลัง (ล่าง) ของกล่อง - หันหลังเข้าหาหน้า (เข้าหากล่อง)
            image_x = box_pos[0]
            image_y = box_pos[1] - (box_depth/2) - (board_thickness/2)
            image_z = box_height/2
            rotation = [0, 0, 0]  # ไม่หมุน หันหลังเข้าหากล่อง
            board_size = [board_width, board_thickness, board_height]
        else:
            print(f"❌ Unknown direction: {direction}")
            return None
        
        # สร้างป้าย
        image_handle = self.sim.createPrimitiveShape(
            self.sim.primitiveshape_cuboid, 
            board_size
        )
        
        if image_handle == -1:
            print(f"❌ Failed to create image board for {actual_direction}")
            return None
        
        self.sim.setObjectPosition(image_handle, [image_x, image_y, image_z])
        self.sim.setObjectOrientation(image_handle, rotation)
        
        # ตั้งชื่อ
        grid_name = self.config.grid_to_string(grid_x, grid_y)
        image_name = f"ImageBoard_{grid_name}_{actual_direction}_{height_cm}cm"
        self.sim.setObjectAlias(image_handle, image_name)
        
        # ใช้สีที่เด่นชัดขึ้น - สีม่วงอ่อนสำหรับป้ายรูป
        self.sim.setShapeColor(image_handle, None, 
            self.sim.colorcomponent_ambient_diffuse, [0.8, 0.4, 0.8])  # สีม่วงอ่อน
        
        # ตั้งค่าฟิสิกส์
        self.sim.setObjectInt32Parameter(image_handle, self.sim.shapeintparam_static, 1)
        self.sim.setObjectInt32Parameter(image_handle, self.sim.shapeintparam_respondable, 1)
        
        # สร้างข้อมูลวัตถุ
        image_info = {
            'handle': image_handle,
            'type': 'image_board',
            'name': image_name,
            'grid': grid_name,
            'direction': actual_direction,
            'position': [image_x, image_y, image_z],
            'box_height_cm': height_cm,
            'rotation': rotation
        }
        
        # แสดงข้อมูล debug แบบละเอียด
        rotation_degrees = [math.degrees(r) for r in rotation]
        print(f"🖼️ Created image board: {image_name}")
        print(f"   📍 Position: ({image_x:.3f}, {image_y:.3f}, {image_z:.3f})")
        print(f"   🔄 Rotation: ({rotation_degrees[0]:.1f}°, {rotation_degrees[1]:.1f}°, {rotation_degrees[2]:.1f}°)")
        print(f"   📐 Direction: {actual_direction} - Back facing box center")
        
        return image_info
    
    def _add_qr_texture(self, object_handle, pad_number):
        """เพิ่ม QR Code texture"""
        try:
            # พาธไฟล์ QR สำหรับแต่ละหมายเลข
            qr_path = f"../mission_pad_templates/number_{pad_number}/missionpad_{pad_number}.png"
            
            # ตรวจสอบไฟล์
            if not os.path.exists(qr_path):
                qr_path = self.config.qr_texture_path  # ใช้ default
            
            # สร้าง texture
            if os.path.exists(qr_path):
                texture_id = self.sim.loadTexture(qr_path)
                if texture_id != -1:
                    self.sim.setShapeTexture(object_handle, texture_id, self.sim.texturemap_plane, 0, [1.0, 1.0])
                    print(f"✅ Added QR texture {pad_number}")
                else:
                    print(f"⚠️ Failed to load QR texture {pad_number}")
            else:
                print(f"⚠️ QR texture file not found: {qr_path}")
                
        except Exception as e:
            print(f"❌ Error adding QR texture: {e}")
