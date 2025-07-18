#!/usr/bin/env python3
"""
License Generator Tool
เครื่องมือสร้าง License สำหรับ Admin
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import datetime
from license_manager import LicenseManager
import os

class LicenseGeneratorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔐 License Generator - Admin Tool")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        self.create_widgets()
        
    def create_widgets(self):
        """สร้าง UI elements"""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#1e3a8a", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="🔐 License Generator", 
                              font=("Arial", 18, "bold"),
                              bg="#1e3a8a", 
                              fg="white")
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(header_frame, 
                                 text="Admin Tool for Creating Software Licenses", 
                                 font=("Arial", 10),
                                 bg="#1e3a8a", 
                                 fg="#bfdbfe")
        subtitle_label.pack()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f8fafc", padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # User Information Section
        user_section = tk.LabelFrame(main_frame, text="👤 User Information", 
                                   font=("Arial", 12, "bold"),
                                   bg="#f8fafc", padx=15, pady=10)
        user_section.pack(fill="x", pady=(0, 15))
        
        # Name
        tk.Label(user_section, text="Full Name:", bg="#f8fafc").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(user_section, width=40, font=("Arial", 10))
        self.name_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # Email
        tk.Label(user_section, text="Email:", bg="#f8fafc").grid(row=1, column=0, sticky="w", pady=5)
        self.email_entry = tk.Entry(user_section, width=40, font=("Arial", 10))
        self.email_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # Company
        tk.Label(user_section, text="Company:", bg="#f8fafc").grid(row=2, column=0, sticky="w", pady=5)
        self.company_entry = tk.Entry(user_section, width=40, font=("Arial", 10))
        self.company_entry.grid(row=2, column=1, padx=(10, 0), pady=5)
        
        # License Configuration Section
        license_section = tk.LabelFrame(main_frame, text="⚙️ License Configuration", 
                                      font=("Arial", 12, "bold"),
                                      bg="#f8fafc", padx=15, pady=10)
        license_section.pack(fill="x", pady=(0, 15))
        
        # License Type
        tk.Label(license_section, text="License Type:", bg="#f8fafc").grid(row=0, column=0, sticky="w", pady=5)
        self.license_type = ttk.Combobox(license_section, width=37, state="readonly")
        self.license_type['values'] = ('TRIAL', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE')
        self.license_type.set('STANDARD')
        self.license_type.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # Duration
        tk.Label(license_section, text="Duration (days):", bg="#f8fafc").grid(row=1, column=0, sticky="w", pady=5)
        self.duration_var = tk.IntVar(value=365)
        duration_frame = tk.Frame(license_section, bg="#f8fafc")
        duration_frame.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="w")
        
        self.duration_entry = tk.Entry(duration_frame, width=10, textvariable=self.duration_var)
        self.duration_entry.pack(side="left")
        
        # Quick duration buttons
        tk.Button(duration_frame, text="30d", command=lambda: self.duration_var.set(30), 
                 width=4, bg="#e5e7eb").pack(side="left", padx=2)
        tk.Button(duration_frame, text="90d", command=lambda: self.duration_var.set(90), 
                 width=4, bg="#e5e7eb").pack(side="left", padx=2)
        tk.Button(duration_frame, text="1y", command=lambda: self.duration_var.set(365), 
                 width=4, bg="#e5e7eb").pack(side="left", padx=2)
        tk.Button(duration_frame, text="∞", command=lambda: self.duration_var.set(36500), 
                 width=4, bg="#fbbf24").pack(side="left", padx=2)
        
        # Features Section
        features_section = tk.LabelFrame(main_frame, text="🎯 Features & Permissions", 
                                       font=("Arial", 12, "bold"),
                                       bg="#f8fafc", padx=15, pady=10)
        features_section.pack(fill="x", pady=(0, 15))
        
        self.features = {}
        feature_list = [
            ("basic_creator", "Basic Field Creator"),
            ("advanced_creator", "Advanced Field Creator"),
            ("coppelia_integration", "CoppeliaSim Integration"),
            ("export_function", "Export Functions"),
            ("unlimited_fields", "Unlimited Fields"),
            ("commercial_use", "Commercial Use")
        ]
        
        for i, (key, label) in enumerate(feature_list):
            self.features[key] = tk.BooleanVar(value=True)
            tk.Checkbutton(features_section, text=label, variable=self.features[key], 
                          bg="#f8fafc", font=("Arial", 10)).grid(row=i//2, column=i%2, 
                                                                 sticky="w", padx=10, pady=2)
        
        # Machine ID Section
        machine_section = tk.LabelFrame(main_frame, text="🖥️ Machine Binding (Optional)", 
                                      font=("Arial", 12, "bold"),
                                      bg="#f8fafc", padx=15, pady=10)
        machine_section.pack(fill="x", pady=(0, 15))
        
        tk.Label(machine_section, text="Machine ID:", bg="#f8fafc").grid(row=0, column=0, sticky="w", pady=5)
        self.machine_id_entry = tk.Entry(machine_section, width=40, font=("Arial", 9))
        self.machine_id_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        tk.Button(machine_section, text="Auto Generate", 
                 command=self.generate_machine_id,
                 bg="#3b82f6", fg="white").grid(row=0, column=2, padx=(5, 0))
        
        # Buttons Section
        button_frame = tk.Frame(main_frame, bg="#f8fafc")
        button_frame.pack(fill="x", pady=20)
        
        tk.Button(button_frame, text="🔒 Generate License", 
                 command=self.generate_license,
                 bg="#10b981", fg="white", 
                 font=("Arial", 12, "bold"),
                 width=20, height=2).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="💾 Save to File", 
                 command=self.save_license_file,
                 bg="#6366f1", fg="white", 
                 font=("Arial", 12, "bold"),
                 width=20, height=2).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="📋 Copy License Data", 
                 command=self.copy_license_data,
                 bg="#f59e0b", fg="white", 
                 font=("Arial", 12, "bold"),
                 width=20, height=2).pack(side="left", padx=5)
        
        # Output Section
        output_section = tk.LabelFrame(main_frame, text="📄 Generated License", 
                                     font=("Arial", 12, "bold"),
                                     bg="#f8fafc", padx=15, pady=10)
        output_section.pack(fill="both", expand=True)
        
        self.output_text = tk.Text(output_section, height=8, font=("Consolas", 9))
        scrollbar = tk.Scrollbar(output_section, orient="vertical", command=self.output_text.yview)
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        self.output_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.generated_license_data = None
        
    def generate_machine_id(self):
        """สร้าง Machine ID แบบสุ่ม"""
        import uuid
        machine_id = str(uuid.uuid4())[:16]
        self.machine_id_entry.delete(0, tk.END)
        self.machine_id_entry.insert(0, machine_id)
        
    def generate_license(self):
        """สร้าง License"""
        # ตรวจสอบข้อมูล
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        
        if not name or not email:
            messagebox.showerror("Error", "Please fill in Name and Email")
            return
        
        # สร้างข้อมูล License
        license_data = {
            "user_name": name,
            "email": email,
            "company": self.company_entry.get().strip(),
            "license_type": self.license_type.get(),
            "machine_id": self.machine_id_entry.get().strip() or None,
            "created_date": datetime.datetime.now().isoformat(),
            "expiry_date": (datetime.datetime.now() + 
                           datetime.timedelta(days=self.duration_var.get())).isoformat(),
            "features": {key: var.get() for key, var in self.features.items()},
            "generator_info": {
                "version": "2.0",
                "generated_by": "License Generator Tool"
            }
        }
        
        self.generated_license_data = license_data
        
        # แสดงผลใน Text widget
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, json.dumps(license_data, indent=2, ensure_ascii=False))
        
        messagebox.showinfo("Success", "License generated successfully!")
        
    def save_license_file(self):
        """บันทึก License เป็นไฟล์"""
        if not self.generated_license_data:
            messagebox.showerror("Error", "Please generate a license first")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save License File"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.generated_license_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"License saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    def copy_license_data(self):
        """คัดลอกข้อมูล License ไปยัง clipboard"""
        if not self.generated_license_data:
            messagebox.showerror("Error", "Please generate a license first")
            return
        
        license_text = json.dumps(self.generated_license_data, indent=2, ensure_ascii=False)
        self.root.clipboard_clear()
        self.root.clipboard_append(license_text)
        messagebox.showinfo("Success", "License data copied to clipboard!")
        
    def run(self):
        """เริ่มต้นโปรแกรม"""
        self.root.mainloop()

if __name__ == "__main__":
    app = LicenseGeneratorGUI()
    app.run()
