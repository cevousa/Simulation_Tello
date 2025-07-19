# -*- mode: python ; coding: utf-8 -*-
"""
Final Optimized Spec File for Drone Odyssey Launcher
แก้ไขปัญหาทั้งหมดและปรับปรุงให้ใช้งานได้ดีที่สุด
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ตั้งค่า working directory
work_dir = SPECPATH

# รายการไฟล์ Python หลักที่ต้องการ
main_files = [
    'launcher.py',
    'field_creator_gui_advanced.py',
    'field_creator_gui.py',
    'drone_gui_connector.py',
    'drone_connector.py',
    'drone_controller.py',
    'mission_pad_detector.py',
    'improved_mission_pad_detector.py',
    'zmqRemoteApi.py',
    'config.py'
]

# สร้าง datas list
datas = []

# เพิ่มไฟล์ Python หลัก
for py_file in main_files:
    file_path = os.path.join(work_dir, py_file)
    if os.path.exists(file_path):
        datas.append((file_path, '.'))

# เพิ่มโฟลเดอร์ที่จำเป็น
essential_folders = [
    ('create_field', 'create_field'),
    ('mission_pad_templates', 'mission_pad_templates'),
    ('export_model', 'export_model'),
    ('Qrcode', 'Qrcode')
]

for src_folder, dst_folder in essential_folders:
    src_path = os.path.join(work_dir, src_folder)
    if os.path.exists(src_path):
        for root, dirs, files in os.walk(src_path):
            for file in files:
                if not file.endswith('.pyc'):  # ข้าม .pyc files
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, work_dir)
                    rel_dir = os.path.dirname(rel_path)
                    datas.append((file_path, rel_dir))

# เพิ่ม requirements.txt
req_file = os.path.join(work_dir, 'requirements.txt')
if os.path.exists(req_file):
    datas.append((req_file, '.'))

# สร้างโฟลเดอร์ captured_images ถ้าไม่มี
captured_dir = os.path.join(work_dir, 'captured_images')
if not os.path.exists(captured_dir):
    os.makedirs(captured_dir)

# Hidden imports ที่จำเป็น
hiddenimports = [
    # Tkinter และ GUI
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    'tkinter.font',
    
    # การประมวลผลภาพ
    'cv2',
    'numpy',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    
    # QR Code (แต่ไม่รวม pyzbar เพื่อหลีกเลี่ยงปัญหา DLL)
    'qrcode',
    'qrcode.image.pil',
    
    # การสื่อสาร
    'zmq',
    'socket',
    'threading',
    'queue',
    'subprocess',
    
    # โมดูลพื้นฐาน
    'json',
    'datetime',
    'time',
    'os',
    'sys',
    'pathlib',
    'logging',
    'random',
    'math',
    
    # โมดูลของเรา
    'create_field',
    'create_field.field_manager',
    'create_field.simulation_manager',
    'create_field.field_config',
    'create_field.basic_objects',
    'create_field.field_parser',
    'create_field.pingpong_system',
]

# ไฟล์ที่ต้องยกเว้น
excludes = [
    'pyzbar',  # ยกเว้น pyzbar เพื่อหลีกเลี่ยงปัญหา DLL
    'matplotlib',  # ไม่จำเป็นสำหรับ GUI หลัก
    'scipy',  # ไม่จำเป็น
    'sklearn',  # ไม่จำเป็น
    'torch',  # ไม่จำเป็น
    'tensorflow',  # ไม่จำเป็น
]

a = Analysis(
    ['launcher.py'],
    pathex=[work_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# กรองเอาเฉพาะไฟล์ที่จำเป็น
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DroneOdysseyLauncher',
    debug=False,  # ปิด debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # ปิด UPX เพื่อความเสถียร
    console=False,  # GUI mode ไม่แสดง console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DroneOdysseyLauncher'
)
