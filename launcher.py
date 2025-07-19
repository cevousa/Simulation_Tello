#!/usr/bin/env python3
"""
Drone Odyssey Field Creator - GUI Launcher (License Protected)
เครื่องมือเลือกและเปิด GUI ต่างๆ พร้อมระบบป้องกันลิขสิทธิ์

Author: Drone Simulation Team
Date: July 2025
License Protection: Enabled
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import threading

# Import license management system - REQUIRED FOR LICENSE PROTECTION
try:
    from license_manager import LicenseManager
    from license_dialog import show_license_activation_dialog
except ImportError:
    messagebox.showerror("Error", "❌ License system not found!\nThis application requires valid licensing.")
    sys.exit(1)


class DroneSimulatorLauncher:
    """
    Main launcher application with license protection.
    Application will not function without a valid license.
    """
    
    def __init__(self):
        # Initialize license manager - CRITICAL FOR PROTECTION
        self.license_manager = LicenseManager()
        self.root = None
        
        # Check license and handle activation
        self._handle_license_validation()
    
    def _handle_license_validation(self):
        """Handle license validation and activation process."""
        if self._validate_license_strict():
            # License is valid, create UI directly
            self._create_main_ui()
        else:
            # No valid license, show activation dialog with callback
            if show_license_activation_dialog(success_callback=self._create_main_ui):
                # License activated successfully and UI already created
                pass
            else:
                # User cancelled or activation failed, exit
                sys.exit(1)
    
    def _create_main_ui(self):
        """Create the main application UI."""
        if self.root is None:
            self.root = tk.Tk()
            self.setup_ui()
        else:
            # If root already exists (shouldn't happen in current flow)
            self.root.deiconify()
    
    def _validate_license_strict(self):
        """Strict license validation - returns True only if license is valid."""
        try:
            return self.license_manager.validate_license(show_errors=False)
        except:
            return False
    
    def setup_ui(self):
        """Setup the main launcher UI."""
        self.root.title("🏟️ Field Creator Launcher (Licensed)")
        self.root.geometry("500x450")  # Increased height for license info
        self.root.configure(bg='#2c3e50')
        self.root.resizable(False, False)
        
        # License verification during runtime
        self.root.after(30000, self._periodic_license_check)  # Check every 30 seconds
        
        # หัวข้อ
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X, pady=10)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🏟️ Drone Simulator",
            font=('Arial', 18, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack(pady=5)

        subtitle_label = tk.Label(
            header_frame,
            text="Choose your preferred interface",
            font=('Arial', 12),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        subtitle_label.pack()
        
        # License status display
        self._add_license_status()

        # ปุ่มเลือก GUI
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=15)

        # GUI แบบ Advanced (แนะนำ)
        advanced_frame = tk.Frame(button_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        advanced_frame.pack(fill=tk.X, pady=8)

        tk.Label(
            advanced_frame,
            text="🎨 Advanced Visual Designer",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        ).pack(pady=8)

        tk.Label(
            advanced_frame,
            text="Interactive grid editor with drag & drop\nVisual field preview and design tools\nBest for creating custom fields",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e',
            justify=tk.CENTER
        ).pack(pady=3)

        tk.Button(
            advanced_frame,
            text="🚀 Launch Advanced GUI (Recommended)",
            command=lambda: self.launch_gui_protected("advanced"),
            bg='#27ae60',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=35,
            pady=5
        ).pack(pady=8)

        # GUI แบบ Basic
        basic_frame = tk.Frame(button_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        basic_frame.pack(fill=tk.X, pady=8)

        tk.Label(
            basic_frame,
            text="📝 Basic Control Panel",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        ).pack(pady=8)

        tk.Label(
            basic_frame,
            text="Simple button interface\nString input dialog\nGood for quick field creation",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e',
            justify=tk.CENTER
        ).pack(pady=3)

        tk.Button(
            basic_frame,
            text="📋 Launch Basic GUI",
            command=lambda: self.launch_gui_protected("basic"),
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=35,
            pady=5
        ).pack(pady=8)

        # Console Interface
        console_frame = tk.Frame(button_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        console_frame.pack(fill=tk.X, pady=8)

        tk.Label(
            console_frame,
            text="⌨️ Console Interface",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        ).pack(pady=8)

        tk.Label(
            console_frame,
            text="Command-line menu interface\nOriginal text-based interface\nFor advanced users",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e',
            justify=tk.CENTER
        ).pack(pady=3)

        tk.Button(
            console_frame,
            text="💻 Launch Console Interface",
            command=lambda: self.launch_gui_protected("console"),
            bg='#7f8c8d',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=35,
            pady=5
        ).pack(pady=8)

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
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Button(
            footer_frame,
            text="🔐 License Info",
            command=self.show_license_info,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 9),
            width=12
        ).pack(side=tk.LEFT, padx=5, pady=10)

        tk.Button(
            footer_frame,
            text="❌ Exit",
            command=self.root.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 9),
            width=10
        ).pack(side=tk.RIGHT, padx=20, pady=10)
    
    def _add_license_status(self):
        """Add license status display to the UI."""
        license_frame = tk.Frame(self.root, bg='#27ae60', height=25)
        license_frame.pack(fill=tk.X, padx=20, pady=5)
        license_frame.pack_propagate(False)
        
        license_info = self.license_manager.get_license_info()
        if license_info:
            status_text = f"✅ Licensed to: {license_info['user']} | Expires: {license_info['expires'].strftime('%Y-%m-%d')}"
        else:
            status_text = "🔓 License Status: Unknown"
        
        tk.Label(
            license_frame,
            text=status_text,
            font=('Arial', 8),
            fg='white',
            bg='#27ae60'
        ).pack(pady=3)
    
    def _periodic_license_check(self):
        """Periodically verify license validity during runtime."""
        if not self._validate_license_strict():
            messagebox.showerror(
                "License Expired", 
                "Your license has expired or become invalid.\nThe application will now close."
            )
            self.root.destroy()
            return
        
        # Schedule next check
        self.root.after(30000, self._periodic_license_check)
    
    def launch_gui_protected(self, gui_type):
        """เปิด GUI ตามประเภทที่เลือก (with license verification)"""
        # Verify license before launching any GUI
        if not self._validate_license_strict():
            messagebox.showerror(
                "License Required", 
                "Valid license required to access this feature.\nPlease activate your license."
            )
            return
        
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
                    self.root.withdraw()
                    field_creator_gui_advanced.main()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load advanced GUI: {e}")
                    # Fallback to subprocess
                    try:
                        subprocess.Popen([sys.executable, "field_creator_gui_advanced.py"])
                        self.root.destroy()
                    except:
                        messagebox.showerror("Error", "Cannot start advanced GUI")
            elif gui_type == "console":
                try:
                    # สำหรับ console mode ให้เปิดใน terminal แยก
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', sys.executable, 'run_create_field.py'])
                    else:
                        subprocess.Popen([sys.executable, "run_create_field.py"])
                    self.root.destroy()
                except:
                    messagebox.showerror("Error", "Cannot start console interface")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {gui_type} interface:\n{e}")

    def show_about(self):
        """แสดงข้อมูลเกี่ยวกับโปรแกรม"""
        about_text = """🏟️ Drone Simulator (Licensed Version)

