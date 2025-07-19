#!/usr/bin/env python3
"""
Script สำหรับ build exe ของ Drone Simulator Launcher
ใช้ PyInstaller ในการสร้างไฟล์ exe พร้อม dependencies ทั้งหมด

Author: Build Script Generator
Date: July 2025
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """ตรวจสอบว่าติดตั้ง PyInstaller แล้วหรือยัง"""
    # ตรวจสอบผ่านการรันคำสั่งแทนการ import
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PyInstaller พร้อมใช้งาน (เวอร์ชัน: {result.stdout.strip()})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller ไม่พบ กำลังติดตั้ง...")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                                  check=True, capture_output=True, text=True)
            print("✅ ติดตั้ง PyInstaller เรียบร้อย")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ ไม่สามารถติดตั้ง PyInstaller ได้: {e}")
            print("กรุณาติดตั้งด้วยตนเอง: pip install pyinstaller")
            return False

def clean_build_folders():
    """ลบโฟลเดอร์ build และ dist เก่า"""
    folders_to_clean = ["build", "dist", "__pycache__"]
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"🧹 ลบโฟลเดอร์ {folder}")
            shutil.rmtree(folder)

def get_project_files():
    """รวบรวมไฟล์ที่จำเป็นสำหรับโปรเจค"""
    print("🔍 ตรวจสอบไฟล์และโฟลเดอร์ที่มีอยู่...")
    
    # ไฟล์ Python หลัก - ตรวจสอบว่ามีอยู่จริง
    all_python_files = [
        "launcher.py",  # ไฟล์หลัก
        "license_manager.py",
        "license_dialog.py",
        "config.py",
        "drone_commands.py",
        "drone_controller.py", 
        "drone_gui_connector.py",
        "field_creator_gui_advanced.py",
        "improved_mission_pad_detector.py",
        "mission_pad_detector.py",
        "zmqRemoteApi.py"
    ]
    
    # กรองเฉพาะไฟล์ที่มีอยู่จริง
    python_files = []
    for file in all_python_files:
        if os.path.exists(file):
            python_files.append(file)
            print(f"✅ พบไฟล์: {file}")
        else:
            print(f"⚠️  ไม่พบไฟล์: {file} (ข้าม)")
    
    # โฟลเดอร์ที่ต้องรวม - ตรวจสอบว่ามีอยู่จริง
    all_data_folders = [
        ("create_field", "create_field"),
        ("export_model", "export_model"),
        ("keys", "keys"),
        ("mission_pad_templates", "mission_pad_templates"),
        ("Qrcode", "Qrcode")
    ]
    
    print("\n📁 ตรวจสอบโฟลเดอร์:")
    # กรองเฉพาะโฟลเดอร์ที่มีอยู่จริง
    data_folders = []
    for src, dst in all_data_folders:
        full_path = os.path.abspath(src)
        if os.path.exists(src) and os.path.isdir(src):
            data_folders.append((src, dst))
            print(f"✅ พบโฟลเดอร์: {src} -> {full_path}")
            # แสดงเนื้อหาในโฟลเดอร์
            try:
                contents = os.listdir(src)
                print(f"   📋 มีไฟล์/โฟลเดอร์: {len(contents)} รายการ")
                if len(contents) <= 5:  # แสดงเฉพาะถ้าไม่เยอะเกินไป
                    for item in contents[:5]:
                        print(f"      - {item}")
                else:
                    print(f"      - {contents[0]}, {contents[1]}, ... และอีก {len(contents)-2} รายการ")
            except PermissionError:
                print(f"   ⚠️  ไม่สามารถเข้าถึงเนื้อหาใน {src}")
        else:
            print(f"❌ ไม่พบโฟลเดอร์: {src} -> {full_path}")
    
    # ไฟล์เพิ่มเติม - ตรวจสอบว่ามีอยู่จริง
    all_additional_files = [
        ("requirements.txt", "."),
    ]
    
    print("\n📄 ตรวจสอบไฟล์เพิ่มเติม:")
    # กรองเฉพาะไฟล์ที่มีอยู่จริง
    additional_files = []
    for src, dst in all_additional_files:
        if os.path.exists(src):
            additional_files.append((src, dst))
            print(f"✅ พบไฟล์เพิ่มเติม: {src}")
        else:
            print(f"⚠️  ไม่พบไฟล์เพิ่มเติม: {src} (ข้าม)")
    
    print(f"\n📊 สรุป: {len(python_files)} ไฟล์ Python, {len(data_folders)} โฟลเดอร์, {len(additional_files)} ไฟล์เพิ่มเติม")
    return python_files, data_folders, additional_files

def build_exe():
    """สร้างไฟล์ exe"""
    print("🚀 เริ่มสร้าง exe...")
    
    python_files, data_folders, additional_files = get_project_files()
    
    # ตรวจสอบว่ามีไฟล์หลักอย่างน้อย
    if not os.path.exists("launcher.py"):
        print("❌ ไม่พบไฟล์หลัก launcher.py")
        return False
    
    # สร้างคำสั่ง PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",  # ใช้ python -m PyInstaller
        "--onefile",  # สร้างไฟล์เดียว
        "--console",  # แสดง console สำหรับ debug (เปลี่ยนเป็น --windowed หลังจากแก้ไขปัญหา)
        "--name", "DroneSimulatorLauncher",  # ชื่อไฟล์ exe
        "--clean",  # ลบ cache เก่า
        "--noconfirm",  # ไม่ถามยืนยัน
        "--paths", ".",  # เพิ่ม current directory เข้า path
        "--collect-all", "cv2",  # รวม OpenCV ทั้งหมด
        "--collect-all", "numpy",  # รวม NumPy ทั้งหมด
        "--collect-all", "PIL",  # รวม Pillow ทั้งหมด
        "--collect-submodules", "tkinter",  # รวม tkinter submodules
    ]
    
    # เพิ่มโฟลเดอร์ข้อมูล (เฉพาะที่มีอยู่จริง) - ใช้ os.pathsep สำหรับ Windows
    for src_folder, dst_folder in data_folders:
        # ใช้ path separator ที่ถูกต้องสำหรับ Windows
        data_arg = f"{src_folder}{os.pathsep}{dst_folder}"
        cmd.extend(["--add-data", data_arg])
        print(f"📁 เพิ่มโฟลเดอร์: {src_folder} -> {dst_folder}")
    
    # เพิ่มไฟล์เพิ่มเติม (เฉพาะที่มีอยู่จริง)
    for src_file, dst_path in additional_files:
        data_arg = f"{src_file}{os.pathsep}{dst_path}"
        cmd.extend(["--add-data", data_arg])
        print(f"📄 เพิ่มไฟล์: {src_file} -> {dst_path}")
    
    # เพิ่ม hidden imports สำหรับไลบรารีที่อาจไม่ถูกตรวจพบ
    hidden_imports = [
        "tkinter",
        "tkinter.messagebox",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.simpledialog",
        "_tkinter",  # เพิ่ม _tkinter
    ]
    
    # ตรวจสอบและเพิ่ม hidden imports สำหรับไลบรารีที่ติดตั้งแล้ว
    optional_imports = [
        "numpy", 
        "zmq",
        "qrcode",
        "cryptography",
        "jwt",
        "yaml",
        "cbor2",
        "flask",
        "requests"
    ]
    
    # สำหรับ OpenCV และ PIL ใช้ collect-all แล้ว ไม่ต้องใส่ hidden-import
    cv_pil_imports = ["cv2", "PIL", "zxingcpp", "djitellopy"]
    
    for import_name in optional_imports:
        try:
            __import__(import_name)
            hidden_imports.append(import_name)
            print(f"📦 เพิ่ม hidden import: {import_name}")
        except ImportError:
            print(f"⚠️  ไม่พบไลบรารี {import_name} (ข้าม)")
    
    # ตรวจสอบ OpenCV, PIL แยกต่างหาก
    for import_name in cv_pil_imports:
        try:
            __import__(import_name)
            print(f"📦 พบไลบรารี {import_name} (ใช้ collect-all)")
        except ImportError:
            print(f"⚠️  ไม่พบไลบรารี {import_name} (ข้าม)")
    
    # เพิ่ม hidden imports เข้าคำสั่ง
    for import_name in hidden_imports:
        cmd.extend(["--hidden-import", import_name])
    
    # เพิ่มไฟล์หลัก
    cmd.append("launcher.py")
    
    print("\n📋 คำสั่งที่จะรัน:")
    print(" ".join(cmd))
    print()
    
    # รันคำสั่ง
    try:
        print("⏳ กำลัง build... (อาจใช้เวลาสักครู่)")
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print("✅ สร้าง exe สำเร็จ!")
        
        # ตรวจสอบไฟล์ที่สร้างขึ้น
        exe_path = "dist/DroneSimulatorLauncher.exe"
        if os.path.exists(exe_path):
            print(f"📁 ไฟล์ exe อยู่ที่: {os.path.abspath(exe_path)}")
            # แสดงขนาดไฟล์
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📏 ขนาดไฟล์: {size_mb:.2f} MB")
        else:
            print("⚠️  ไม่พบไฟล์ exe ที่สร้างขึ้น")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False
    except FileNotFoundError:
        print("❌ ไม่พบ PyInstaller กรุณาติดตั้งด้วย: pip install pyinstaller")
        return False

def create_spec_file():
    """สร้างไฟล์ .spec สำหรับการปรับแต่งเพิ่มเติม"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('create_field', 'create_field'),
        ('export_model', 'export_model'),
        ('keys', 'keys'),
        ('mission_pad_templates', 'mission_pad_templates'),
        ('Qrcode', 'Qrcode'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.messagebox',
        'cv2',
        'numpy',
        'PIL',
        'zmq',
        'qrcode',
        'zxingcpp',
        'cryptography',
        'jwt',
        'yaml',
        'cbor2',
        'djitellopy',
        'flask',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DroneSimulatorLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open("DroneSimulatorLauncher.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("📝 สร้างไฟล์ DroneSimulatorLauncher.spec แล้ว")
    print("💡 คุณสามารถแก้ไขไฟล์ .spec และรันด้วย: pyinstaller DroneSimulatorLauncher.spec")

def main():
    """ฟังก์ชันหลัก"""
    print("🏗️  Drone Simulator Launcher - Build Script")
    print("=" * 50)
    
    # ตรวจสอบว่าอยู่ในโฟลเดอร์ที่ถูกต้อง
    if not os.path.exists("launcher.py"):
        print("❌ ไม่พบไฟล์ launcher.py")
        print("กรุณารันสคริปต์นี้ในโฟลเดอร์ที่มีไฟล์ launcher.py")
        return False
    
    try:
        # 1. ตรวจสอบ requirements
        if not check_requirements():
            return False
        
        # 2. ลบโฟลเดอร์เก่า
        clean_build_folders()
        
        # 3. สร้างไฟล์ .spec (ทางเลือก)
        create_spec_file()
        
        # 4. สร้าง exe
        if build_exe():
            print("\n🎉 Build เสร็จสิ้น!")
            print("📁 ไฟล์ exe พร้อมใช้งานแล้ว")
            print(f"📍 ตำแหน่ง: {os.path.abspath('dist/DroneSimulatorLauncher.exe')}")
            
            # แสดงขนาดไฟล์
            exe_path = "dist/DroneSimulatorLauncher.exe"
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📏 ขนาดไฟล์: {size_mb:.2f} MB")
            
            return True
        else:
            print("\n❌ Build ไม่สำเร็จ")
            return False
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        input("\n✅ กด Enter เพื่อออก...")
    else:
        input("\n❌ กด Enter เพื่อออก...")
