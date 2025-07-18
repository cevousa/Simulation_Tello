#!/usr/bin/env python3
"""
Protected Launcher with License Check
Launcher ที่มีการตรวจสอบ License โดยไม่เปลี่ยน GUI
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

# นำเข้า License Manager
try:
    from license_manager import LicenseManager
except ImportError:
    messagebox.showerror("Error", "License system not found!")
    sys.exit(1)

class ProtectedLauncher:
    def __init__(self):
        self.license_manager = LicenseManager()
        self.license_valid = False
        self.user_features = []
        
    def check_license(self):
        """ตรวจสอบ License ก่อนเริ่มโปรแกรม"""
        is_valid, license_info = self.license_manager.validate_license()
        
        if not is_valid:
            # แสดง Dialog ให้ใส่ License
            if not self.license_manager.show_license_dialog():
                messagebox.showerror("License Required", 
                                   "Valid license is required to run this application.")
                return False
            
            # ตรวจสอบอีกครั้งหลังจากใส่ License
            is_valid, license_info = self.license_manager.validate_license()
        
        if is_valid:
            self.license_valid = True
            self.user_features = license_info.get("features", [])
            return True
        else:
            messagebox.showerror("License Error", 
                               f"License validation failed: {license_info}")
            return False
    
    def launch_gui(self, gui_type):
        """เปิด GUI ตามประเภทที่เลือก (มีการตรวจสอบ License)"""
        if not self.license_valid:
            messagebox.showerror("License Error", "No valid license found!")
            return
        
        # ตรวจสอบ Feature Permission
        feature_map = {
            "basic": "basic_gui",
            "advanced": "advanced_gui", 
            "console": "console_gui"
        }
        
        required_feature = feature_map.get(gui_type)
        if required_feature and required_feature not in self.user_features:
            messagebox.showerror("Feature Not Licensed", 
                               f"Your license does not include access to {gui_type} interface.")
            return
        
        try:
            if gui_type == "basic":
                subprocess.Popen([sys.executable, "field_creator_gui.py"])
            elif gui_type == "advanced":
                subprocess.Popen([sys.executable, "field_creator_gui_advanced.py"])
            elif gui_type == "console":
                subprocess.Popen([sys.executable, "run_create_field.py"])
            
            # ปิดหน้าต่าง launcher
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {gui_type} interface:\n{e}")

    def show_about(self):
        """แสดงข้อมูลเกี่ยวกับโปรแกรม (รวม License Info)"""
        # ข้อมูล License
        license_info = ""
        if self.license_valid:
            is_valid, data = self.license_manager.validate_license()
            if is_valid:
                license_info = f"\n🔒 Licensed to: {data.get('user_name', 'Unknown')}"
        
        about_text = f"""🏟️ Drone Odyssey Challenge Field Creator

โปรแกรมสร้างสนามสำหรับการแข่งขัน Drone Odyssey Challenge{license_info}

🎯 Features:
• Visual Field Designer
• Interactive Grid Editor  
• String-based Field Creation
• Real-time Field Preview
• CoppeliaSim Integration

📏 Field Specifications:
• Size: 5.0×5.0 meters
• Tiles: 80×80cm with 20cm gaps
• Objects: Obstacles, Mission Pads, Ping Pong Balls

🚀 Version: 2.0 Protected
📅 Date: July 2025"""
        
        messagebox.showinfo("About", about_text)

    def show_license_info(self):
        """แสดงข้อมูล License"""
        if not self.license_valid:
            messagebox.showwarning("No License", "No valid license found!")
            return
            
        is_valid, license_data = self.license_manager.validate_license()
        if is_valid:
            import datetime
            expire_date = datetime.datetime.fromisoformat(license_data["expire_date"])
            days_left = (expire_date - datetime.datetime.now()).days
            
            info_text = f"""📄 License Information

