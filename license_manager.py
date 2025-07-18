#!/usr/bin/env python3
"""
License Management System
ระบบจัดการ License สำหรับ Drone Odyssey Field Creator
"""

import os
import json
import hashlib
import datetime
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox
import uuid

class LicenseManager:
    def __init__(self):
        self.license_file = "license.dat"
        self.key_file = "app.key"
        self.machine_id = self.get_machine_id()
        
    def get_machine_id(self):
        """สร้าง Machine ID เฉพาะสำหรับเครื่องนี้"""
        machine_info = f"{os.environ.get('COMPUTERNAME', 'unknown')}-{os.environ.get('USERNAME', 'user')}"
        return hashlib.sha256(machine_info.encode()).hexdigest()[:16]
    
    def generate_key(self):
        """สร้าง encryption key"""
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        return key
    
    def load_key(self):
        """โหลด encryption key"""
        try:
            with open(self.key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return self.generate_key()
    
    def create_license(self, user_name, email, days_valid=365, license_type="STANDARD"):
        """สร้าง License ใหม่"""
        license_data = {
            "user_name": user_name,
            "email": email,
            "machine_id": self.machine_id,
            "license_type": license_type,
            "created_date": datetime.datetime.now().isoformat(),
            "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=days_valid)).isoformat(),
            "features": {
                "basic_creator": True,
                "advanced_creator": True,
                "coppelia_integration": True,
                "export_function": True
            }
        }
        
        # เข้ารหัส license
        key = self.load_key()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(json.dumps(license_data).encode())
        
        with open(self.license_file, 'wb') as f:
            f.write(encrypted_data)
        
        return license_data
    
    def verify_license(self):
        """ตรวจสอบ License"""
        try:
            if not os.path.exists(self.license_file):
                return False, "License file not found"
            
            key = self.load_key()
            fernet = Fernet(key)
            
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            license_data = json.loads(decrypted_data.decode())
            
            # ตรวจสอบ Machine ID
            if license_data.get("machine_id") != self.machine_id:
                return False, "License not valid for this machine"
            
            # ตรวจสอบวันหมดอายุ
            expiry_date = datetime.datetime.fromisoformat(license_data.get("expiry_date"))
            if datetime.datetime.now() > expiry_date:
                return False, "License expired"
            
            return True, license_data
            
        except Exception as e:
            return False, f"License verification failed: {str(e)}"
    
    def get_license_info(self):
        """ดึงข้อมูล License"""
        valid, data = self.verify_license()
        if valid:
            expiry_date = datetime.datetime.fromisoformat(data.get("expiry_date"))
            days_left = (expiry_date - datetime.datetime.now()).days
            return {
                "valid": True,
                "user_name": data.get("user_name"),
                "email": data.get("email"),
                "license_type": data.get("license_type"),
                "days_left": days_left,
                "features": data.get("features", {})
            }
        else:
            return {"valid": False, "error": data}

def show_license_dialog():
    """แสดง Dialog สำหรับใส่ License"""
    def activate_license():
        name = name_entry.get().strip()
        email = email_entry.get().strip()
        
        if not name or not email:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        license_manager = LicenseManager()
        license_data = license_manager.create_license(name, email)
        
        messagebox.showinfo("Success", 
                          f"License activated successfully!\n"
                          f"User: {license_data['user_name']}\n"
                          f"Valid until: {license_data['expiry_date'][:10]}")
        
        root.destroy()
    
    root = tk.Tk()
    root.title("License Activation")
    root.geometry("400x200")
    root.resizable(False, False)
    
    # Center the window
    root.eval('tk::PlaceWindow . center')
    
    tk.Label(root, text="Drone Odyssey Field Creator", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(root, text="License Activation", font=("Arial", 10)).pack()
    
    frame = tk.Frame(root)
    frame.pack(pady=20)
    
    tk.Label(frame, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    name_entry = tk.Entry(frame, width=30)
    name_entry.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(frame, text="Email:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    email_entry = tk.Entry(frame, width=30)
    email_entry.grid(row=1, column=1, padx=5, pady=5)
    
    tk.Button(root, text="Activate", command=activate_license, bg="#4CAF50", fg="white", width=15).pack(pady=10)
    
    root.mainloop()

def check_license_on_startup():
    """ตรวจสอบ License เมื่อเริ่มโปรแกรม"""
    license_manager = LicenseManager()
    valid, result = license_manager.verify_license()
    
    if not valid:
        response = messagebox.askyesno("License Required", 
                                     f"License verification failed: {result}\n\n"
                                     "Would you like to activate a license now?")
        if response:
            show_license_dialog()
            # ตรวจสอบอีกครั้งหลัง activation
            valid, result = license_manager.verify_license()
            if not valid:
                messagebox.showerror("Error", "License activation failed. The application will exit.")
                return False
        else:
            messagebox.showinfo("Demo Mode", "Running in demo mode with limited features.")
            return "demo"
    
    return True

if __name__ == "__main__":
    # ทดสอบระบบ License
    license_manager = LicenseManager()
    print(f"Machine ID: {license_manager.machine_id}")
    
    # สร้าง license ทดสอบ
    license_data = license_manager.create_license("Test User", "test@example.com")
    print("License created:", license_data)
    
    # ตรวจสอบ license
    valid, result = license_manager.verify_license()
    print("License valid:", valid)
    print("Result:", result)
