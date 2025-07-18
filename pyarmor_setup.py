#!/usr/bin/env python3
"""
PyArmor Protection Script
สคริปต์สำหรับป้องกันโค้ดด้วย PyArmor
"""

import os
import shutil
import subprocess
import sys

def setup_pyarmor():
    """ตั้งค่า PyArmor"""
    print("🔒 Setting up PyArmor protection...")
    
    # สร้างโฟลเดอร์สำหรับไฟล์ที่ป้องกันแล้ว
    protected_dir = "protected_build"
    if os.path.exists(protected_dir):
        shutil.rmtree(protected_dir)
    os.makedirs(protected_dir)
    
    return protected_dir

def protect_files(protected_dir):
    """ป้องกันไฟล์ด้วย PyArmor"""
    print("🛡️ Protecting Python files...")
    
    # รายการไฟล์ที่ต้องการป้องกัน
    files_to_protect = [
        "protected_launcher.py",
        "license_manager.py", 
        "field_creator_gui.py",
        "field_creator_gui_advanced.py",
        "drone_controller.py",
        "improved_mission_pad_detector.py",
        "mission_pad_detector.py",
        "config.py",
        "zmqRemoteApi.py"
    ]
    
    # ป้องกันไฟล์แต่ละไฟล์
    for file in files_to_protect:
        if os.path.exists(file):
            print(f"  Protecting {file}...")
            try:
                # ใช้ PyArmor ป้องกันไฟล์
                cmd = [
                    sys.executable, "-m", "pyarmor", "gen",
                    "--output", protected_dir,
                    "--recursive",
                    "--enable-suffix",
                    file
                ]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"  ✅ {file} protected successfully")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Failed to protect {file}: {e}")
    
    # ป้องกันโฟลเดอร์ create_field
    if os.path.exists("create_field"):
        print("  Protecting create_field module...")
        try:
            cmd = [
                sys.executable, "-m", "pyarmor", "gen",
                "--output", protected_dir,
                "--recursive",
                "--enable-suffix",
                "create_field"
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("  ✅ create_field module protected successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to protect create_field: {e}")

def copy_resources(protected_dir):
    """คัดลอกไฟล์ทรัพยากรที่ไม่ต้องป้องกัน"""
    print("📁 Copying resource files...")
    
    resources = [
        "requirements.txt",
        "mission_pad_templates",
        "export_model", 
        "Qrcode",
        "captured_images"
    ]
    
    for resource in resources:
        if os.path.exists(resource):
            dest = os.path.join(protected_dir, resource)
            if os.path.isdir(resource):
                shutil.copytree(resource, dest)
            else:
                shutil.copy2(resource, dest)
            print(f"  ✅ Copied {resource}")

def create_main_launcher(protected_dir):
    """สร้าง Main Launcher ที่ไม่ป้องกัน"""
    print("🚀 Creating main launcher...")
    
    launcher_content = '''#!/usr/bin/env python3
"""
Main Launcher for Protected Drone Odyssey Field Creator
จุดเริ่มต้นสำหรับโปรแกรมที่ป้องกันแล้ว
"""

import sys
import os

# เพิ่ม path ของ protected files
sys.path.insert(0, os.path.dirname(__file__))

try:
    # นำเข้า protected launcher
    from protected_launcher import ProtectedLauncher
    
    def main():
        """ฟังก์ชันหลัก"""
        launcher = ProtectedLauncher()
        launcher.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Failed to import protected modules: {e}")
    print("Please ensure all protected files are in place.")
    input("Press Enter to exit...")
except Exception as e:
    print(f"❌ Application error: {e}")
    input("Press Enter to exit...")
'''
    
    main_launcher_path = os.path.join(protected_dir, "main.py")
    with open(main_launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print(f"  ✅ Main launcher created: {main_launcher_path}")

def create_license_generator():
    """สร้างเครื่องมือสำหรับสร้าง License Key"""
    print("🔑 Creating license generator...")
    
    generator_content = '''#!/usr/bin/env python3
"""
License Key Generator for Drone Odyssey Field Creator
เครื่องมือสร้าง License Key สำหรับผู้พัฒนา
"""

import sys
import os
import json
import hashlib
import datetime
from cryptography.fernet import Fernet

class LicenseGenerator:
    def __init__(self):
        # ต้องใช้ secret key เดียวกับใน license_manager.py
        self.cipher = Fernet(Fernet.generate_key())
        
    def generate_license_key(self, user_name, machine_id, expire_days=365, features=None):
        """สร้าง License Key"""
        if features is None:
            features = ["basic_gui", "advanced_gui", "console_gui"]
            
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expire_days)
        
        license_data = {
            "user_name": user_name,
            "machine_id": machine_id,
            "created_date": datetime.datetime.now().isoformat(),
            "expire_date": expire_date.isoformat(),
            "features": features,
            "version": "2.0"
        }
        
        # เข้ารหัส license data
        license_json = json.dumps(license_data)
        encrypted_license = self.cipher.encrypt(license_json.encode())
        
        # สร้าง license key ที่อ่านได้
        license_key = hashlib.sha256(encrypted_license).hexdigest()[:24].upper()
        formatted_key = f"{license_key[:6]}-{license_key[6:12]}-{license_key[12:18]}-{license_key[18:24]}"
        
        return formatted_key, license_data

def main():
    """ฟังก์ชันหลักสำหรับสร้าง License"""
    print("🔑 Drone Odyssey License Key Generator")
    print("=" * 50)
    
    generator = LicenseGenerator()
    
    # รับข้อมูลจากผู้ใช้
    user_name = input("Enter user name: ").strip()
    if not user_name:
        print("❌ User name is required!")
        return
    
    machine_id = input("Enter machine ID (leave blank for any machine): ").strip()
    if not machine_id:
        machine_id = "ANY_MACHINE"
    
    try:
        expire_days = int(input("Enter expiration days (default 365): ") or "365")
    except ValueError:
        expire_days = 365
    
    # เลือก Features
    print("\\nAvailable features:")
    print("1. Basic GUI")
    print("2. Advanced GUI")
    print("3. Console Interface")
    print("4. All Features (default)")
    
    feature_choice = input("Select features (1-4, default 4): ").strip()
    
    if feature_choice == "1":
        features = ["basic_gui"]
    elif feature_choice == "2":
        features = ["advanced_gui"]
    elif feature_choice == "3":
        features = ["console_gui"]
    else:
        features = ["basic_gui", "advanced_gui", "console_gui"]
    
    # สร้าง License Key
    license_key, license_data = generator.generate_license_key(
        user_name, machine_id, expire_days, features
    )
    
    # แสดงผลลัพธ์
    print("\\n" + "=" * 50)
    print("✅ License Key Generated Successfully!")
    print("=" * 50)
    print(f"License Key: {license_key}")
    print(f"User Name: {user_name}")
    print(f"Machine ID: {machine_id}")
    print(f"Expires: {license_data['expire_date'][:10]}")
    print(f"Features: {', '.join(features)}")
    print("=" * 50)
    
    # บันทึกลงไฟล์
    save_file = input("\\nSave to file? (y/n): ").lower().startswith('y')
    if save_file:
        filename = f"license_{user_name.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Drone Odyssey Field Creator - License Key\\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\\n\\n")
            f.write(f"License Key: {license_key}\\n")
            f.write(f"User Name: {user_name}\\n")
            f.write(f"Machine ID: {machine_id}\\n")
            f.write(f"Expires: {license_data['expire_date'][:10]}\\n")
            f.write(f"Features: {', '.join(features)}\\n")
        print(f"✅ License saved to: {filename}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        input("\\nPress Enter to exit...")
'''
    
    with open("license_generator.py", 'w', encoding='utf-8') as f:
        f.write(generator_content)
    
    print("  ✅ License generator created: license_generator.py")

def main():
    """ฟังก์ชันหลัก"""
    print("🔒 PyArmor Protection Setup")
    print("=" * 40)
    
    try:
        # 1. ตั้งค่า PyArmor
        protected_dir = setup_pyarmor()
        
        # 2. ป้องกันไฟล์
        protect_files(protected_dir)
        
        # 3. คัดลอกทรัพยากร
        copy_resources(protected_dir)
        
        # 4. สร้าง Main Launcher
        create_main_launcher(protected_dir)
        
        # 5. สร้าง License Generator
        create_license_generator()
        
        print("\\n✅ PyArmor protection completed successfully!")
        print(f"📁 Protected files are in: {protected_dir}")
        print("🔑 License generator created: license_generator.py")
        print("🚀 Main launcher: {}/main.py".format(protected_dir))
        
    except Exception as e:
        print(f"❌ Protection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎉 Ready for PyInstaller build!")
    else:
        print("\\n❌ Protection failed. Please check errors above.")
    
    input("Press Enter to continue...")
