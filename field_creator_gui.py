#!/usr/bin/env python3
"""
Drone Odyssey Challenge Field Creator - GUI Version
โปรแกรม GUI สำหรับสร้างสนามแบบ Interactive
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sys
import os
import threading
import json
from datetime import datetime

# เพิ่ม path สำหรับ import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from create_field import FieldManager
except ImportError as e:
    print(f"❌ Error importing field manager: {e}")
    sys.exit(1)

class FieldCreatorGUI:
    """GUI สำหรับสร้างและจัดการสนาม Drone Odyssey Challenge"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🏟️ Drone Odyssey Field Creator")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # สร้าง FieldManager
        self.field_manager = None
        self.is_simulation_running = False
        
        # สร้าง UI
        self.setup_ui()
        
        # เริ่มต้น FieldManager
        self.initialize_field_manager()
    
    def setup_ui(self):
        """ตั้งค่า UI หลัก"""
        # หัวข้อหลัก
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🏟️ Drone Odyssey Challenge Field Creator", 
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Right panel - Output and field visualization
        right_panel = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
    
    def setup_left_panel(self, parent):
        """ตั้งค่าแผงควบคุมด้านซ้าย"""
        # Simulation Control
        sim_frame = tk.LabelFrame(parent, text="🚀 Simulation Control", font=('Arial', 10, 'bold'))
        sim_frame.pack(fill=tk.X, padx=10, pady=5)
        
        button_frame = tk.Frame(sim_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_btn = tk.Button(
            button_frame, 
            text="▶️ Start Simulation", 
            command=self.start_simulation,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = tk.Button(
            button_frame, 
            text="⏹️ Stop Simulation", 
            command=self.stop_simulation,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 9, 'bold'),
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        # Field Operations
        field_frame = tk.LabelFrame(parent, text="🏗️ Field Operations", font=('Arial', 10, 'bold'))
        field_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            field_frame, 
            text="🎨 Create from String Input", 
            command=self.show_string_input_dialog,
            width=25
        ).pack(pady=2)
        
        tk.Button(
            field_frame, 
            text="🏗️ Create Default Preset", 
            command=self.create_default_field,
            width=25
        ).pack(pady=2)
        
        tk.Button(
            field_frame, 
            text="🏟️ Create Complete Field", 
            command=self.create_complete_field,
            width=25
        ).pack(pady=2)
        
        tk.Button(
            field_frame, 
            text="🧹 Clear All Objects", 
            command=self.clear_field,
            width=25,
            bg='#f39c12',
            fg='white'
        ).pack(pady=2)
        
        # Field Information
        info_frame = tk.LabelFrame(parent, text="📊 Field Information", font=('Arial', 10, 'bold'))
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            info_frame, 
            text="📋 List Field Objects", 
            command=self.list_field_objects,
            width=25
        ).pack(pady=2)
        
        tk.Button(
            info_frame, 
            text="📊 Show Statistics", 
            command=self.show_statistics,
            width=25
        ).pack(pady=2)
        
        # File Operations
        file_frame = tk.LabelFrame(parent, text="💾 File Operations", font=('Arial', 10, 'bold'))
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            file_frame, 
            text="📁 Load Field Config", 
            command=self.load_field_config,
            width=25
        ).pack(pady=2)
        
        tk.Button(
            file_frame, 
            text="💾 Save Field Config", 
            command=self.save_field_config,
            width=25
        ).pack(pady=2)
        
        # Quick Actions
        quick_frame = tk.LabelFrame(parent, text="⚡ Quick Actions", font=('Arial', 10, 'bold'))
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            quick_frame, 
            text="🎲 Random Field", 
            command=self.create_random_field,
            width=25,
            bg='#9b59b6',
            fg='white'
        ).pack(pady=2)
        
        tk.Button(
            quick_frame, 
            text="🏃 Quick Test Field", 
            command=self.create_test_field,
            width=25,
            bg='#3498db',
            fg='white'
        ).pack(pady=2)
    
    def setup_right_panel(self, parent):
        """ตั้งค่าแผงแสดงผลด้านขวา"""
        # Status bar
        status_frame = tk.Frame(parent, bg='#34495e', height=30)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame, 
            text="🔄 Initializing...", 
            bg='#34495e', 
            fg='white',
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Output area
        output_frame = tk.LabelFrame(parent, text="📝 Output Log", font=('Arial', 10, 'bold'))
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            height=15, 
            font=('Consolas', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Field visualization (placeholder)
        viz_frame = tk.LabelFrame(parent, text="🗺️ Field Visualization", font=('Arial', 10, 'bold'))
        viz_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.field_canvas = tk.Canvas(viz_frame, height=200, bg='#ecf0f1')
        self.field_canvas.pack(fill=tk.X, padx=5, pady=5)
        
        # Draw grid
        self.draw_field_grid()
    
    def draw_field_grid(self):
        """วาดตาราง 5x5 สำหรับแสดงสนาม"""
        self.field_canvas.delete("all")
        
        canvas_width = self.field_canvas.winfo_reqwidth()
        canvas_height = 200
        
        # คำนวณขนาดช่อง
        grid_size = min(canvas_width - 20, canvas_height - 20) 
        cell_size = grid_size // 5
        start_x = (canvas_width - grid_size) // 2
        start_y = 10
        
        # วาดตาราง
        for i in range(6):
            # เส้นแนวตั้ง
            x = start_x + i * cell_size
            self.field_canvas.create_line(x, start_y, x, start_y + grid_size, fill='#7f8c8d', width=1)
            
            # เส้นแนวนอน
            y = start_y + i * cell_size
            self.field_canvas.create_line(start_x, y, start_x + grid_size, y, fill='#7f8c8d', width=1)
        
        # เพิ่มป้ายกำกับ
        for row in range(5):
            for col in range(5):
                x = start_x + col * cell_size + cell_size // 2
                y = start_y + row * cell_size + cell_size // 2
                self.field_canvas.create_text(
                    x, y, 
                    text=f"({col},{row})", 
                    fill='#7f8c8d', 
                    font=('Arial', 8)
                )
    
    def log_message(self, message):
        """แสดงข้อความใน output log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update()
    
    def update_status(self, status):
        """อัพเดทสถานะ"""
        self.status_label.config(text=status)
        self.root.update()
    
    def initialize_field_manager(self):
        """เริ่มต้น FieldManager"""
        try:
            self.update_status("🔄 Initializing Field Manager...")
            self.field_manager = FieldManager()
            self.log_message("✅ Field Manager initialized successfully")
            self.update_status("✅ Ready")
        except Exception as e:
            self.log_message(f"❌ Error initializing Field Manager: {e}")
            self.update_status("❌ Error")
            messagebox.showerror("Error", f"Failed to initialize Field Manager:\n{e}")
    
    def start_simulation(self):
        """เริ่มการจำลอง"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.update_status("🚀 Starting simulation...")
            success = self.field_manager.start_simulation()
            
            if success:
                self.is_simulation_running = True
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.log_message("✅ Simulation started successfully")
                self.update_status("🚀 Simulation Running")
            else:
                self.log_message("❌ Failed to start simulation")
                self.update_status("❌ Start Failed")
        except Exception as e:
            self.log_message(f"❌ Error starting simulation: {e}")
            self.update_status("❌ Error")
            messagebox.showerror("Error", f"Failed to start simulation:\n{e}")
    
    def stop_simulation(self):
        """หยุดการจำลอง"""
        if not self.field_manager:
            return
        
        try:
            self.update_status("⏹️ Stopping simulation...")
            success = self.field_manager.stop_simulation()
            
            self.is_simulation_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            if success:
                self.log_message("✅ Simulation stopped successfully")
                self.update_status("⏹️ Simulation Stopped")
            else:
                self.log_message("⚠️ Simulation stop completed")
                self.update_status("⏹️ Stopped")
        except Exception as e:
            self.log_message(f"❌ Error stopping simulation: {e}")
            self.update_status("❌ Error")
    
    def show_string_input_dialog(self):
        """แสดงหน้าต่างสำหรับใส่ string field"""
        dialog = StringInputDialog(self.root, self.field_manager, self.log_message, self.update_status)
    
    def create_default_field(self):
        """สร้างสนามแบบ default preset"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.update_status("🏗️ Creating default field...")
            self.log_message("🏗️ Creating default preset field...")
            
            # สร้างในเธรดแยก
            def create_field():
                try:
                    self.field_manager.create_default_preset_field()
                    self.log_message("✅ Default field created successfully")
                    self.update_status("✅ Field Created")
                except Exception as e:
                    self.log_message(f"❌ Error creating default field: {e}")
                    self.update_status("❌ Error")
            
            threading.Thread(target=create_field, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Error: {e}")
            self.update_status("❌ Error")
    
    def create_complete_field(self):
        """สร้างสนามแบบสมบูรณ์"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.update_status("🏟️ Creating complete field...")
            self.log_message("🏟️ Creating complete field with special fence...")
            
            def create_field():
                try:
                    self.field_manager.create_complete_field_with_special_fence()
                    self.log_message("✅ Complete field created successfully")
                    self.update_status("✅ Complete Field Created")
                except Exception as e:
                    self.log_message(f"❌ Error creating complete field: {e}")
                    self.update_status("❌ Error")
            
            threading.Thread(target=create_field, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Error: {e}")
            self.update_status("❌ Error")
    
    def clear_field(self):
        """ล้างสนาม"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        result = messagebox.askyesno("Confirm", "Are you sure you want to clear all field objects?")
        if result:
            try:
                self.update_status("🧹 Clearing field...")
                self.field_manager.clear_field()
                self.log_message("✅ Field cleared successfully")
                self.update_status("✅ Field Cleared")
            except Exception as e:
                self.log_message(f"❌ Error clearing field: {e}")
                self.update_status("❌ Error")
    
    def list_field_objects(self):
        """แสดงรายการวัตถุในสนาม"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.log_message("📋 Listing field objects...")
            self.field_manager.list_field_objects()
            self.update_status("📋 Objects Listed")
        except Exception as e:
            self.log_message(f"❌ Error listing objects: {e}")
            self.update_status("❌ Error")
    
    def show_statistics(self):
        """แสดงสถิติสนาม"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.log_message("📊 Showing field statistics...")
            self.field_manager.show_field_statistics()
            self.update_status("📊 Statistics Shown")
        except Exception as e:
            self.log_message(f"❌ Error showing statistics: {e}")
            self.update_status("❌ Error")
    
    def create_random_field(self):
        """สร้างสนามแบบสุ่ม"""
        self.log_message("🎲 Creating random field... (Feature coming soon)")
        self.update_status("🎲 Random Field")
    
    def create_test_field(self):
        """สร้างสนามทดสอบ"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.update_status("🏃 Creating test field...")
            self.log_message("🏃 Creating quick test field...")
            
            def create_field():
                try:
                    # สร้างสนามทดสอบง่ายๆ
                    self.field_manager.create_tiled_floor()
                    self.field_manager.create_fence()
                    self.log_message("✅ Test field created successfully")
                    self.update_status("✅ Test Field Created")
                except Exception as e:
                    self.log_message(f"❌ Error creating test field: {e}")
                    self.update_status("❌ Error")
            
            threading.Thread(target=create_field, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Error: {e}")
            self.update_status("❌ Error")
    
    def load_field_config(self):
        """โหลดการตั้งค่าสนาม"""
        filename = filedialog.askopenfilename(
            title="Load Field Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.log_message(f"📁 Loaded config from: {filename}")
                self.update_status("📁 Config Loaded")
            except Exception as e:
                self.log_message(f"❌ Error loading config: {e}")
                self.update_status("❌ Load Error")
    
    def save_field_config(self):
        """บันทึกการตั้งค่าสนาม"""
        filename = filedialog.asksaveasfilename(
            title="Save Field Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                config = {
                    "timestamp": datetime.now().isoformat(),
                    "field_objects_count": len(self.field_manager.field_objects) if self.field_manager else 0,
                    "simulation_running": self.is_simulation_running
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                self.log_message(f"💾 Saved config to: {filename}")
                self.update_status("💾 Config Saved")
            except Exception as e:
                self.log_message(f"❌ Error saving config: {e}")
                self.update_status("❌ Save Error")


class StringInputDialog:
    """หน้าต่างสำหรับใส่ field string"""
    
    def __init__(self, parent, field_manager, log_callback, status_callback):
        self.field_manager = field_manager
        self.log_callback = log_callback
        self.status_callback = status_callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🎨 Create Field from String Input")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
    
    def setup_dialog(self):
        """ตั้งค่าหน้าต่าง dialog"""
        # หัวข้อ
        title_label = tk.Label(
            self.dialog, 
            text="🎨 Create Field from String Input", 
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)
        
        # คำแนะนำ
        info_text = """Enter field configuration string (5x5 grid):
Format: 5 rows, 5 columns separated by dashes (-)

Available codes:
- 0 = Empty space
- B.80 = Box 80cm height
- B.160 = Box 160cm height  
- B.240 = Box 240cm height
- M1-M8 = Mission Pad No.1-8
- H = Pingpong Zone (fence area)
- H. = Pingpong zone with 8 balls
- D = Drone

Example: "0-H-0-0-0" (row with fence in column B)"""
        
        info_label = tk.Label(
            self.dialog, 
            text=info_text, 
            justify=tk.LEFT,
            font=('Arial', 9)
        )
        info_label.pack(pady=5, padx=20)
        
        # Text input area
        input_frame = tk.Frame(self.dialog)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(input_frame, text="Field String:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.text_input = scrolledtext.ScrolledText(
            input_frame, 
            height=10, 
            width=50,
            font=('Consolas', 10)
        )
        self.text_input.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ใส่ตัวอย่าง
        example_string = """0-H-0-0-0
H-H-0-B.80-0
H-H-0-0-0
0-0-0-0-M1
M2-0-0-0-0"""
        self.text_input.insert(tk.END, example_string)
        
        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame, 
            text="✅ Create Field", 
            command=self.create_field,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="❓ Help", 
            command=self.show_help,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="❌ Cancel", 
            command=self.dialog.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=15
        ).pack(side=tk.LEFT, padx=5)
    
    def create_field(self):
        """สร้างสนามจาก string input"""
        field_string = self.text_input.get(1.0, tk.END).strip()
        
        if not field_string:
            messagebox.showwarning("Warning", "Please enter a field string")
            return
        
        # Validate format before sending to field manager
        lines = [line.strip() for line in field_string.strip().split('\n') if line.strip()]
        
        if len(lines) != 5:
            messagebox.showerror("Invalid Format", 
                f"Field must have exactly 5 rows, but got {len(lines)} rows.\n\n"
                "Example format:\n"
                "0-H-0-0-0\n"
                "H-H-0-B.80-0\n"
                "H-H-0-0-0\n"
                "0-0-0-0-M1\n"
                "M2-0-0-0-0")
            return
        
        # Check each row has 5 cells
        for i, line in enumerate(lines):
            cells = line.split('-')
            if len(cells) != 5:
                messagebox.showerror("Invalid Format", 
                    f"Row {i+1} must have exactly 5 cells separated by '-', but got {len(cells)} cells.\n\n"
                    f"Row {i+1}: {line}\n\n"
                    "Each row should look like: 0-H-0-B.80-M1")
                return
        
        try:
            self.status_callback("🎨 Creating field from string...")
            self.log_callback(f"🎨 Creating field from string input:\n{field_string}")
            
            def create_field():
                try:
                    self.field_manager.create_field_from_string(field_string)
                    self.log_callback("✅ Field created successfully from string input")
                    self.status_callback("✅ String Field Created")
                except Exception as e:
                    self.log_callback(f"❌ Error creating field from string: {e}")
                    self.status_callback("❌ Error")
            
            threading.Thread(target=create_field, daemon=True).start()
            self.dialog.destroy()
            
        except Exception as e:
            self.log_callback(f"❌ Error: {e}")
            self.status_callback("❌ Error")
            messagebox.showerror("Error", f"Failed to create field:\n{e}")
    
    def show_help(self):
        """แสดงคำแนะนำการใช้งาน"""
        help_window = tk.Toplevel(self.dialog)
        help_window.title("❓ Field Format Help")
        help_window.geometry("650x500")
        help_window.transient(self.dialog)
        
        # Help content
        help_text = """🎨 Field Creator - String Input Format Help

รูปแบบ input:
0-H-0-0-0
H-H-0-B.80-0
H-H-0-0-0
0-0-0-0-M1
M2-0-0-0-0

รหัสที่ใช้ได้:
• 0 = ว่างเปล่า (Empty space)
• B.80 = Box สูง 80cm
• B.160 = Box สูง 160cm  
• B.240 = Box สูง 240cm
• M1-M8 = Mission Pad No.1-8
• H = Pingpong Zone (เขตกั้น)
• H. = จุดที่มี ping pong วางอยู่ 8 ลูก
• D = Drone (โดรนจาก Quadcopter.ttm)

รหัสพิเศษสำหรับรูปภาพบนกล่อง:
• B.[P = รูปภาพด้านซ้ายของกล่อง
• B.P] = รูปภาพด้านขวาของกล่อง
• B.P^ = รูปภาพด้านบนของกล่อง
• B.P_ = รูปภาพด้านล่างของกล่อง

หมายเหตุสำคัญ:
• แต่ละแถวต้องมี 5 ช่อง คั่นด้วย - (dash)
• ต้องมี 5 แถว
• แถวบนสุด = แถว 5, แถวล่างสุด = แถว 1
• คอลัมน์ซ้าย = A, คอลัมน์ขวา = E

ตัวอย่าง grid:
   A B C D E
5  0-H-0-0-0
4  H-H-0-B.80-0
3  H-H-0-0-0
2  0-0-0-0-M1
1  M2-0-0-0-0

ตัวอย่างอื่นๆ:
• สนามว่าง: 0-0-0-0-0 (ทุกแถว)
• กล่องเดียว: 0-0-B.160-0-0 (แถวกลาง)
• Mission pad มุม: M1-0-0-0-M2 (แถวบน)
"""
        
        text_widget = scrolledtext.ScrolledText(
            help_window, 
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        tk.Button(
            help_window,
            text="✅ Close",
            command=help_window.destroy,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(pady=5)


def main():
    """ฟังก์ชันหลัก"""
    root = tk.Tk()
    app = FieldCreatorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Application error: {e}")


if __name__ == "__main__":
    main()
