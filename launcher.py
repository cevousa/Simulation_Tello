#!/usr/bin/env python3
"""
Drone Odyssey Field Creator - GUI Launcher
เครื่องมือเลือกและเปิด GUI ต่างๆ
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

# Import License Manager
try:
    from license_manager import check_license_on_startup, LicenseManager
    LICENSE_AVAILABLE = True
except ImportError:
    LICENSE_AVAILABLE = False
    print("Warning: License system not available")

def check_license():
    """ตรวจสอบและแสดงข้อมูล License"""
    if not LICENSE_AVAILABLE:
        messagebox.showinfo("License", "License system not available")
        return
    
    license_manager = LicenseManager()
    license_info = license_manager.get_license_info()
    
    if license_info["valid"]:
        info_text = f"""License Information:
        
User: {license_info['user_name']}
Email: {license_info['email']}
Type: {license_info['license_type']}
Days Remaining: {license_info['days_left']} days

Features Available:
• Basic Creator: {'✓' if license_info['features'].get('basic_creator') else '✗'}
• Advanced Creator: {'✓' if license_info['features'].get('advanced_creator') else '✗'}
• CoppeliaSim Integration: {'✓' if license_info['features'].get('coppelia_integration') else '✗'}
• Export Function: {'✓' if license_info['features'].get('export_function') else '✗'}"""
    else:
        info_text = f"License Status: Invalid\nError: {license_info.get('error', 'Unknown error')}"
    
    messagebox.showinfo("License Information", info_text)

def launch_gui(gui_type):
    """เปิด GUI ตามประเภทที่เลือก"""
    # ตรวจสอบ License ก่อนเปิด GUI
    if LICENSE_AVAILABLE:
        license_manager = LicenseManager()
        license_info = license_manager.get_license_info()
        
        if not license_info["valid"]:
            response = messagebox.askyesno("License Required", 
                                         "This feature requires a valid license.\n"
                                         "Continue in demo mode?")
            if not response:
                return
    
    try:
        if gui_type == "basic":
            subprocess.Popen([sys.executable, "field_creator_gui.py"])
        elif gui_type == "advanced":
            subprocess.Popen([sys.executable, "field_creator_gui_advanced.py"])
        elif gui_type == "console":
            subprocess.Popen([sys.executable, "run_create_field.py"])
        
        # ปิดหน้าต่าง launcher
        root.destroy()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch {gui_type} interface:\n{e}")

def show_about():
    """แสดงข้อมูลเกี่ยวกับโปรแกรม"""
    about_text = """🏟️ Drone Odyssey Challenge Field Creator

โปรแกรมสร้างสนามสำหรับการแข่งขัน Drone Odyssey Challenge

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

🚀 Version: 2.0
📅 Date: July 2025"""
    
    messagebox.showinfo("About", about_text)

def create_main_window():
    """สร้างหน้าต่างหลัก"""
    global root
    root = tk.Tk()
    root.title("🚁 Drone Odyssey Field Creator")
    root.geometry("500x600")
    root.resizable(False, False)
    
    # Icon (ถ้ามี)
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # Center window
    root.eval('tk::PlaceWindow . center')
    
    # Header
    header_frame = tk.Frame(root, bg="#2E3440", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    title_label = tk.Label(header_frame, 
                          text="🏟️ Drone Odyssey Field Creator", 
                          font=("Arial", 16, "bold"),
                          bg="#2E3440", 
                          fg="white")
    title_label.pack(expand=True)
    
    subtitle_label = tk.Label(header_frame, 
                             text="Create Competition Fields for Drone Racing", 
                             font=("Arial", 10),
                             bg="#2E3440", 
                             fg="#D8DEE9")
    subtitle_label.pack()
    
    # Main content
    main_frame = tk.Frame(root, bg="#ECEFF4", padx=40, pady=30)
    main_frame.pack(fill="both", expand=True)
    
    # Description
    desc_label = tk.Label(main_frame, 
                         text="Choose your preferred interface to start creating drone racing fields:",
                         font=("Arial", 11),
                         bg="#ECEFF4",
                         fg="#2E3440",
                         wraplength=400,
                         justify="center")
    desc_label.pack(pady=(0, 30))
    
    # Buttons
    button_style = {
        "font": ("Arial", 12, "bold"),
        "width": 25,
        "height": 2,
        "relief": "flat",
        "cursor": "hand2"
    }
    
    # Basic GUI Button
    basic_btn = tk.Button(main_frame,
                         text="🎨 Visual Field Designer",
                         command=lambda: launch_gui("basic"),
                         bg="#5E81AC",
                         fg="white",
                         **button_style)
    basic_btn.pack(pady=8)
    
    # Advanced GUI Button  
    advanced_btn = tk.Button(main_frame,
                            text="⚡ Advanced Creator",
                            command=lambda: launch_gui("advanced"),
                            bg="#81A1C1",
                            fg="white",
                            **button_style)
    advanced_btn.pack(pady=8)
    
    # Console Button
    console_btn = tk.Button(main_frame,
                           text="💻 String-based Creator",
                           command=lambda: launch_gui("console"),
                           bg="#88C0D0",
                           fg="white",
                           **button_style)
    console_btn.pack(pady=8)
    
    # Separator
    separator = tk.Frame(main_frame, height=2, bg="#D8DEE9")
    separator.pack(fill="x", pady=20)
    
    # License & About buttons
    button_frame = tk.Frame(main_frame, bg="#ECEFF4")
    button_frame.pack()
    
    license_btn = tk.Button(button_frame,
                           text="🔐 License Info",
                           command=check_license,
                           bg="#A3BE8C",
                           fg="white",
                           font=("Arial", 10),
                           width=12,
                           relief="flat",
                           cursor="hand2")
    license_btn.pack(side="left", padx=5)
    
    about_btn = tk.Button(button_frame,
                         text="ℹ️ About",
                         command=show_about,
                         bg="#EBCB8B",
                         fg="white",
                         font=("Arial", 10),
                         width=12,
                         relief="flat",
                         cursor="hand2")
    about_btn.pack(side="left", padx=5)
    
    # Footer
    footer_label = tk.Label(main_frame,
                           text="© 2025 Drone Odyssey Challenge | Version 2.0",
                           font=("Arial", 8),
                           bg="#ECEFF4",
                           fg="#4C566A")
    footer_label.pack(side="bottom", pady=(30, 0))

def main():
    """ฟังก์ชันหลัก"""
    # ตรวจสอบ License เมื่อเริ่มโปรแกรม
    if LICENSE_AVAILABLE:
        license_status = check_license_on_startup()
        if license_status is False:
            return  # ออกจากโปรแกรมถ้า License ไม่ valid
    
    # สร้างและแสดงหน้าต่างหลัก
    create_main_window()
    root.mainloop()

if __name__ == "__main__":
    main()
