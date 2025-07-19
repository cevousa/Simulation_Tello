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
import threading

def launch_gui(gui_type):
    """เปิด GUI ตามประเภทที่เลือก"""
    try:
        # สำหรับ exe ไฟล์ ให้ import และรันโดยตรง
        if gui_type == "basic":
            # Try to import and run directly first
            try:
                import field_creator_gui_advanced
                field_creator_gui_advanced.main()
            except:
                # Fallback to subprocess
                subprocess.Popen([sys.executable, "field_creator_gui.py"])
        elif gui_type == "advanced":
            try:
                import field_creator_gui_advanced
                # ปิดหน้าต่าง launcher ก่อน
                root.withdraw()
                field_creator_gui_advanced.main()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load advanced GUI: {e}")
                # Fallback to subprocess
                try:
                    subprocess.Popen([sys.executable, "field_creator_gui_advanced.py"])
                    root.destroy()
                except:
                    messagebox.showerror("Error", "Cannot start advanced GUI")
        elif gui_type == "console":
            try:
                # สำหรับ console mode ให้เปิดใน terminal แยก
                if os.name == 'nt':  # Windows
                    subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', sys.executable, 'run_create_field.py'])
                else:
                    subprocess.Popen([sys.executable, "run_create_field.py"])
                root.destroy()
            except:
                messagebox.showerror("Error", "Cannot start console interface")
        
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

# สร้างหน้าต่างหลัก
root = tk.Tk()
root.title("🏟️ Field Creator Launcher")
root.geometry("500x400")
root.configure(bg='#2c3e50')
root.resizable(False, False)

# หัวข้อ
header_frame = tk.Frame(root, bg='#2c3e50', height=80)
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
button_frame = tk.Frame(root, bg='#2c3e50')
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
    command=lambda: launch_gui("advanced"),
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
    command=lambda: launch_gui("basic"),
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
    command=lambda: launch_gui("console"),
    bg='#7f8c8d',
    fg='white',
    font=('Arial', 11, 'bold'),
    width=35,
    pady=5
).pack(pady=10)

# Footer
footer_frame = tk.Frame(root, bg='#2c3e50', height=50)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
footer_frame.pack_propagate(False)

tk.Button(
    footer_frame,
    text="ℹ️ About",
    command=show_about,
    bg='#95a5a6',
    fg='white',
    font=('Arial', 9),
    width=10
).pack(side=tk.LEFT, padx=20, pady=10)

tk.Button(
    footer_frame,
    text="❌ Exit",
    command=root.destroy,
    bg='#e74c3c',
    fg='white',
    font=('Arial', 9),
    width=10
).pack(side=tk.RIGHT, padx=20, pady=10)

# เริ่มโปรแกรม
if __name__ == "__main__":
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Launcher error: {e}")
