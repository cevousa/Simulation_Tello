"""
Field Manager - Main Controller
คลาสหลักสำหรับจัดการสนามทั้งหมด
"""

from .simulation_manager import SimulationManager
from .field_config import FieldConfig
from .basic_objects import BasicObjectsCreator
from .pingpong_system import PingPongSystem
from .field_parser import FieldParser

class FieldManager:
    """คลาสหลักสำหรับจัดการสนาม Drone Odyssey Challenge"""
    
    def __init__(self):
        # สร้าง components
        self.sim_manager = SimulationManager()
        self.config = FieldConfig()
        self.objects_creator = BasicObjectsCreator(self.sim_manager, self.config)
        self.pingpong_system = PingPongSystem(self.sim_manager, self.config)
        self.parser = FieldParser(self.config)
        
        # เก็บสถานะสนาม
        self.field_objects = []
        
        print("🏟️ Drone Odyssey Challenge Field Creator (Modular)")
        print(f"📏 Field: {self.config.field_size}×{self.config.field_size}m")
        print(f"🔲 Tiles: {self.config.tile_size*100:.0f}×{self.config.tile_size*100:.0f}cm, Gap: {self.config.tile_gap*100:.0f}cm")
    
    # ===============================================================
    # BASIC FIELD OPERATIONS
    # ===============================================================
    
    def start_simulation(self):
        """เริ่มการจำลอง"""
        return self.sim_manager.start_simulation()
    
    def stop_simulation(self):
        """หยุดการจำลอง"""
        return self.sim_manager.stop_simulation()
    
    def clear_field(self):
        """ล้างวัตถุในสนาม"""
        if self.field_objects:
            handles_to_remove = []
            
            for obj in self.field_objects:
                if 'handle' in obj:
                    handles_to_remove.append(obj['handle'])
            
            if handles_to_remove:
                self.sim_manager.remove_objects(handles_to_remove)
                print(f"🗑️ Cleared {len(handles_to_remove)} field objects")
            
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
    # FLOOR CREATION
    # ===============================================================
    
    def create_tiled_floor(self):
        """สร้างพื้นสนามแบ่งช่อง 5×5"""
        print("🟫 Creating tiled floor (5×5 grid)...")
        
        # ตั้งค่า physics ก่อน
        self.sim_manager.setup_physics_engine(self.config)
        
        floor_count = 0
        for row in range(5):
            for col in range(5):
                tile_info = self.objects_creator.create_floor_tile(col, row, floor_count)
                if tile_info:
                    self.field_objects.append(tile_info)
                    floor_count += 1
        
        print(f"✅ Created {floor_count} floor tiles")
        return floor_count > 0
    
    # ===============================================================
    # STRING INPUT FIELD CREATION
    # ===============================================================
    
    def create_field_from_string(self, field_string):
        """สร้างสนามจาก string pattern"""
        try:
            print("🎨 Parsing field string...")
            field_data = self.parser.parse_field_string(field_string)
            
            # ตรวจสอบความถูกต้อง
            validation = self.parser.validate_field_layout(field_data)
            if not validation['valid']:
                print("❌ Field validation failed:")
                for error in validation['errors']:
                    print(f"  - {error}")
                return False
            
            # แสดงคำเตือน (ถ้ามี)
            if validation['warnings']:
                print("⚠️ Warnings:")
                for warning in validation['warnings']:
                    print(f"  - {warning}")
            
            print("🏗️ Creating field objects...")
            created_count = 0
            
            for item in field_data:
                grid_x, grid_y = item['grid_x'], item['grid_y']
                code = item['code']
                position = item['position']
                
                print(f"  Creating '{code}' at {position}")
                
                parsed = self.parser.parse_cell_code(code)
                obj_info = self._create_object_from_parsed(grid_x, grid_y, parsed)
                
                if obj_info:
                    if isinstance(obj_info, list):
                        self.field_objects.extend(obj_info)
                        created_count += len(obj_info)
                    else:
                        self.field_objects.append(obj_info)
                        created_count += 1
            
            print(f"✅ Created {created_count} objects from string")
            return created_count > 0
            
        except Exception as e:
            print(f"❌ Error creating field from string: {e}")
            return False
    
    def _create_object_from_parsed(self, grid_x, grid_y, parsed):
        """สร้างวัตถุจากข้อมูลที่แปลงแล้ว"""
        obj_type = parsed['type']
        
        if obj_type == 'empty':
            return None
        
        elif obj_type == 'obstacle_box':
            return self.objects_creator.create_obstacle_box(
                grid_x, grid_y, 
                parsed['height_cm'], 
                parsed.get('texture_side')
            )
        
        elif obj_type == 'mission_pad':
            return self.objects_creator.create_mission_pad(
                grid_x, grid_y, 
                parsed['pad_number']
            )
        
        elif obj_type == 'predefined_fence':
            # สร้างรั้วแบบ predefined (รูปแบบพิเศษ) + ลูกปิงปอง
            objects = []
            
            # สร้างรั้วพิเศษ
            fence_objects = self.pingpong_system.create_predefined_fence()
            if fence_objects:
                objects.extend(fence_objects)
            
            # สร้างลูกปิงปองในพื้นที่ A3
            balls = self.pingpong_system.create_pingpong_balls(0, 2, 8)  # A3 area
            if balls:
                objects.extend(balls)
            
            return objects if objects else None
        
        elif obj_type == 'fence_zone':
            # สร้างรั้วในตำแหน่งนี้ และลูกปิงปองถ้ามี
            objects = []
            
            # สร้างรั้วรอบๆ พื้นที่
            fence_segments = self._create_fence_segments_for_position(grid_x, grid_y)
            fence_objects = self.pingpong_system.create_fence_boundary(fence_segments)
            
            if fence_objects:
                objects.extend(fence_objects)
            
            # สร้างลูกปิงปองถ้ามี
            if parsed['has_balls']:
                balls = self.pingpong_system.create_pingpong_balls(grid_x, grid_y)
                if balls:
                    objects.extend(balls)
            
            return objects if objects else None
        
        elif obj_type == 'drone':
            return self._create_drone(grid_x, grid_y, parsed.get('model_path'))
        
        elif obj_type == 'qrcode_box':
            return self.objects_creator.create_qrcode_box(
                grid_x, grid_y, 
                parsed.get('qr_path')
            )
        
        elif obj_type == 'pingpong_zone':
            zone_info = self.pingpong_system.create_pingpong_zone(
                grid_x, grid_y, 
                parsed['has_balls']
            )
            
            if zone_info:
                # แปลงเป็น list ของ objects
                objects = []
                
                # เพิ่ม poles
                for pole_handle in zone_info['poles']:
                    objects.append({
                        'handle': pole_handle,
                        'type': 'pingpong_pole',
                        'grid': zone_info['grid']
                    })
                
                # เพิ่ม balls
                objects.extend(zone_info['balls'])
                
                return objects
            
        else:
            print(f"❌ Unknown object type: {obj_type}")
            return None
    
    def _create_fence_segments_for_position(self, grid_x, grid_y):
        """สร้าง fence segments รอบตำแหน่งที่กำหนด"""
        position = self.config.get_grid_position(grid_x, grid_y)
        half_tile = self.config.tile_size / 2
        
        # สร้างรั้วล้อมรอบ 1 ช่อง
        fence_segments = [
            # รั้วล่าง
            ([position[0] - half_tile, position[1] - half_tile], 
             [position[0] + half_tile, position[1] - half_tile], f"Fence_{grid_x}_{grid_y}_Bottom"),
            
            # รั้วบน
            ([position[0] - half_tile, position[1] + half_tile], 
             [position[0] + half_tile, position[1] + half_tile], f"Fence_{grid_x}_{grid_y}_Top"),
            
            # รั้วซ้าย
            ([position[0] - half_tile, position[1] - half_tile], 
             [position[0] - half_tile, position[1] + half_tile], f"Fence_{grid_x}_{grid_y}_Left"),
            
            # รั้วขวา
            ([position[0] + half_tile, position[1] - half_tile], 
             [position[0] + half_tile, position[1] + half_tile], f"Fence_{grid_x}_{grid_y}_Right"),
        ]
        
        return fence_segments

    # ===============================================================
    # PRESET FIELD CREATION
    # ===============================================================
    
    def create_default_preset_field(self):
        """สร้างสนามแบบ preset พื้นฐาน"""
        print("🏗️ Creating default preset field...")
        
        # สร้างพื้นก่อน
        if not self.create_tiled_floor():
            return False
        
        try:
            # Mission Pads ที่มุม
            objects = []
            
            objects.append(self.objects_creator.create_mission_pad(0, 0, 1))  # A1
            objects.append(self.objects_creator.create_mission_pad(4, 0, 2))  # E1
            objects.append(self.objects_creator.create_mission_pad(0, 4, 3))  # A5
            objects.append(self.objects_creator.create_mission_pad(4, 4, 4))  # E5
            
            # กล่องสิ่งกีดขวางตรงกลาง
            objects.append(self.objects_creator.create_obstacle_box(2, 2, 160))  # C3
            objects.append(self.objects_creator.create_obstacle_box(1, 2, 80))   # B3
            objects.append(self.objects_creator.create_obstacle_box(3, 2, 80))   # D3
            
            # Ping Pong Zones
            zone1 = self.pingpong_system.create_pingpong_zone(1, 1, has_balls=True)  # B2
            zone2 = self.pingpong_system.create_pingpong_zone(3, 3, has_balls=True)  # D4
            
            # เพิ่มวัตถุที่สร้างสำเร็จ
            for obj in objects:
                if obj:
                    self.field_objects.append(obj)
            
            # เพิ่ม ping pong zones
            for zone in [zone1, zone2]:
                if zone:
                    # เพิ่ม poles
                    for pole_handle in zone['poles']:
                        self.field_objects.append({
                            'handle': pole_handle,
                            'type': 'pingpong_pole',
                            'grid': zone['grid']
                        })
                    
                    # เพิ่ม balls
                    self.field_objects.extend(zone['balls'])
            
            print("✅ Default preset field created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating preset field: {e}")
            return False
    
    def create_complete_field_with_fence(self):
        """สร้างสนามที่มีรั้วพิเศษตามแบบเดิม"""
        print("🏗️ Creating complete field with special fence...")
        
        # สร้างพื้นก่อน
        if not self.create_tiled_floor():
            return False
        
        try:
            # สร้าง Mission Pads
            mission_pads = [
                self.objects_creator.create_mission_pad(2, 1, 1),  # C2
                self.objects_creator.create_mission_pad(3, 2, 2),  # D3
                self.objects_creator.create_mission_pad(2, 3, 3),  # C4
                self.objects_creator.create_mission_pad(3, 4, 4),  # D5
            ]
            
            # สร้างสิ่งกีดขวาง
            obstacles = [
                self.objects_creator.create_obstacle_box(1, 1, 80),   # B2
                self.objects_creator.create_obstacle_box(2, 2, 120),  # C3
                self.objects_creator.create_obstacle_box(3, 3, 80),   # D4
                self.objects_creator.create_obstacle_box(4, 4, 80),   # E5
            ]
            
            # สร้างรั้วพิเศษ
            print("🔍 Creating predefined fence...")
            fence_objects = self.pingpong_system.create_predefined_fence()
            print(f"🟢 Fence creation returned {len(fence_objects) if fence_objects else 0} objects")
            
            # สร้างลูกปิงปองในพื้นที่รั้ว (A3)
            print("🔍 Creating ping pong balls...")
            pingpong_balls = self.pingpong_system.create_pingpong_balls(0, 2, 8)  # A3 area
            print(f"🟠 Ping pong creation returned {len(pingpong_balls) if pingpong_balls else 0} balls")
            
            # เพิ่มทุกอย่างเข้า field_objects
            all_objects = mission_pads + obstacles
            
            # เพิ่ม fence objects (ตรวจสอบให้แน่ใจว่าไม่เป็น None)
            if fence_objects:
                all_objects.extend(fence_objects)
                print(f"✅ Added {len(fence_objects)} fence objects to field")
            else:
                print("⚠️ No fence objects to add")
            
            # เพิ่ม ping pong balls
            if pingpong_balls:
                all_objects.extend(pingpong_balls)
                print(f"✅ Added {len(pingpong_balls)} ping pong balls to field")
            else:
                print("⚠️ No ping pong balls to add")
            
            print(f"🔍 Total objects to add: {len(all_objects)}")
            
            for obj in all_objects:
                if obj:
                    self.field_objects.append(obj)
                    print(f"  ➕ Added {obj.get('type', 'unknown')} object")
            
            print("✅ Complete field with fence created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating complete field: {e}")
            return False
    
    # ===============================================================
    # HELP AND UTILITIES
    # ===============================================================
    
    def get_field_creation_help(self):
        """ดึงข้อความช่วยเหลือ"""
        return self.parser.get_help_text()
    
    def get_field_stats(self):
        """ดึงสถิติสนาม"""
        if not self.field_objects:
            return "📭 No objects in field"
        
        stats = {}
        for obj in self.field_objects:
            obj_type = obj['type']
            stats[obj_type] = stats.get(obj_type, 0) + 1
        
        stats_text = f"📊 Field Statistics ({len(self.field_objects)} total objects):\n"
        for obj_type, count in stats.items():
            stats_text += f"  - {obj_type.replace('_', ' ').title()}: {count}\n"
        
        return stats_text
    
    def validate_field_completeness(self):
        """ตรวจสอบความสมบูรณ์ของสนาม"""
        has_floor = any(obj['type'] == 'floor' for obj in self.field_objects)
        has_mission_pads = any(obj['type'] == 'mission_pad' for obj in self.field_objects)
        has_obstacles = any(obj['type'] == 'obstacle' for obj in self.field_objects)
        
        completeness = {
            'has_floor': has_floor,
            'has_mission_pads': has_mission_pads,
            'has_obstacles': has_obstacles,
            'is_complete': has_floor and (has_mission_pads or has_obstacles)
        }
        
        return completeness
    
    def _create_drone(self, grid_x, grid_y, model_path=None):
        """สร้างโดรนในตำแหน่งที่กำหนด"""
        try:
            position = self.config.get_grid_position(grid_x, grid_y)
            
            # ถ้าไม่ระบุ path ให้ใช้ path เริ่มต้น
            if model_path is None:
                # ค้นหาไฟล์ Quadcopter.ttm ในโฟลเดอร์ export_model
                import os
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), '..', 'export_model', 'Quadcopter.ttm'),
                    os.path.join(os.path.dirname(__file__), '..', 'export_model', 'quadcopter_scene.ttt'),
                    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'export_model', 'Quadcopter.ttm')),
                ]
                
                model_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        model_path = path
                        print(f"✅ พบไฟล์โดรน: {path}")
                        break
                
                if model_path is None:
                    print("⚠️ ไม่พบไฟล์โมเดลโดรนในโฟลเดอร์ export_model")
            
            drone_handle = None
            
            # ลองโหลดโมเดล .ttm
            if model_path and os.path.exists(model_path):
                print(f"🔄 กำลัง import โมเดลโดรน: {model_path}")
                try:
                    # ตรวจสอบขนาดไฟล์
                    import os
                    file_size = os.path.getsize(model_path)
                    print(f"📁 ขนาดไฟล์: {file_size} bytes")
                    
                    result = self.sim_manager.sim.loadModel(model_path)
                    print(f"🔍 ผลการโหลด: {result}")
                    
                    if result is not None and result != -1:
                        drone_handle = result
                        print(f"✅ Import Quadcopter.ttm สำเร็จ! Handle: {drone_handle}")
                        
                        # ลองดึงข้อมูลเพิ่มเติม
                        try:
                            object_alias = self.sim_manager.sim.getObjectAlias(drone_handle)
                            print(f"📋 ชื่อ object: {object_alias}")
                        except Exception as e:
                            print(f"📋 ไม่สามารถดึงชื่อ object ได้: {e}")
                    else:
                        print(f"❌ loadModel คืนค่า: {result}")
                        
                except Exception as e:
                    print(f"⚠️ ไม่สามารถโหลดโมเดล .ttm ได้: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ ไม่พบไฟล์: {model_path}")
            
            # ถ้าโหลดโมเดลไม่ได้ ให้สร้างโดรนพื้นฐาน
            if drone_handle is None:
                print("🔄 สร้างโดรนพื้นฐานแทน...")
                drone_handle = self._create_basic_drone(grid_x, grid_y)
            
            if drone_handle:
                # ตั้งตำแหน่งโดรนบนพื้น (Z = 0.05 เพื่อไม่ให้จมใต้พื้น)
                drone_position = [position[0], position[1], 0.05]
                self.sim_manager.sim.setObjectPosition(drone_handle, drone_position)
                
                # หันหน้าไปทางทิศเหนือ (Y+ direction) - กล้องชี้เหนือ
                # ใน CoppeliaSim: X=East, Y=North, Z=Up
                # หมุน 0° รอบแกน Z หมายถึงหันไปทาง Y+ (เหนือ)
                drone_orientation = [0, 0, 1.55]  # [X-rot, Y-rot, Z-rot] ไม่หมุน = หันเหนือ
                self.sim_manager.sim.setObjectOrientation(drone_handle, drone_orientation)
                
                # ตั้งชื่อ
                grid_name = self.config.grid_to_string(grid_x, grid_y)
                drone_name = "Quadcopter"
                self.sim_manager.sim.setObjectAlias(drone_handle, drone_name)
                
                # สร้างข้อมูลโดรน
                drone_info = {
                    'handle': drone_handle,
                    'type': 'drone',
                    'name': drone_name,
                    'grid': grid_name,
                    'position': drone_position,
                    'model_loaded': model_path is not None,
                    'facing': 'north',
                    'on_ground': True
                }
                
                print(f"🚁 Created drone at {grid_name} - หันหน้าเหนือ, วางบนพื้น")
                return drone_info
            else:
                print(f"❌ Failed to create drone at {self.config.grid_to_string(grid_x, grid_y)}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating drone: {e}")
            return None
    
    def _create_basic_drone(self, grid_x, grid_y):
        """สร้างโดรนพื้นฐาน (กรณีที่โหลดโมเดลไม่ได้)"""
        try:
            # สร้างโดรนแบบง่ายๆ ด้วย primitive shapes
            
            # ตัวโดรน (ลูกบอล)
            drone_body = self.sim_manager.sim.createPrimitiveShape(
                self.sim_manager.sim.primitiveshape_spheroid,
                [0.3, 0.3, 0.1]  # ขนาด 30x30x10 cm
            )
            
            # ตั้งสี (สีฟ้าสำหรับโดรน)
            self.sim_manager.sim.setShapeColor(drone_body, None, 
                                               self.sim_manager.sim.colorcomponent_ambient_diffuse, 
                                               [0.0, 0.5, 1.0])  # สีฟ้า
            
            # ตั้งค่าฟิสิกส์
            self.sim_manager.sim.setObjectInt32Parameter(drone_body, 
                                                         self.sim_manager.sim.shapeintparam_static, 0)  # ไม่ static
            self.sim_manager.sim.setObjectInt32Parameter(drone_body, 
                                                         self.sim_manager.sim.shapeintparam_respondable, 1)
            
            # ตั้งมวล
            self.sim_manager.sim.setShapeMass(drone_body, 1.5)  # 1.5 กิโลกรัม
            
            # หันหน้าไปทางทิศเหนือ
            self.sim_manager.sim.setObjectOrientation(drone_body, [0, 0, 0])  # หันเหนือ
            
            print("🚁 สร้างโดรนพื้นฐาน (สีฟ้า) หันหน้าทิศเหนือ, วางบนพื้น")
            
            return drone_body
            
        except Exception as e:
            print(f"❌ Error creating basic drone: {e}")
            return None

    # ===============================================================
