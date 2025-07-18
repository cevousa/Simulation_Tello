#!/usr/bin/env python3
"""
PyInstaller Build Script
สคริปต์สำหรับสร้างไฟล์ .exe
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def create_pyinstaller_spec():
    """สร้างไฟล์ .spec สำหรับ PyInstaller"""
    print("📝 Creating PyInstaller spec file...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['protected_build/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('protected_build/mission_pad_templates', 'mission_pad_templates'),
        ('protected_build/export_model', 'export_model'),
        ('protected_build/Qrcode', 'Qrcode'),
        ('protected_build/captured_images', 'captured_images'),
        ('protected_build/requirements.txt', '.'),
        ('protected_build/create_field', 'create_field'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'cv2',
        'numpy',
        'zmq',
        'cryptography',
        'cryptography.fernet',
        'json',
        'hashlib',
        'datetime',
        'uuid',
        'platform',
        'subprocess',
        'threading'
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
    [],
    exclude_binaries=True,
    name='DroneOdysseyFieldCreator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # ไม่แสดง console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DroneOdysseyFieldCreator',
)
'''
    
    with open("drone_odyssey.spec", 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("  ✅ Spec file created: drone_odyssey.spec")

def create_app_icon():
    """สร้างไอคอนสำหรับแอป (ถ้ายังไม่มี)"""
    if not os.path.exists("app_icon.ico"):
        print("ℹ️ No icon file found. You can add 'app_icon.ico' for custom icon.")
    else:
        print("✅ App icon found: app_icon.ico")

def build_executable():
    """สร้างไฟล์ .exe ด้วย PyInstaller"""
    print("🔨 Building executable with PyInstaller...")
    
    try:
        # ลบไดเรกทอรีเก่า
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("build"):
            shutil.rmtree("build")
        
        # รัน PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "drone_odyssey.spec"
        ]
        
        print("  Running PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ Build successful!")
            return True
        else:
            print(f"  ❌ Build failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"  ❌ Build error: {e}")
        return False

def create_installer_script():
    """สร้างสคริปต์ติดตั้ง"""
    print("📦 Creating installer script...")
    
    installer_content = '''@echo off
echo ================================================
echo  Drone Odyssey Field Creator - Installer
echo ================================================
echo.

set "INSTALL_DIR=%PROGRAMFILES%\\DroneOdysseyFieldCreator"
set "DESKTOP_SHORTCUT=%USERPROFILE%\\Desktop\\Drone Odyssey Field Creator.lnk"
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Drone Odyssey Field Creator.lnk"

echo Installing to: %INSTALL_DIR%
echo.

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Copying application files...
xcopy /E /I /Y "DroneOdysseyFieldCreator" "%INSTALL_DIR%"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\DroneOdysseyFieldCreator.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\DroneOdysseyFieldCreator.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo ================================================
echo  Installation completed successfully!
echo ================================================
echo.
echo Desktop shortcut: %DESKTOP_SHORTCUT%
echo Start menu: %START_MENU%
echo Installation folder: %INSTALL_DIR%
echo.
echo You can now run the application from desktop or start menu.
echo.
pause
'''
    
    with open("dist/install.bat", 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print("  ✅ Installer script created: dist/install.bat")

def create_uninstaller():
    """สร้างสคริปต์ถอนการติดตั้ง"""
    print("🗑️ Creating uninstaller...")
    
    uninstaller_content = '''@echo off
echo ================================================
echo  Drone Odyssey Field Creator - Uninstaller
echo ================================================
echo.

set "INSTALL_DIR=%PROGRAMFILES%\\DroneOdysseyFieldCreator"
set "DESKTOP_SHORTCUT=%USERPROFILE%\\Desktop\\Drone Odyssey Field Creator.lnk"
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Drone Odyssey Field Creator.lnk"

echo This will remove Drone Odyssey Field Creator from your system.
echo Installation folder: %INSTALL_DIR%
echo.
set /p "confirm=Are you sure you want to uninstall? (Y/N): "

if /I "%confirm%" NEQ "Y" (
    echo Uninstallation cancelled.
    pause
    exit /b
)

echo.
echo Removing application files...

REM Remove shortcuts
if exist "%DESKTOP_SHORTCUT%" del "%DESKTOP_SHORTCUT%"
if exist "%START_MENU%" del "%START_MENU%"

REM Remove installation directory
if exist "%INSTALL_DIR%" rmdir /S /Q "%INSTALL_DIR%"

echo.
echo ================================================
echo  Uninstallation completed successfully!
echo ================================================
echo.
pause
'''
    
    # วางใน installation directory
    install_dir = "dist/DroneOdysseyFieldCreator"
    if os.path.exists(install_dir):
        with open(f"{install_dir}/uninstall.bat", 'w', encoding='utf-8') as f:
            f.write(uninstaller_content)
        print("  ✅ Uninstaller created: dist/DroneOdysseyFieldCreator/uninstall.bat")

def create_readme():
    """สร้างไฟล์ README สำหรับการติดตั้ง"""
    print("📋 Creating installation README...")
    
    readme_content = '''# Drone Odyssey Field Creator - Installation Guide

## เกี่ยวกับโปรแกรม
โปรแกรมสร้างสนามสำหรับการแข่งขัน Drone Odyssey Challenge พร้อมระบบ License

## การติดตั้ง

### วิธีที่ 1: ติดตั้งอัตโนมัติ
1. Double-click ไฟล์ `install.bat`
2. ปฏิบัติตามคำแนะนำบนหน้าจอ
3. โปรแกรมจะถูกติดตั้งใน Program Files
4. Shortcut จะถูกสร้างบน Desktop และ Start Menu

### วิธีที่ 2: ติดตั้งด้วยตนเอง
1. คัดลอกโฟลเดอร์ `DroneOdysseyFieldCreator` ไปยังตำแหน่งที่ต้องการ
2. สร้าง Shortcut ของ `DroneOdysseyFieldCreator.exe`
3. Run โปรแกรมจาก Shortcut

## การใช้งาน

### เริ่มต้นใช้งาน
1. เปิดโปรแกรม
2. ใส่ License Key ที่ได้รับ
3. เลือก Interface ที่ต้องการใช้งาน

### License Key
- โปรแกรมต้องการ License Key ถูกต้องเพื่อใช้งาน
- License Key จะผูกกับเครื่องที่ติดตั้ง
- ติดต่อผู้พัฒนาเพื่อขอ License Key

### Interface ที่มี
- **Advanced GUI**: Editor แบบ Visual พร้อม Drag & Drop
- **Basic GUI**: Panel ควบคุมแบบเรียบง่าย  
- **Console Interface**: Interface แบบ Text-based

## การถอนการติดตั้ง
1. ไปที่โฟลเดอร์ติดตั้ง (Program Files\\DroneOdysseyFieldCreator)
2. Double-click `uninstall.bat`
3. ปฏิบัติตามคำแนะนำ

## ข้อกำหนดระบบ
- Windows 10/11
- ไม่ต้องติดตั้ง Python (Built-in)
- RAM: 2GB ขึ้นไป
- HDD: 500MB พื้นที่ว่าง

## การติดต่อ
หากมีปัญหาการใช้งานสามารถติดต่อผู้พัฒนาได้

## เวอร์ชัน
Version: 2.0 Protected
Date: July 2025
'''
    
    with open("dist/README.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("  ✅ README created: dist/README.txt")

def main():
    """ฟังก์ชันหลัก"""
    print("🔨 PyInstaller Build Setup")
    print("=" * 40)
    
    # ตรวจสอบว่ามี protected files หรือไม่
    if not os.path.exists("protected_build"):
        print("❌ Protected build directory not found!")
        print("Please run pyarmor_setup.py first.")
        return False
    
    try:
        # 1. สร้าง spec file
        create_pyinstaller_spec()
        
        # 2. ตรวจสอบ icon
        create_app_icon()
        
        # 3. Build executable
        if not build_executable():
            return False
        
        # 4. สร้างสคริปต์ติดตั้ง
        create_installer_script()
        
        # 5. สร้าง uninstaller
        create_uninstaller()
        
        # 6. สร้าง README
        create_readme()
        
        print("\\n✅ Build completed successfully!")
        print("📁 Output directory: dist/")
        print("🚀 Executable: dist/DroneOdysseyFieldCreator/DroneOdysseyFieldCreator.exe")
        print("📦 Installer: dist/install.bat")
        print("📋 README: dist/README.txt")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎉 Ready for distribution!")
    else:
        print("\\n❌ Build failed. Please check errors above.")
    
    input("Press Enter to continue...")