โปรแกรมสร้างสนามสำหรับการแข่งขัน Drone Simulator
พร้อมระบบป้องกันลิขสิทธิ์

🎯 Features:
• Visual Field Designer
• Interactive Grid Editor  
• String-based Field Creation
• Real-time Field Preview
• CoppeliaSim Integration
• Hardware-bound License Protection

📏 Field Specifications:
• Size: 5.0×5.0 meters
• Tiles: 80×80cm with 20cm gaps
• Objects: Obstacles, Mission Pads, Ping Pong Balls

🔐 Security Features:
• Hardware-bound licensing
• Periodic license validation
• Secure token verification

🚀 Version: 2.0 (Protected)
📅 Date: July 2025"""
        
        messagebox.showinfo("About", about_text)
    
    def show_license_info(self):
        """Show detailed license information."""
        hw_id = self.license_manager.generate_hardware_id()
        license_info = self.license_manager.get_license_info()
        
        if license_info:
            info_text = f"""🔐 License Information

Application: Drone Simulator Field Creator
Version: 2.0 (Protected)

Hardware ID: {hw_id}

📋 License Details:
Licensed User: {license_info['user']}
Email: {license_info['email']}
License Type: {license_info.get('license_type', 'Standard')}
Issue Date: {license_info.get('issued', 'N/A')}
Expires: {license_info['expires'].strftime('%Y-%m-%d %H:%M:%S')}
Days Remaining: {license_info['days_remaining']}

Status: ✅ Valid"""
        else:
            info_text = f"""🔐 License Information

Application: Drone Simulator Field Creator
Version: 2.0 (Protected)

Hardware ID: {hw_id}

Status: ❌ No Valid License Found

Please contact support to obtain a license for this hardware ID."""
        
        messagebox.showinfo("License Information", info_text)

    def run(self):
        """Start the application."""
        if self.root:
            self.root.mainloop()


def main():
    """
    Main application entry point with license protection.
    MINIMAL LICENSE INTEGRATION - Just 3 lines needed!
    """
    
    # STEP 1: Import license_manager (done at top)
    # STEP 2: Create app (includes automatic license check)
    # STEP 3: Run app
    
    app = DroneSimulatorLauncher()
    app.run()


# เริ่มโปรแกรม
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        messagebox.showerror("Fatal Error", f"Application failed to start:\n{e}")
