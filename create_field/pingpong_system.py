# -*- coding: utf-8 -*-
"""
Ping Pong System Module
จัดการระบบลูกปิงปองและรั้วกั้น
"""

import math
import random

class PingPongSystem:
    """คลาสสำหรับจัดการระบบลูกปิงปองและรั้ว"""
    
    def __init__(self, sim_manager, config):
        self.sim = sim_manager.sim
        self.config = config
    
    def create_pingpong_zone(self, grid_x, grid_y, has_balls=False):
        """สร้างเขตปิงปอง - ไม่รวมเสา ใช้เฉพาะลูกปิงปอง"""
        try:
            grid_name = self.config.grid_to_string(grid_x, grid_y)
            
            # สร้างลูกปิงปองถ้าต้องการ
            balls = []
            if has_balls:
                balls = self.create_pingpong_balls(grid_x, grid_y)
            
            print(f"[PINGPONG] Created Ping Pong Zone at {grid_name} (balls only)")
            
            return {
                'poles': [],  # ไม่มีเสา
                'balls': balls,
                'grid': grid_name
            }
            
        except Exception as e:
            print(f"[ERROR] Error creating ping pong zone: {e}")
            return None
    
    def create_pingpong_balls(self, grid_x, grid_y, count=8):
        """สร้างลูกปิงปอง"""
        try:
            position = self.config.get_grid_position(grid_x, grid_y)
            balls = []
            
            # ตำแหน่งลูกปิงปอง (วางแบบสุ่มในพื้นที่)
            for i in range(count):
                # สุ่มตำแหน่งในพื้นที่ 0.6×0.6 ตารางเมตร
                ball_x = position[0] + random.uniform(-0.25, 0.25)
                ball_y = position[1] + random.uniform(-0.25, 0.25)
                ball_z = 0.02  # วางบนพื้น
                
                ball_handle = self.sim.createPrimitiveShape(
                    self.sim.primitiveshape_spheroid,
                    [self.config.physics['pingpong_diameter']] * 3
                )
                self.sim.setObjectPosition(ball_handle, [ball_x, ball_y, ball_z])
                
                # ตั้งชื่อ
                ball_name = f"PingPongBall_{i}_{self.config.grid_to_string(grid_x, grid_y)}"
                self.sim.setObjectAlias(ball_handle, ball_name)
                
                # ตั้งค่าคุณสมบัติ (ไม่ static เพื่อให้เคลื่อนที่ได้)
                self.sim.setObjectInt32Parameter(ball_handle, self.sim.shapeintparam_static, 0)
                self.sim.setObjectInt32Parameter(ball_handle, self.sim.shapeintparam_respondable, 1)
                
                # ตั้งมวล
                self.sim.setShapeMass(ball_handle, self.config.physics['pingpong_mass'])
                
                # ตั้งสี
                self.sim.setShapeColor(ball_handle, None, self.sim.colorcomponent_ambient_diffuse, 
                                     self.config.colors['pingpong_ball'])
                
                ball_info = {
                    'handle': ball_handle,
                    'type': 'pingpong_ball',
                    'name': ball_name,
                    'grid': self.config.grid_to_string(grid_x, grid_y),
                    'position': [ball_x, ball_y, ball_z]
                }
                
                balls.append(ball_info)
            
            grid_name = self.config.grid_to_string(grid_x, grid_y)
            print(f"[PINGPONG] Created {count} ping pong balls at {grid_name}")
            return balls
            
        except Exception as e:
            print(f"[ERROR] Error creating ping pong balls: {e}")
            return []
    
    def create_fence_boundary(self, fence_segments):
        """สร้างรั้วกั้นตามพิกัดที่กำหนด"""
        try:
            fence_objects = []
            
            for start_pos, end_pos, name in fence_segments:
                fence_obj = self._create_fence_segment(start_pos, end_pos, name)
                if fence_obj:
                    fence_objects.append(fence_obj)
            
            print(f"[SUCCESS] Created {len(fence_objects)} fence segments")
            return fence_objects
            
        except Exception as e:
            print(f"[ERROR] Error creating fence boundary: {e}")
            return []
    
    def _create_fence_segment(self, start_pos, end_pos, name, height=0.1):
        """สร้างรั้วแต่ละส่วน - ใช้สีขาวตามรูป"""
        try:
            length = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
            angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
            
            wall = self.sim.createPrimitiveShape(
                self.sim.primitiveshape_cuboid,
                [length, 0.06, height]  # ความหนา 6cm สูง 10cm
            )
            
            center_pos = [
                (start_pos[0] + end_pos[0]) / 2,
                (start_pos[1] + end_pos[1]) / 2,
                height/2 + 0.02
            ]
            
            self.sim.setObjectPosition(wall, center_pos)
            self.sim.setObjectOrientation(wall, [0, 0, angle])
            
            # ตั้งชื่อ
            self.sim.setObjectAlias(wall, name)
            
            # ตั้งค่าคุณสมบัติ
            self.sim.setObjectInt32Parameter(wall, self.sim.shapeintparam_static, 1)
            self.sim.setObjectInt32Parameter(wall, self.sim.shapeintparam_respondable, 1)
            
            # ใช้สีเขียวตามโค้ดเดิม
            self.sim.setShapeColor(wall, None, self.sim.colorcomponent_ambient_diffuse, 
                                 [0.2, 0.8, 0.2])  # สีเขียวตามเดิม
            
            fence_info = {
                'handle': wall,
                'type': 'fence',
                'name': name,
                'position': center_pos,
                'length': length,
                'angle': angle
            }
            
            return fence_info
            
        except Exception as e:
            print(f"[ERROR] Failed to create fence segment {name}: {e}")
            return None
    
    def create_predefined_fence(self):
        """สร้างรั้วรูปแบบพิเศษตาม field_creator เดิม - แบบล้อมรอบสมบูรณ์"""
        a3_pos = self.config.get_grid_position(0, 2)  # A3
        a4_pos = self.config.get_grid_position(0, 3)  # A4
        b3_pos = self.config.get_grid_position(1, 2)  # B3
        b4_pos = self.config.get_grid_position(1, 3)  # B4
        b5_pos = self.config.get_grid_position(1, 4)  # B5
        
        half_tile = self.config.tile_size / 2
        
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
        
        fence_objects = self.create_fence_boundary(fence_segments)
        print(f"[SUCCESS] Created livestock fence (shaped boundary) - Height: {fence_height*100:.0f}cm")
        return fence_objects
