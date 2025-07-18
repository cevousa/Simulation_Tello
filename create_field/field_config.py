"""
Field Configuration Settings
การตั้งค่าและขนาดต่างๆ สำหรับสนาม
"""

class FieldConfig:
    """คลาสสำหรับเก็บการตั้งค่าสนาม"""
    
    def __init__(self):
        # ขนาดสนามตามมาตรฐาน
        self.field_size = 5.0  # 5×5 เมตร
        self.tile_size = 0.8   # แผ่นขนาด 80×80 ซม.
        self.tile_gap = 0.2    # ช่องว่าง 20 ซม.
        self.border_gap = 0.1  # เว้นจากขอบ 10 ซม.
        
        # ขนาดอุปกรณ์
        self.obstacle_size = [0.6, 0.6, 0.8]  # กล่อง 60×60×80 ซม.
        self.qr_board_size = [0.3, 0.3, 0.02] # ป้าย QR 30×30 ซม.
        self.image_board_size = [0.4, 0.3, 0.02] # ป้ายรูป 40×30 ซม.
        
        # สีต่างๆ
        self.colors = {
            'floor': [0.7, 0.7, 0.7],           # สีเทาอ่อน
            'obstacle': [0.6, 0.4, 0.2],        # สีน้ำตาล
            'mission_pad_1': [1.0, 0.0, 0.0],   # แดง
            'mission_pad_2': [0.0, 1.0, 0.0],   # เขียว
            'mission_pad_3': [0.0, 0.0, 1.0],   # น้ำเงิน
            'mission_pad_4': [1.0, 1.0, 0.0],   # เหลือง
            'mission_pad_5': [1.0, 0.0, 1.0],   # ม่วง
            'mission_pad_6': [0.0, 1.0, 1.0],   # ฟ้า
            'mission_pad_7': [1.0, 0.5, 0.0],   # ส้ม
            'mission_pad_8': [0.5, 0.5, 0.5],   # เทา
            'pingpong_ball': [1.0, 0.5, 0.0],   # ส้ม
            'pingpong_pole': [1.0, 1.0, 0.0],   # เหลือง
            'fence': [0.2, 0.8, 0.2],           # เขียว
            'image_board': [0.1, 0.5, 1.0],     # ฟ้าสด
        }
        
        # พาธไฟล์
        self.qr_texture_path = r"..\testqrcode.png"
        self.image_texture_path = r"..\testqrcode.png"
        
        # การตั้งค่าฟิสิกส์
        self.physics = {
            'simulation_time_step': 0.005,
            'realtime_simulation': True,
            'floor_mass': 1000.0,
            'pingpong_mass': 0.0027,  # 2.7 กรัม
            'pingpong_diameter': 0.04,  # 4 ซม.
        }
    
    def get_mission_pad_color(self, pad_number):
        """ดึงสีของ Mission Pad ตามหมายเลข"""
        color_key = f'mission_pad_{pad_number}'
        return self.colors.get(color_key, self.colors['mission_pad_1'])
    
    def get_grid_position(self, grid_x, grid_y):
        """แปลงตำแหน่ง Grid เป็นพิกัดจริง (A1 = มุมล่างซ้าย)"""
        real_x = self.border_gap + (self.tile_size + self.tile_gap) * grid_x + self.tile_size/2 - self.field_size/2
        real_y = self.border_gap + (self.tile_size + self.tile_gap) * grid_y + self.tile_size/2 - self.field_size/2
        return [real_x, real_y]
    
    def get_edge_position(self, grid_x, grid_y):
        """แปลงตำแหน่ง Grid เป็นพิกัดขอบ (สำหรับป้ายที่ขอบ)"""
        center_pos = self.get_grid_position(grid_x, grid_y)
        
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
    
    def parse_grid_string(self, grid_string):
        """แปลง string grid เป็น x,y coordinates (เช่น 'A1' -> 0,0)"""
        if len(grid_string) < 2:
            raise ValueError(f"Invalid grid string: {grid_string}")
        
        grid_x = ord(grid_string[0].upper()) - ord('A')  # A=0, B=1, C=2, ...
        grid_y = int(grid_string[1:]) - 1                # 1=0, 2=1, 3=2, ...
        
        if not (0 <= grid_x < 5 and 0 <= grid_y < 5):
            raise ValueError(f"Grid position out of bounds: {grid_string}")
        
        return grid_x, grid_y
    
    def grid_to_string(self, grid_x, grid_y):
        """แปลง x,y coordinates เป็น string grid (เช่น 0,0 -> 'A1')"""
        return f"{chr(65+grid_x)}{grid_y+1}"
