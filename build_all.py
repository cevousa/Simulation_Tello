#!/usr/bin/env python3
"""
All-in-One Build Script
สคริปต์รวมสำหรับสร้างโปรแกรมป้องกันและ .exe
"""

import os
import sys
import subprocess
import time

def print_banner():
    """แสดงแบนเนอร์"""
    print("=" * 60)
    print("🏟️  Drone Odyssey Field Creator - Build System")
    print("=" * 60)
    print("🔒 PyArmor Protection + 📦 PyInstaller Build")
    print("=" * 60)

def check_requirements():
    """ตรวจสอบความพร้อม"""
    print("🔍 Checking requirements...")
    
    required_files = [
        "launcher.py",
        "license_manager.py",
        "protected_launcher.py",
        "field_creator_gui.py",
        "field_creator_gui_advanced.py",
        "create_field"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files found")
    return True

def run_step(step_name, script_name):
    """รันสคริปต์แต่ละขั้นตอน"""
    print(f"\n🚀 {step_name}...")
    print("-" * 40)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {step_name} completed successfully!")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {step_name} failed!")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {step_name} timed out!")
        return False
    except Exception as e:
        print(f"❌ {step_name} error: {e}")
        return False

def create_build_info():
    """สร้างไฟล์ข้อมูล Build"""
    print("📝 Creating build info...")
    
    import datetime
    build_info = f"""Drone Odyssey Field Creator - Build Information
===============================================

Build Date: {datetime.datetime.now().isoformat()}
Version: 2.0 Protected
Python Version: {sys.version}
Platform: {sys.platform}

Build Steps:
1. ✅ PyArmor Protection Applied
2. ✅ PyInstaller Executable Created
3. ✅ Installer Scripts Generated
4. ✅ License System Integrated

Features:
- 🔒 Code Protection with PyArmor
- 📦 Standalone Executable
- 🔑 License Management System
- 🎨 Multiple GUI Interfaces
- 📋 Automatic Installation

Distribution Contents:
- DroneOdysseyFieldCreator.exe (Main Application)
- install.bat (Automatic Installer)
- uninstall.bat (Uninstaller)
- README.txt (Installation Guide)
- license_generator.py (License Key Generator)

Usage:
1. Run install.bat to install the application
2. Use license_generator.py to create license keys
3. Start the application and enter license key
4. Choose preferred interface and start creating fields

Support:
For technical support and license keys, contact the developer.
"""
    
    with open("BUILD_INFO.txt", 'w', encoding='utf-8') as f:
        f.write(build_info)
    
    print("✅ Build info created: BUILD_INFO.txt")

def cleanup_build_files():
    """ทำความสะอาดไฟล์ build"""
    print("🧹 Cleaning up build files...")
    
    cleanup_items = [
        "build",
        "__pycache__",
        "*.pyc",
        "*.pyo"
    ]
    
    for item in cleanup_items:
        if os.path.exists(item):
            if os.path.isdir(item):
                import shutil
                shutil.rmtree(item)
                print(f"  Removed directory: {item}")
            else:
                os.remove(item)
                print(f"  Removed file: {item}")

def show_final_summary():
    """แสดงสรุปผลการ Build"""
    print("\n" + "=" * 60)
    print("🎉 BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n📂 Output Files:")
    print("├── dist/")
    print("│   ├── DroneOdysseyFieldCreator/")
    print("│   │   └── DroneOdysseyFieldCreator.exe")
    print("│   ├── install.bat")
    print("│   └── README.txt")
    print("├── license_generator.py")
    print("└── BUILD_INFO.txt")
    
    print("\n🚀 Next Steps:")
    print("1. Test the executable in dist/DroneOdysseyFieldCreator/")
    print("2. Use license_generator.py to create license keys")
    print("3. Run install.bat to install on target machines")
    print("4. Distribute the dist/ folder to users")
    
    print("\n🔑 License Management:")
    print("- Run: python license_generator.py")
    print("- Enter user details and machine ID")
    print("- Provide generated license key to users")
    
    print("\n📋 User Instructions:")
    print("- Run install.bat on target machine")
    print("- Start application from desktop shortcut")
    print("- Enter license key when prompted")
    print("- Choose GUI interface and start creating fields")

def main():
    """ฟังก์ชันหลัก"""
    print_banner()
    
    # ตรวจสอบความพร้อม
    if not check_requirements():
        print("\n❌ Requirements check failed!")
        input("Press Enter to exit...")
        return
    
    # ขั้นตอนการ Build
    steps = [
        ("PyArmor Protection", "pyarmor_setup.py"),
        ("PyInstaller Build", "pyinstaller_build.py")
    ]
    
    start_time = time.time()
    
    for step_name, script_name in steps:
        if not run_step(step_name, script_name):
            print(f"\n❌ Build failed at: {step_name}")
            input("Press Enter to exit...")
            return
        time.sleep(1)  # หน่วงเวลาเล็กน้อยระหว่างขั้นตอน
    
    # สร้างไฟล์เพิ่มเติม
    create_build_info()
    
    # ทำความสะอาด
    cleanup_build_files()
    
    # แสดงสรุป
    build_time = time.time() - start_time
    print(f"\n⏱️ Total build time: {build_time:.1f} seconds")
    
    show_final_summary()
    
    print("\n" + "=" * 60)
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Build interrupted by user!")
    except Exception as e:
        print(f"\n\n❌ Build error: {e}")
        input("Press Enter to exit...")
