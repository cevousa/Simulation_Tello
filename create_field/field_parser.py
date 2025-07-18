"""
Field Parser Module
แปลงและวิเคราะห์ string input สำหรับสร้างสนาม
"""

class FieldParser:
    """คลาสสำหรับแปลง field input string"""
    
    def __init__(self, config):
        self.config = config
    
    def parse_field_string(self, field_string):
        """แปลง string pattern เป็น field objects"""
        lines = [line.strip() for line in field_string.strip().split('\n') if line.strip()]
        
        if len(lines) != 5:
            raise ValueError("Field must have exactly 5 rows")
        
        field_data = []
        for row_idx, line in enumerate(lines):
            cells = line.split('-')
            if len(cells) != 5:
                raise ValueError(f"Row {row_idx+1} must have exactly 5 cells separated by '-'")
            
            # แปลงลำดับแถว (แถวบนสุดใน string = row 4 ใน grid)
            grid_row = 4 - row_idx
            
            for col_idx, cell in enumerate(cells):
                cell = cell.strip()
                if cell and cell != '0':
                    field_data.append({
                        'grid_x': col_idx,
                        'grid_y': grid_row,
                        'code': cell,
                        'position': self.config.grid_to_string(col_idx, grid_row)
                    })
        
        return field_data
    
    def parse_cell_code(self, code):
        """แปลงรหัสเซลล์เป็นข้อมูลที่ใช้ได้"""
        code = code.strip()
        
        if code == '0' or code == '':
            return {'type': 'empty'}
        
        elif code == 'H':
            return {'type': 'predefined_fence', 'has_balls': True}
        
        elif code == 'H.':
            return {'type': 'predefined_fence', 'has_balls': True}
        
        elif code.startswith('B.'):
            return self._parse_box_code(code)
        
        elif code.startswith('M'):
            return self._parse_mission_pad_code(code)
        
        elif code == 'D':
            return {'type': 'drone', 'model_path': None}
        
        elif code == 'Q':
            return {'type': 'qrcode_box', 'height_cm': 230, 'qr_path': r'D:\pythonforcoppelia\Qrcode\testqrcode.png'}
        
        else:
            return {'type': 'unknown', 'code': code}
    
    def _parse_box_code(self, code):
        """แปลงรหัสกล่อง B.xxx"""
        parts = code.split('.')
        if len(parts) < 2:
            return {'type': 'unknown', 'code': code}
        
        height_part = parts[1]
        height_cm = 80  # ค่าเริ่มต้น
        texture_side = None
        
        # ตรวจสอบรูปแบบ texture ที่มี P ใน pattern
        if '[P' in height_part:
            texture_side = '['
            # ลบ [P ออกเพื่อหา height
            height_part = height_part.replace('[P', '')
        elif 'P]' in height_part:
            texture_side = ']'
            # ลบ P] ออกเพื่อหา height
            height_part = height_part.replace('P]', '')
        elif 'P^' in height_part:
            texture_side = '^'
            # ลบ P^ ออกเพื่อหา height
            height_part = height_part.replace('P^', '')
        elif 'P_' in height_part:
            texture_side = '_'
            # ลบ P_ ออกเพื่อหา height
            height_part = height_part.replace('P_', '')
        else:
            # ถ้าไม่มี P ใน pattern ให้หา texture แบบปกติ
            height_str = ""
            for char in height_part:
                if char.isdigit():
                    height_str += char
                elif char in [']', '[', '^', '_']:
                    texture_side = char
                    break
            
            # แปลงความสูง
            try:
                if height_str:
                    height_cm = int(height_str)
            except ValueError:
                height_cm = 80
                
            return {
                'type': 'obstacle_box',
                'height_cm': height_cm,
                'texture_side': texture_side
            }
        
        # สำหรับกรณีที่มี P ใน pattern - หา height จากส่วนที่เหลือ
        height_str = ""
        for char in height_part:
            if char.isdigit():
                height_str += char
        
        # แปลงความสูง
        try:
            if height_str:
                height_cm = int(height_str)
        except ValueError:
            height_cm = 80
        
        return {
            'type': 'obstacle_box',
            'height_cm': height_cm,
            'texture_side': texture_side
        }
    
    def _parse_mission_pad_code(self, code):
        """แปลงรหัส Mission Pad Mxx"""
        try:
            pad_number = int(code[1:])
            if 1 <= pad_number <= 8:
                return {
                    'type': 'mission_pad',
                    'pad_number': pad_number
                }
            else:
                return {'type': 'unknown', 'code': code}
        except ValueError:
            return {'type': 'unknown', 'code': code}
    
    def validate_field_layout(self, field_data):
        """ตรวจสอบความถูกต้องของ layout"""
        errors = []
        warnings = []
        
        # เก็บสถิติ
        stats = {
            'mission_pads': [],
            'obstacles': 0,
            'pingpong_zones': 0,
            'fence_zones': 0,
            'drones': 0,
            'empty_cells': 0
        }
        
        for item in field_data:
            parsed = self.parse_cell_code(item['code'])
            
            if parsed['type'] == 'mission_pad':
                pad_num = parsed['pad_number']
                if pad_num in stats['mission_pads']:
                    errors.append(f"Duplicate Mission Pad {pad_num}")
                else:
                    stats['mission_pads'].append(pad_num)
            
            elif parsed['type'] == 'obstacle_box':
                stats['obstacles'] += 1
            
            elif parsed['type'] == 'pingpong_zone':
                stats['pingpong_zones'] += 1
            
            elif parsed['type'] == 'fence_zone':
                stats['fence_zones'] += 1
            
            elif parsed['type'] == 'drone':
                stats['drones'] += 1
            
            elif parsed['type'] == 'unknown':
                errors.append(f"Unknown code '{item['code']}' at {item['position']}")
        
        # ตรวจสอบข้อแนะนำ
        if len(stats['mission_pads']) == 0:
            warnings.append("No Mission Pads found")
        
        if stats['obstacles'] == 0:
            warnings.append("No obstacles found")
        
        if stats['pingpong_zones'] == 0:
            warnings.append("No ping pong zones found")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'stats': stats
        }
    
    def get_help_text(self):
        """ดึงข้อความช่วยเหลือ"""
        return """
🎨 Field Creator - String Input Mode

รูปแบบ input:
0-H-0-0-0
H-H-0-B.80-0
H-H-0-0-0
0-0-0-0-M1
M2-0-0-0-0

รหัสที่ใช้ได้:
0 = ว่างเปล่า
B.80 = Box สูง 80cm
B.160 = Box สูง 160cm  
B.240 = Box สูง 240cm
M1-M8 = Mission Pad No.1-8
H = Pingpong Zone (เขตกั้น)
H. = จุดที่มี ping pong วางอยู่ 8 ลูก
D = Drone (โดรนจาก Quadcopter.ttm)
B.P] = รูปภาพด้านขวาของกล่อง
B.[P = รูปภาพด้านซ้ายของกล่อง
B.P^ = รูปภาพด้านบนของกล่อง
B.P_ = รูปภาพด้านล่างของกล่อง

หมายเหตุ:
- แต่ละแถวต้องมี 5 ช่อง คั่นด้วย -
- ต้องมี 5 แถว
- แถวบนสุด = แถว 5, แถวล่างสุด = แถว 1
- คอลัมน์ซ้าย = A, คอลัมน์ขวา = E

ตัวอย่าง grid:
   A B C D E
5  - - - - -
4  - - - - -
3  - - - - -
2  - - - - -
1  - - - - -
"""