👤 User: {license_data.get('user_name', 'Unknown')}
🆔 Machine ID: {license_data.get('machine_id', 'Unknown')[:8]}...
📅 Activated: {license_data.get('activated_date', 'Unknown')[:10]}
⏰ Expires: {license_data.get('expire_date', 'Unknown')[:10]}
📊 Days Remaining: {days_left}
🎯 Features: {', '.join(license_data.get('features', []))}
📦 Version: {license_data.get('version', 'Unknown')}"""
            
            messagebox.showinfo("License Information", info_text)

    def create_gui(self):
        """สร้าง GUI (เหมือนเดิม แต่เพิ่มปุ่ม License Info)"""
        # สร้างหน้าต่างหลัก
        self.root = tk.Tk()
        self.root.title("🏟️ Field Creator Launcher")
        self.root.geometry("500x420")  # เพิ่มความสูงนิดหน่อย
        self.root.configure(bg='#2c3e50')
        self.root.resizable(False, False)

        # หัวข้อ
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X, pady=10)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🏟️ Drone Odyssey Field Creator",
            font=('Arial', 18, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack(pady=10)

        subtitle_label = tk.Label(
            header_frame,
            text="Choose your preferred interface",
            font=('Arial', 12),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        subtitle_label.pack()

        # ปุ่มเลือก GUI
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # GUI แบบ Advanced (แนะนำ)
        advanced_frame = tk.Frame(button_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        advanced_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            advanced_frame,
            text="🎨 Advanced Visual Designer",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        ).pack(pady=10)

        tk.Label(
            advanced_frame,
            text="Interactive grid editor with drag & drop\nVisual field preview and design tools\nBest for creating custom fields",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e',
            justify=tk.CENTER
        ).pack(pady=5)

        tk.Button(
            advanced_frame,
            text="🚀 Launch Advanced GUI (Recommended)",
            command=lambda: self.launch_gui("advanced"),
            bg='#27ae60',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=35,
            pady=5
        ).pack(pady=10)

        # GUI แบบ Basic
        basic_frame = tk.Frame(button_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        basic_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            basic_frame,
            text="📝 Basic Control Panel",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        ).pack(pady=10)

        tk.Label(
            basic_frame,
            text="Simple button interface\nString input dialog\nGood for quick field creation",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e',
            justify=tk.CENTER
        ).pack(pady=5)

        tk.Button(
            basic_frame,
            text="📋 Launch Basic GUI",
            command=lambda: self.launch_gui("basic"),
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=35,
            pady=5
        ).pack(pady=10)

        # Console Interface
        console_frame = tk.Frame(button_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        console_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            console_frame,
            text="⌨️ Console Interface",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        ).pack(pady=10)

        tk.Label(
            console_frame,
            text="Command-line menu interface\nOriginal text-based interface\nFor advanced users",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e',
            justify=tk.CENTER
        ).pack(pady=5)

        tk.Button(
            console_frame,
            text="💻 Launch Console Interface",
            command=lambda: self.launch_gui("console"),
            bg='#7f8c8d',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=35,
            pady=5
        ).pack(pady=10)

        # Footer
        footer_frame = tk.Frame(self.root, bg='#2c3e50', height=50)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)

        tk.Button(
            footer_frame,
            text="ℹ️ About",
            command=self.show_about,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 9),
            width=10
        ).pack(side=tk.LEFT, padx=10, pady=10)

        # เพิ่มปุ่ม License Info
        tk.Button(
            footer_frame,
            text="🔒 License",
            command=self.show_license_info,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 9),
            width=10
        ).pack(side=tk.LEFT, padx=5, pady=10)

        tk.Button(
            footer_frame,
            text="❌ Exit",
            command=self.root.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 9),
            width=10
        ).pack(side=tk.RIGHT, padx=10, pady=10)

    def run(self):
        """เริ่มต้นโปรแกรม"""
        # ตรวจสอบ License ก่อน
        if not self.check_license():
            return
        
        # สร้างและแสดง GUI
        self.create_gui()
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Launcher error: {e}")

if __name__ == "__main__":
    launcher = ProtectedLauncher()
    launcher.run()
