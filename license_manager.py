#!/usr/bin/env python3
"""
License Manager for Drone Odyssey Field Creator
ระบบจัดการลิขสิทธิ์และการตรวจสอบ License
"""

import os
import json
import hashlib
import datetime
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox, simpledialog
import uuid

class LicenseManager:
    def __init__(self):
        self.license_file = "license.dat"
        self.machine_id = self._get_machine_id()
        self.secret_key = b'your_secret_key_here_32_bytes_long'  # เปลี่ยนเป็น key จริง
        self.cipher = Fernet(Fernet.generate_key())
        
    def _get_machine_id(self):
        """สร้าง Machine ID ที่ไม่ซ้ำกัน"""
        try:
            # ใช้ MAC address และ OS info
            import platform
            machine_info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
            return hashlib.sha256(machine_info.encode()).hexdigest()[:16]
        except:
            return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]
    
    def generate_license_key(self, user_name, expire_days=365, features=None):
        """สร้าง License Key"""
        if features is None:
            features = ["basic_gui", "advanced_gui", "console_gui"]
            
        expire_date = datetime.datetime.now() + datetime.timedelta(days=expire_days)
        
        license_data = {
            "user_name": user_name,
            "machine_id": self.machine_id,
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
    
    def validate_license(self):
        """ตรวจสอบ License"""
        if not os.path.exists(self.license_file):
            return False, "No license file found"
        
        try:
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            license_data = json.loads(decrypted_data.decode())
            
            # ตรวจสอบ Machine ID
            if license_data.get("machine_id") != self.machine_id:
                return False, "License not valid for this machine"
            
            # ตรวจสอบวันหมดอายุ
            expire_date = datetime.datetime.fromisoformat(license_data.get("expire_date"))
            if datetime.datetime.now() > expire_date:
                return False, "License has expired"
            
            return True, license_data
            
        except Exception as e:
            return False, f"License validation error: {e}"
    
    def save_license(self, license_key, user_name):
        """บันทึก License"""
        try:
            # สร้าง license data จาก key
            license_data = {
                "user_name": user_name,
                "machine_id": self.machine_id,
                "license_key": license_key,
                "activated_date": datetime.datetime.now().isoformat(),
                "features": ["basic_gui", "advanced_gui", "console_gui"],
                "version": "2.0"
            }
            
            # เข้ารหัสและบันทึก
            license_json = json.dumps(license_data)
            encrypted_license = self.cipher.encrypt(license_json.encode())
            
            with open(self.license_file, 'wb') as f:
                f.write(encrypted_license)
            
            return True, "License activated successfully"
            
        except Exception as e:
            return False, f"License save error: {e}"
    
    def show_license_dialog(self):
        """แสดง Dialog สำหรับใส่ License Key"""
        root = tk.Tk()
        root.withdraw()  # ซ่อนหน้าต่างหลัก
        
        # ตรวจสอบ license ปัจจุบัน
        is_valid, license_info = self.validate_license()
        
        if is_valid:
            days_left = (datetime.datetime.fromisoformat(license_info["expire_date"]) - datetime.datetime.now()).days
            messagebox.showinfo(
                "License Status", 
                f"License is valid!\n\n"
                f"User: {license_info.get('user_name', 'Unknown')}\n"
                f"Days remaining: {days_left}\n"
                f"Features: {', '.join(license_info.get('features', []))}"
            )
            root.destroy()
            return True
        
        # ถ้าไม่มี license หรือไม่ valid ให้ใส่ใหม่
        messagebox.showwarning("License Required", 
                              f"License validation failed: {license_info}\n\n"
                              "Please enter your license key to continue.")
        
        # Dialog ใส่ License Key
        license_key = simpledialog.askstring(
            "License Activation",
            "Enter your license key (Format: XXXXXX-XXXXXX-XXXXXX-XXXXXX):",
            show='*'
        )
        
        if not license_key:
            root.destroy()
            return False
        
        user_name = simpledialog.askstring(
            "User Information",
            "Enter your name:",
        )
        
        if not user_name:
            user_name = "Licensed User"
        
        # บันทึก license
        success, message = self.save_license(license_key, user_name)
        
        if success:
            messagebox.showinfo("Success", message)
            root.destroy()
            return True
        else:
            messagebox.showerror("Error", message)
            root.destroy()
            return False
    
    def get_machine_info(self):
        """แสดงข้อมูล Machine สำหรับสร้าง License"""
        return {
            "machine_id": self.machine_id,
            "platform": os.name,
            "architecture": os.uname() if hasattr(os, 'uname') else 'Windows'
        }

# ฟังก์ชันสำหรับสร้าง License Key (สำหรับผู้พัฒนา)
def create_license_key():
    """สร้าง License Key ใหม่ (สำหรับผู้พัฒนา)"""
    lm = LicenseManager()
    
    print(f"Machine ID: {lm.machine_id}")
    user_name = input("Enter user name: ")
    expire_days = int(input("Enter expiration days (default 365): ") or "365")
    
    license_key, license_data = lm.generate_license_key(user_name, expire_days)
    
    print(f"\nGenerated License Key: {license_key}")
    print(f"User: {user_name}")
    print(f"Expires: {license_data['expire_date']}")
    print(f"Machine ID: {license_data['machine_id']}")
    
    return license_key

if __name__ == "__main__":
    # สำหรับทดสอบ
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_license_key()
    else:
        lm = LicenseManager()
        print("Machine Info:", lm.get_machine_info())
        result = lm.show_license_dialog()
        print(f"License validation result: {result}")
