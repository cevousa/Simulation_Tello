#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Drone Odyssey Challenge Field Creator - Advanced GUI Version
โปรแกรม GUI แบบขั้นสูงพร้อม Visual Field Designer Tools

Available Tools:
- B.80, B.160, B.240 = กล่องขนาดต่างๆ
- B.[P = กล่องรูปภาพซ้าย (Box Left Image)
- B.P] = กล่องรูปภาพขวา (Box Right Image)  
- B.P^ = กล่องรูปภาพบน (Box Top Image)
- B.P_ = กล่องรูปภาพล่าง (Box Bottom Image)
- Q = กล่อง QR Code 230cm (QR Code Box)
- M1-M8 = Mission Pads
- H, H. = Pingpong Zones
- D = Drone
- 0 = Empty Space
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sys
import os
import threading
import json
from datetime import datetime
import random
import subprocess
import tempfile

# เพิ่ม path สำหรับ import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from create_field import FieldManager
except ImportError as e:
    print(f"[ERROR] Error importing field manager: {e}")
    sys.exit(1)

class AdvancedFieldCreatorGUI:
    """GUI ขั้นสูงสำหรับสร้างและจัดการสนาม Drone Odyssey Challenge"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Field Creator Pro - Drone Odyssey Challenge")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # ตั้งค่า style
        self.setup_styles()
        
        # ตัวแปรสถานะ
        self.field_manager = None
        self.is_simulation_running = False
        self.field_grid = [['0' for _ in range(5)] for _ in range(5)]  # 5x5 grid
        self.selected_tool = 'B.80'  # เครื่องมือที่เลือก
        self.is_code_running = False
        self.code_process = None
        
        # สร้าง UI
        self.setup_ui()
        
        # เริ่มต้น FieldManager
        self.initialize_field_manager()
    
    def setup_styles(self):
        """ตั้งค่า TTK Styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # กำหนดสีและรูปแบบ
        self.style.configure('Header.TLabel', 
                           foreground='white', 
                           background='#2c3e50',
                           font=('Arial', 16, 'bold'))
        
        self.style.configure('Panel.TFrame', 
                           background='#34495e')
        
        self.style.configure('Tool.TButton',
                           font=('Arial', 9, 'bold'))
    
    def setup_ui(self):
        """ตั้งค่า UI หลัก"""
        # หัวข้อหลัก
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=70)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="Field Creator Pro - Drone Odyssey Challenge", 
            font=('Arial', 18, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            header_frame, 
            text="Advanced Visual Field Designer with Interactive Tools", 
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        subtitle_label.pack()
        
        # Main container
        main_container = tk.Frame(self.root, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Top toolbar
        self.setup_toolbar(main_container)
        
        # Content area
        content_frame = tk.Frame(main_container, bg='#2c3e50')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # สร้าง Notebook สำหรับ tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Field Designer
        field_tab = ttk.Frame(self.notebook)
        self.notebook.add(field_tab, text="🏟️ Field Designer")
        
        # Tab 2: Python Code Runner
        code_tab = ttk.Frame(self.notebook)
        self.notebook.add(code_tab, text="🐍 Python Code")
        
        # Setup tabs
        self.setup_field_designer_tab(field_tab)
        self.setup_code_runner_tab(code_tab)
        
        # Status bar
        self.setup_status_bar()
    
    def setup_field_designer_tab(self, parent):
        """ตั้งค่า Tab สำหรับ Field Designer"""
        # Left panel - Visual field designer
        left_panel = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right panel - Controls and output
        right_panel = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.setup_visual_designer(left_panel)
        self.setup_control_panel(right_panel)
    
    def setup_code_runner_tab(self, parent):
        """ตั้งค่า Tab สำหรับ Python Code Runner"""
        # Main container for code tab
        code_main = tk.Frame(parent, bg='#2c3e50')
        code_main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top frame for editor
        editor_frame = tk.LabelFrame(code_main, text="🐍 Python Code Editor", 
                                   bg='#34495e', fg='white', font=('Arial', 10, 'bold'))
        editor_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Toolbar for code editor
        code_toolbar = tk.Frame(editor_frame, bg='#34495e')
        code_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # File operations
        tk.Button(code_toolbar, text="📄 New", command=self.new_code_file,
                 bg='#3498db', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
        
        tk.Button(code_toolbar, text="📁 Open", command=self.open_code_file,
                 bg='#3498db', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
        
        tk.Button(code_toolbar, text="💾 Save", command=self.save_code_file,
                 bg='#3498db', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
        
        # Separator
        tk.Frame(code_toolbar, width=2, bg='#7f8c8d').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Run controls
        self.run_code_btn = tk.Button(code_toolbar, text="▶️ Run Code", command=self.run_python_code,
                                     bg='#27ae60', fg='white', font=('Arial', 8, 'bold'))
        self.run_code_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_code_btn = tk.Button(code_toolbar, text="⏹️ Stop", command=self.stop_python_code,
                                      bg='#e74c3c', fg='white', font=('Arial', 8, 'bold'), state=tk.DISABLED)
        self.stop_code_btn.pack(side=tk.LEFT, padx=2)
        
        tk.Button(code_toolbar, text="🧹 Clear Output", command=self.clear_code_output,
                 bg='#f39c12', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
        
        # Separator
        tk.Frame(code_toolbar, width=2, bg='#7f8c8d').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Tools
        tk.Button(code_toolbar, text="✓ Check Syntax", command=self.check_python_syntax,
                 bg='#9b59b6', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
        
        tk.Button(code_toolbar, text="📦 Install Package", command=self.install_python_package,
                 bg='#8e44ad', fg='white', font=('Arial', 8, 'bold')).pack(side=tk.LEFT, padx=2)
        
        # Code editor container
        editor_container = tk.Frame(editor_frame, bg='#34495e')
        editor_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Line numbers
        self.line_numbers = tk.Text(editor_container, width=4, padx=3, takefocus=0,
                                  border=0, state='disabled', wrap='none',
                                  bg='#404040', fg='#ffffff', font=('Consolas', 10))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Code editor
        self.code_editor = scrolledtext.ScrolledText(
            editor_container,
            wrap='none',
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff',
            selectbackground='#404040',
            font=('Consolas', 10),
            undo=True,
            maxundo=-1
        )
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events for line numbers and syntax highlighting
        self.code_editor.bind('<KeyRelease>', self.on_code_changed)
        self.code_editor.bind('<Button-1>', self.on_code_changed)
        
        # Bottom frame for output
        output_frame = tk.LabelFrame(code_main, text="📋 Output Console", 
                                   bg='#34495e', fg='white', font=('Arial', 10, 'bold'))
        output_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Output text area
        self.code_output = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            bg='#1a1a1a',
            fg='#00ff00',
            font=('Consolas', 9),
            state='disabled'
        )
        self.code_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for different output types
        self.code_output.tag_configure("error", foreground="#ff6b6b")
        self.code_output.tag_configure("info", foreground="#4ecdc4")
        self.code_output.tag_configure("warning", foreground="#ffe66d")
        
        # Add welcome code
        self.add_welcome_code()
        
        # Current file tracking
        self.current_code_file = None
    
    def setup_toolbar(self, parent):
        """ตั้งค่า toolbar ด้านบน"""
        toolbar_frame = tk.Frame(parent, bg='#34495e', height=50)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        toolbar_frame.pack_propagate(False)
        
        # Tool selection
        tools_frame = tk.Frame(toolbar_frame, bg='#34495e')
        tools_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Label(tools_frame, text="🛠️ Tools:", bg='#34495e', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # เครื่องมือต่างๆ รวม QR Code Box
        tools = [
            ('🟫', 'B.80', 'Box 80cm'),
            ('🏢', 'B.160', 'Box 160cm'),
            ('🏗️', 'B.240', 'Box 240cm'),
            ('🖼️', 'B.[P', 'Box Left Image'),
            ('🎨', 'B.P]', 'Box Right Image'),
            ('🖌️', 'B.P^', 'Box Top Image'),
            ('🎭', 'B.P_', 'Box Bottom Image'),
            ('�', 'Q', 'QR Code Box 230cm'),
            ('�🔴', 'M1', 'Mission Pad 1'),
            ('🟢', 'M2', 'Mission Pad 2'),
            ('🔵', 'M3', 'Mission Pad 3'),
            ('🟡', 'M4', 'Mission Pad 4'),
            ('🟣', 'M5', 'Mission Pad 5'),
            ('⚫', 'M6', 'Mission Pad 6'),
            ('🟤', 'M7', 'Mission Pad 7'),
            ('🔶', 'M8', 'Mission Pad 8'),
            ('🟩', 'H', 'Pingpong Zone'),
            ('🟦', 'H.', 'Pingpong + Balls'),
            ('🚁', 'D', 'Drone'),
            ('⬜', '0', 'Empty')
        ]
        
        self.tool_buttons = {}
        for emoji, tool_id, tooltip in tools:
            btn = tk.Button(
                tools_frame,
                text=f"{emoji}\n{tool_id}",
                command=lambda t=tool_id: self.select_tool(t),
                width=4,
                font=('Arial', 8, 'bold'),
                bg='#3498db' if tool_id == self.selected_tool else '#7f8c8d',
                fg='white',
                relief=tk.RAISED
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.tool_buttons[tool_id] = btn
        
        # Simulation controls
        sim_frame = tk.Frame(toolbar_frame, bg='#34495e')
        sim_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.start_btn = tk.Button(
            sim_frame, 
            text="▶️ Start", 
            command=self.start_simulation,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=8
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = tk.Button(
            sim_frame, 
            text="⏹️ Stop", 
            command=self.stop_simulation,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 9, 'bold'),
            width=8,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)
    
    def setup_visual_designer(self, parent):
        """ตั้งค่าส่วนออกแบบสนามแบบ visual"""
        # หัวข้อ
        header = tk.Label(parent, text="🎨 Visual Field Designer", 
                         bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        header.pack(pady=10)
        
        # Grid canvas
        canvas_frame = tk.Frame(parent, bg='#34495e')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.field_canvas = tk.Canvas(
            canvas_frame, 
            bg='#ecf0f1',
            relief=tk.SUNKEN,
            bd=2
        )
        self.field_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.field_canvas.bind('<Button-1>', self.on_canvas_click)
        self.field_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.field_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Control buttons
        control_frame = tk.Frame(parent, bg='#34495e')
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(control_frame, text="🎲 Random Fill", command=self.random_fill,
                 bg='#9b59b6', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=2)
        
        tk.Button(control_frame, text="🧹 Clear Grid", command=self.clear_grid,
                 bg='#f39c12', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=2)
        
        tk.Button(control_frame, text="🏗️ Build Field", command=self.build_field_from_grid,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=2)
        
        tk.Button(control_frame, text="💾 Save Design", command=self.save_design,
                 bg='#3498db', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.RIGHT, padx=2)
        
        tk.Button(control_frame, text="📁 Load Design", command=self.load_design,
                 bg='#8e44ad', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.RIGHT, padx=2)
        
        # แสดงตาราง
        self.draw_field_grid()
    
    def setup_control_panel(self, parent):
        """ตั้งค่าแผงควบคุมด้านขวา"""
        parent.configure(width=350)
        
        # Quick Actions
        quick_frame = tk.LabelFrame(parent, text="⚡ Quick Actions", 
                                   bg='#34495e', fg='white', font=('Arial', 10, 'bold'))
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        quick_buttons = [
            ("🏗️ Default Preset", self.create_default_field, '#3498db'),
            ("🏟️ Complete Field", self.create_complete_field, '#27ae60'),
            ("🏃 Test Field", self.create_test_field, '#e67e22'),
            ("🧹 Clear All", self.clear_field, '#e74c3c')
        ]
        
        for text, command, color in quick_buttons:
            tk.Button(quick_frame, text=text, command=command,
                     bg=color, fg='white', font=('Arial', 9, 'bold'),
                     width=20).pack(pady=2, padx=5)
        
        # Field Information
        info_frame = tk.LabelFrame(parent, text="📊 Field Information", 
                                  bg='#34495e', fg='white', font=('Arial', 10, 'bold'))
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(info_frame, text="📋 List Objects", command=self.list_field_objects,
                 width=20).pack(pady=2, padx=5)
        
        tk.Button(info_frame, text="📊 Statistics", command=self.show_statistics,
                 width=20).pack(pady=2, padx=5)
        
        # String Input
        string_frame = tk.LabelFrame(parent, text="📝 String Input", 
                                    bg='#34495e', fg='white', font=('Arial', 10, 'bold'))
        string_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.string_text = tk.Text(string_frame, height=6, font=('Consolas', 8))
        self.string_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Insert default example
        default_example = """0-H-0-0-0
H-H-0-B.80-0
H-H-0-0-0
0-0-0-0-M1
M2-0-0-0-0"""
        self.string_text.insert(tk.END, default_example)
        
        tk.Button(string_frame, text="🎨 Create from String", 
                 command=self.create_from_string,
                 bg='#9b59b6', fg='white', font=('Arial', 9, 'bold'),
                 width=20).pack(pady=2, padx=5)
        
        tk.Button(string_frame, text="📄 Grid to String", 
                 command=self.grid_to_string,
                 bg='#34495e', fg='white', font=('Arial', 9, 'bold'),
                 width=20).pack(pady=2, padx=5)
        
        # Output Log
        log_frame = tk.LabelFrame(parent, text="📝 Output Log", 
                                 bg='#34495e', fg='white', font=('Arial', 10, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            log_frame, 
            height=8, 
            font=('Consolas', 8),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_status_bar(self):
        """ตั้งค่า status bar"""
        status_frame = tk.Frame(self.root, bg='#2c3e50', height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame, 
            text="🔄 Initializing...", 
            bg='#2c3e50', 
            fg='#bdc3c7',
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Tool info
        self.tool_info_label = tk.Label(
            status_frame, 
            text=f"🛠️ Selected: {self.selected_tool}", 
            bg='#2c3e50', 
            fg='#bdc3c7',
            font=('Arial', 9)
        )
        self.tool_info_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def draw_field_grid(self):
        """วาดตาราง 5x5 field"""
        self.field_canvas.delete("all")
        
        canvas_width = self.field_canvas.winfo_width()
        canvas_height = self.field_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.draw_field_grid)
            return
        
        # คำนวณขนาดช่อง
        margin = 20
        grid_size = min(canvas_width - 2*margin, canvas_height - 2*margin)
        cell_size = grid_size // 5
        start_x = (canvas_width - grid_size) // 2
        start_y = (canvas_height - grid_size) // 2
        
        self.cell_size = cell_size
        self.start_x = start_x
        self.start_y = start_y
        
        # สีสำหรับแต่ละประเภท
        colors = {
            '0': '#ecf0f1',     # ว่าง
            'B.80': '#8b4513',     # กล่อง 80cm
            'B.160': '#654321',    # กล่อง 160cm
            'B.240': '#3e2723',    # กล่อง 240cm
            'B.[P': '#ff6b6b',   # Box Left Image
            'B.P]': '#ff8e8e',   # Box Right Image
            'B.P^': '#ffb3b3',   # Box Top Image
            'B.P_': '#ffd9d9',   # Box Bottom Image
            'Q': '#4a90e2',      # QR Code Box 230cm
            'M1': '#e74c3c',    # Mission pad 1
            'M2': '#27ae60',    # Mission pad 2  
            'M3': '#3498db',    # Mission pad 3
            'M4': '#f1c40f',    # Mission pad 4
            'M5': '#9b59b6',    # Mission pad 5
            'M6': '#1abc9c',    # Mission pad 6
            'M7': '#e67e22',    # Mission pad 7
            'M8': '#95a5a6',    # Mission pad 8
            'H': '#2ecc71',     # Pingpong Zone
            'H.': '#27ae60',    # Pingpong + balls
            'D': '#34495e'      # Drone
        }
        
        # วาดช่องตาราง
        for row in range(5):
            for col in range(5):
                x = start_x + col * cell_size
                y = start_y + row * cell_size
                
                cell_type = self.field_grid[row][col]
                color = colors.get(cell_type, '#ecf0f1')
                
                # วาดช่อง
                self.field_canvas.create_rectangle(
                    x, y, x + cell_size, y + cell_size,
                    fill=color, outline='#34495e', width=2,
                    tags=f"cell_{row}_{col}"
                )
                
                # เพิ่มข้อความ
                text_color = '#2c3e50' if cell_type in ['0', 'M4'] else 'white'
                self.field_canvas.create_text(
                    x + cell_size//2, y + cell_size//2,
                    text=cell_type if cell_type != '0' else f"({col},{row})",
                    fill=text_color, font=('Arial', 10, 'bold'),
                    tags=f"text_{row}_{col}"
                )
    
    def on_canvas_click(self, event):
        """จัดการการคลิกบน canvas"""
        if not hasattr(self, 'cell_size'):
            return
        
        # คำนวณตำแหน่งช่อง
        x = event.x - self.start_x
        y = event.y - self.start_y
        
        if x < 0 or y < 0:
            return
        
        col = x // self.cell_size
        row = y // self.cell_size
        
        if 0 <= row < 5 and 0 <= col < 5:
            self.field_grid[row][col] = self.selected_tool
            self.draw_field_grid()
            self.log_message(f"🎨 Placed {self.selected_tool} at ({col},{row})")
    
    def on_canvas_drag(self, event):
        """จัดการการลากบน canvas"""
        self.on_canvas_click(event)
    
    def on_canvas_resize(self, event):
        """จัดการการเปลี่ยนขนาด canvas"""
        self.draw_field_grid()
    
    def select_tool(self, tool):
        """เลือกเครื่องมือ"""
        self.selected_tool = tool
        
        # อัพเดทสีปุ่ม
        for tool_id, btn in self.tool_buttons.items():
            if tool_id == tool:
                btn.config(bg='#3498db')
            else:
                btn.config(bg='#7f8c8d')
        
        self.tool_info_label.config(text=f"🛠️ Selected: {tool}")
        self.log_message(f"🛠️ Selected tool: {tool}")
    
    def random_fill(self):
        """เติมตาราง randomly"""
        tools = ['B.80', 'B.[P', 'B.P]', 'B.P^', 'B.P_', 'Q', 'M1', 'M2', 'M3', 'M4', 'H', 'H.', '0', '0', '0']  # เพิ่ม QR Code Box และช่องว่างให้มากขึ้น
        
        for row in range(5):
            for col in range(5):
                self.field_grid[row][col] = random.choice(tools)
        
        self.draw_field_grid()
        self.log_message("🎲 Generated random field layout")
    
    def clear_grid(self):
        """ล้างตาราง"""
        for row in range(5):
            for col in range(5):
                self.field_grid[row][col] = '0'
        
        self.draw_field_grid()
        self.log_message("🧹 Cleared grid layout")
    
    def grid_to_string(self):
        """แปลงตารางเป็น string"""
        field_string = '\n'.join(['-'.join(row) for row in self.field_grid])
        self.string_text.delete(1.0, tk.END)
        self.string_text.insert(1.0, field_string)
        self.log_message("📄 Converted grid to string format")
    
    def build_field_from_grid(self):
        """สร้างสนามจากตาราง"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        # Convert grid to proper format with dashes
        field_string = '\n'.join(['-'.join(row) for row in self.field_grid])
        
        try:
            self.update_status("🏗️ Building field from grid...")
            self.log_message("🏗️ Building field from visual grid...")
            
            def build_field():
                try:
                    # เริ่ม simulation ก่อน (ถ้ายังไม่ได้เริ่ม)
                    if not self.is_simulation_running:
                        self.field_manager.start_simulation()
                        self.is_simulation_running = True
                        self.log_message("✅ Simulation started")
                    
                    # สร้างพื้นสนามก่อน
                    self.field_manager.create_tiled_floor()
                    self.log_message("✅ Created tiled floor")
                    
                    # จากนั้นสร้างวัตถุในสนาม
                    self.field_manager.create_field_from_string(field_string)
                    self.log_message("✅ Field built successfully from grid")
                    self.update_status("✅ Field Built")
                except Exception as e:
                    self.log_message(f"❌ Error building field: {e}")
                    self.update_status("❌ Build Error")
            
            threading.Thread(target=build_field, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Error: {e}")
            self.update_status("❌ Error")
    
    def create_from_string(self):
        """สร้างสนามจาก string input"""
        field_string = self.string_text.get(1.0, tk.END).strip()
        
        if not field_string:
            messagebox.showwarning("Warning", "Please enter a field string")
            return
        
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.update_status("🎨 Creating field from string...")
            self.log_message(f"🎨 Creating field from string:\n{field_string}")
            
            def create_field():
                try:
                    # เริ่ม simulation ก่อน (ถ้ายังไม่ได้เริ่ม)
                    if not self.is_simulation_running:
                        self.field_manager.start_simulation()
                        self.is_simulation_running = True
                        self.log_message("✅ Simulation started")
                    
                    # สร้างพื้นสนามก่อน
                    self.field_manager.create_tiled_floor()
                    self.log_message("✅ Created tiled floor")
                    
                    # จากนั้นสร้างวัตถุในสนาม
                    self.field_manager.create_field_from_string(field_string)
                    self.log_message("✅ Field created from string")
                    self.update_status("✅ String Field Created")
                    
                    # อัพเดทตาราง
                    lines = field_string.strip().split('\n')
                    for row, line in enumerate(lines[:5]):
                        for col, char in enumerate(line[:5]):
                            if row < 5 and col < 5:
                                self.field_grid[row][col] = char
                    self.draw_field_grid()
                    
                except Exception as e:
                    self.log_message(f"❌ Error creating field: {e}")
                    self.update_status("❌ Error")
            
            threading.Thread(target=create_field, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Error: {e}")
            self.update_status("❌ Error")
    
    # เมธอดอื่นๆ (เหมือนกับ GUI ปกติ)
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
    
    def create_default_field(self):
        """สร้างสนามแบบ default preset"""
        if not self.field_manager:
            messagebox.showerror("Error", "Field Manager not initialized")
            return
        
        try:
            self.update_status("🏗️ Creating default field...")
            self.log_message("🏗️ Creating default preset field...")
            
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
    
    def clear_field(self):
        """ล้างสนามทั้งหมด - ทั้งใน simulation และ visual grid"""
        result = messagebox.askyesno("Clear All Confirmation", 
                                   "Are you sure you want to clear everything?\n\n" +
                                   "This will remove:\n" +
                                   "• All objects from simulation field\n" +
                                   "• All visual grid layout\n" +
                                   "• Reset simulation state\n" +
                                   "• Clear log messages\n" +
                                   "• Reset the entire field to empty state")
        if result:
            try:
                self.update_status("🧹 Clearing everything...")
                
                # 1. ล้าง visual grid ก่อน
                for row in range(5):
                    for col in range(5):
                        self.field_grid[row][col] = '0'
                
                # 2. อัพเดท visual display
                self.draw_field_grid()
                
                # 3. ล้าง simulation field (ถ้ามี field manager)
                if self.field_manager:
                    self.field_manager.clear_field()
                    self.log_message("✅ Simulation field cleared")
                    
                    # 3.1 ล้าง ImageBoard objects โดยเฉพาะ (double-check)
                    try:
                        import re
                        sim = self.field_manager.sim_manager.sim
                        
                        # หา objects ที่มีชื่อขึ้นต้นด้วย "ImageBoard_"
                        all_objects = sim.getObjectsInTree(sim.handle_scene)
                        imageboard_handles = []
                        
                        for obj_handle in all_objects:
                            try:
                                obj_name = sim.getObjectAlias(obj_handle)
                                if obj_name and obj_name.startswith("ImageBoard_"):
                                    imageboard_handles.append(obj_handle)
                            except:
                                continue
                        
                        # ลบ ImageBoard objects ที่เหลือ
                        if imageboard_handles:
                            sim.removeObjects(imageboard_handles)
                            self.log_message(f"🖼️ Cleared {len(imageboard_handles)} additional ImageBoard objects")
                        else:
                            self.log_message("🖼️ No additional ImageBoard objects found")
                            
                    except Exception as e:
                        self.log_message(f"⚠️ Warning clearing ImageBoards: {e}")
                
                # 4. รีเซ็ต simulation state
                if hasattr(self, 'is_simulation_running'):
                    self.is_simulation_running = False
                
                # 5. รีเซ็ต selected tool เป็นค่าเริ่มต้น
                self.select_tool('B.80')
                
                # 6. ล้าง log output
                if hasattr(self, 'output_text'):
                    self.output_text.delete(1.0, tk.END)
                
                self.log_message("✅ Everything cleared successfully!")
                self.log_message("🔄 Field reset to empty state")
                self.update_status("✅ All Cleared")
                
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
    
    def save_design(self):
        """บันทึกการออกแบบ"""
        filename = filedialog.asksaveasfilename(
            title="Save Field Design",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                design = {
                    "grid": self.field_grid,
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0"
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(design, f, indent=2, ensure_ascii=False)
                self.log_message(f"💾 Design saved to: {filename}")
                self.update_status("💾 Design Saved")
            except Exception as e:
                self.log_message(f"❌ Error saving design: {e}")
                self.update_status("❌ Save Error")
    
    def load_design(self):
        """โหลดการออกแบบ"""
        filename = filedialog.askopenfilename(
            title="Load Field Design",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    design = json.load(f)
                
                if 'grid' in design:
                    self.field_grid = design['grid']
                    self.draw_field_grid()
                    self.grid_to_string()
                    
                self.log_message(f"📁 Design loaded from: {filename}")
                self.update_status("📁 Design Loaded")
            except Exception as e:
                self.log_message(f"❌ Error loading design: {e}")
                self.update_status("❌ Load Error")
    
    # ===========================================
    # Python Code Runner Methods
    # ===========================================
    
    def add_welcome_code(self):
        """เพิ่มโค้ดต้อนรับ"""
        welcome_code = '''# 🐍 Python Code Runner - Drone Odyssey Field Creator
# Welcome to the integrated Python code runner!
# 
# Features:
# - Run Python code with real-time output
# - Syntax highlighting and checking
# - File operations (New, Open, Save)
# - Package installation
# - Access to field manager through 'self.field_manager'
# 
# Example 1: Basic Python
print("Hello from Drone Odyssey! 🚁")
print("Python version:", __import__('sys').version)

# Example 2: Working with field manager (if available)
# Note: You can access the field manager through the parent GUI
# import math
# print(f"Pi = {math.pi}")
# print(f"Square root of 16 = {math.sqrt(16)}")

# Example 3: Loop example
for i in range(5):
    print(f"Count: {i}")

# Happy coding! 🚀
'''
        self.code_editor.insert('1.0', welcome_code)
        self.update_line_numbers()
    
    def new_code_file(self):
        """สร้างไฟล์โค้ดใหม่"""
        if self.confirm_unsaved_code_changes():
            self.code_editor.delete('1.0', tk.END)
            self.current_code_file = None
            self.append_code_output("📄 New code file created\n", "info")
            self.update_line_numbers()
    
    def open_code_file(self):
        """เปิดไฟล์โค้ด"""
        if self.confirm_unsaved_code_changes():
            file_path = filedialog.askopenfilename(
                title="Open Python File",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    self.code_editor.delete('1.0', tk.END)
                    self.code_editor.insert('1.0', content)
                    self.current_code_file = file_path
                    self.append_code_output(f"📁 Opened: {os.path.basename(file_path)}\n", "info")
                    self.update_line_numbers()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open file:\n{e}")
    
    def save_code_file(self):
        """บันทึกไฟล์โค้ด"""
        if self.current_code_file:
            self.save_code_to_file(self.current_code_file)
        else:
            self.save_code_as_file()
    
    def save_code_as_file(self):
        """บันทึกไฟล์โค้ดเป็น"""
        file_path = filedialog.asksaveasfilename(
            title="Save Python File",
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path:
            self.save_code_to_file(file_path)
            self.current_code_file = file_path
    
    def save_code_to_file(self, file_path):
        """บันทึกเนื้อหาโค้ดลงไฟล์"""
        try:
            content = self.code_editor.get('1.0', tk.END)[:-1]  # Remove last newline
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.append_code_output(f"💾 Saved: {os.path.basename(file_path)}\n", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def confirm_unsaved_code_changes(self):
        """ยืนยันการเปลี่ยนแปลงที่ยังไม่บันทึก"""
        # Simplified version - you might want to track actual changes
        return True
    
    def run_python_code(self):
        """รันโค้ด Python"""
        if self.is_code_running:
            messagebox.showwarning("Warning", "Code is already running!")
            return
        
        code = self.code_editor.get('1.0', tk.END).strip()
        if not code:
            messagebox.showwarning("Warning", "No code to run!")
            return
        
        # Create temp file
        try:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
            
            # Add field manager access to the code
            enhanced_code = f'''
# Auto-generated field manager access
import sys
import os
sys.path.append(r"{os.path.dirname(os.path.abspath(__file__))}")

try:
    from create_field import FieldManager
    # Create field manager instance if not exists
    if 'field_manager' not in globals():
        field_manager = FieldManager()
        print("✅ Field manager available as 'field_manager'")
except Exception as e:
    print(f"⚠️ Field manager not available: {{e}}")
    field_manager = None

# User code starts here
{code}
'''
            
            temp_file.write(enhanced_code)
            temp_file.close()
            
            # Run in thread
            thread = threading.Thread(target=self._run_python_code_thread, args=(temp_file.name,))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create temp file:\n{e}")
    
    def _run_python_code_thread(self, file_path):
        """รันโค้ดใน Thread แยก"""
        self.is_code_running = True
        self.run_code_btn.config(state=tk.DISABLED)
        self.stop_code_btn.config(state=tk.NORMAL)
        
        try:
            # Clear output
            self.clear_code_output()
            self.append_code_output("🚀 Running Python code...\n", "info")
            self.append_code_output("=" * 50 + "\n", "info")
            
            # Run Python script
            self.code_process = subprocess.Popen(
                [sys.executable, file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Read output in real-time
            while True:
                output = self.code_process.stdout.readline()
                if output == '' and self.code_process.poll() is not None:
                    break
                if output:
                    self.append_code_output(output, "normal")
            
            # Get any remaining output
            stdout, stderr = self.code_process.communicate()
            if stdout:
                self.append_code_output(stdout, "normal")
            if stderr:
                self.append_code_output(stderr, "error")
            
            # Show completion
            return_code = self.code_process.returncode
            self.append_code_output(f"\n{'='*50}\n", "info")
            if return_code == 0:
                self.append_code_output("✅ Code execution completed successfully!\n", "info")
            else:
                self.append_code_output(f"❌ Code execution failed with return code: {return_code}\n", "error")
            
        except Exception as e:
            self.append_code_output(f"❌ Execution error: {str(e)}\n", "error")
        
        finally:
            self.is_code_running = False
            self.run_code_btn.config(state=tk.NORMAL)
            self.stop_code_btn.config(state=tk.DISABLED)
            self.code_process = None
            
            # Clean up temp file
            try:
                os.unlink(file_path)
            except:
                pass
    
    def stop_python_code(self):
        """หยุดการทำงานของโค้ด"""
        if self.code_process:
            self.code_process.terminate()
            self.append_code_output("\n⚠️ Code execution stopped by user!\n", "warning")
            self.is_code_running = False
            self.run_code_btn.config(state=tk.NORMAL)
            self.stop_code_btn.config(state=tk.DISABLED)
    
    def clear_code_output(self):
        """ล้าง Output"""
        self.code_output.config(state=tk.NORMAL)
        self.code_output.delete('1.0', tk.END)
        self.code_output.config(state=tk.DISABLED)
    
    def append_code_output(self, text, tag="normal"):
        """เพิ่มข้อความใน Output"""
        self.code_output.config(state=tk.NORMAL)
        self.code_output.insert(tk.END, text, tag)
        self.code_output.see(tk.END)
        self.code_output.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def check_python_syntax(self):
        """ตรวจสอบ Syntax"""
        code = self.code_editor.get('1.0', tk.END)
        try:
            compile(code, '<string>', 'exec')
            self.append_code_output("✅ Syntax is correct!\n", "info")
        except SyntaxError as e:
            self.append_code_output(f"❌ Syntax error at line {e.lineno}: {e.msg}\n", "error")
    
    def install_python_package(self):
        """ติดตั้ง Python Package"""
        package_dialog = tk.Toplevel(self.root)
        package_dialog.title("Install Python Package")
        package_dialog.geometry("400x150")
        package_dialog.configure(bg='#2c3e50')
        package_dialog.transient(self.root)
        package_dialog.grab_set()
        
        tk.Label(package_dialog, text="Package name:", 
                bg='#2c3e50', fg='white', font=('Arial', 10)).pack(pady=10)
        
        package_entry = tk.Entry(package_dialog, width=40, font=('Arial', 10))
        package_entry.pack(pady=5)
        package_entry.focus()
        
        def install():
            package_name = package_entry.get().strip()
            if package_name:
                package_dialog.destroy()
                self.append_code_output(f"📦 Installing package: {package_name}\n", "info")
                
                # Install in thread
                thread = threading.Thread(target=self._install_package_thread, args=(package_name,))
                thread.daemon = True
                thread.start()
        
        tk.Button(package_dialog, text="Install", command=install,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold')).pack(pady=10)
        
        package_entry.bind('<Return>', lambda e: install())
    
    def _install_package_thread(self, package_name):
        """ติดตั้ง Package ใน Thread แยก"""
        try:
            process = subprocess.Popen(
                [sys.executable, '-m', 'pip', 'install', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.append_code_output(f"✅ Successfully installed {package_name}\n", "info")
                self.append_code_output(stdout, "normal")
            else:
                self.append_code_output(f"❌ Failed to install {package_name}\n", "error")
                self.append_code_output(stderr, "error")
                
        except Exception as e:
            self.append_code_output(f"❌ Installation error: {str(e)}\n", "error")
    
    def on_code_changed(self, event=None):
        """เมื่อโค้ดมีการเปลี่ยนแปลง"""
        self.update_line_numbers()
    
    def update_line_numbers(self):
        """อัพเดท Line Numbers"""
        line_count = int(self.code_editor.index('end-1c').split('.')[0])
        line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', line_numbers_string)
        self.line_numbers.config(state='disabled')


def main():
    """ฟังก์ชันหลัก"""
    root = tk.Tk()
    app = AdvancedFieldCreatorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Application error: {e}")


if __name__ == "__main__":
    main()
