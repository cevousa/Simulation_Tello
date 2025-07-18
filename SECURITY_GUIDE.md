# 🛡️ Drone Odyssey Field Creator - Security & Distribution Guide

## 📋 สารบัญ
1. [การป้องกันโค้ดด้วย PyArmor](#การป้องกันโค้ดด้วย-pyarmor)
2. [การสร้างไฟล์ .exe](#การสร้างไฟล์-exe)
3. [ระบบ License](#ระบบ-license)
4. [การสร้าง Installer](#การสร้าง-installer)
5. [การ Deploy และ Distribution](#การ-deploy-และ-distribution)

---

## 🔒 การป้องกันโค้ดด้วย PyArmor

### ✅ ข้อกำหนดเบื้องต้น
```bash
pip install pyarmor pyinstaller cryptography
```

### 🚀 วิธีการป้องกันโค้ด

#### วิธีที่ 1: ใช้ไฟล์ .bat (แนะนำ)
```bash
protect.bat
```

#### วิธีที่ 2: ใช้คำสั่งตรง
```bash
# ป้องกันไฟล์หลัก
pyarmor gen --output protected --platform windows.x86_64 --enable-jit --mix-str --private --restrict launcher.py drone_controller.py

# ป้องกันโมดูล create_field
pyarmor gen --output protected/create_field --platform windows.x86_64 --enable-jit --mix-str create_field/*.py
```

### 🛡️ คุณสมบัติการป้องกัน
- **--enable-jit**: JIT Protection (ป้องกัน reverse engineering)
- **--mix-str**: String Encryption (เข้ารหัสข้อความ)
- **--assert-call**: Call Protection (ป้องกันการเรียกใช้ผิดปกติ)
- **--assert-import**: Import Protection (ป้องกัน import ผิดปกติ)
- **--private**: Private Mode (ป้องกันการเข้าถึงโค้ด)
- **--restrict**: Restricted Mode (จำกัดการใช้งาน)

---

## 📦 การสร้างไฟล์ .exe

### 🛠️ วิธีสร้าง Executable

#### วิธีที่ 1: ใช้ Build Script (แนะนำ)
```bash
build.bat
```

#### วิธีที่ 2: ใช้ PyInstaller ตรง
```bash
cd protected
pyinstaller --onefile --windowed --name "DroneOdysseyFieldCreator" launcher.py
```

### 📁 โครงสร้างหลังจาก Build
```
📦 โปรเจค
├── 🔒 protected/          # ไฟล์ที่ป้องกันแล้ว
├── 📦 dist/              # ไฟล์ .exe
├── 🏗️ build/             # ไฟล์ชั่วคราว
└── 📄 ไฟล์ต้นฉบับ
```

---

## 🔐 ระบบ License

### 🎯 คุณสมบัติระบบ License
- **Machine Binding**: ผูกกับเครื่องเฉพาะ
- **Expiration Date**: วันหมดอายุ
- **Feature Control**: ควบคุมฟีเจอร์ที่ใช้ได้
- **Encryption**: เข้ารหัสข้อมูล License

### 👨‍💼 สำหรับ Admin: การสร้าง License

#### 1. เปิดเครื่องมือสร้าง License
```bash
python license_generator.py
```

#### 2. กรอกข้อมูลผู้ใช้
- ชื่อ-นามสกุล
- อีเมล
- บริษัท (ถ้ามี)

#### 3. ตั้งค่า License
- ประเภท: TRIAL, STANDARD, PROFESSIONAL, ENTERPRISE
- ระยะเวลา: จำนวนวัน
- ฟีเจอร์ที่อนุญาต
- Machine ID (ถ้าต้องการผูกกับเครื่องเฉพาะ)

#### 4. สร้างและส่งมอบ License
- กด "Generate License"
- บันทึกเป็นไฟล์หรือคัดลอกข้อมูล
- ส่งให้ลูกค้า

### 👤 สำหรับ User: การใช้ License

#### 1. เปิดโปรแกรม
- โปรแกรมจะตรวจสอบ License อัตโนมัติ
- หากไม่มี License จะเปิด Dialog สำหรับใส่ข้อมูล

#### 2. Activate License
- กรอกชื่อและอีเมลตาม License ที่ได้รับ
- กด "Activate"

#### 3. ตรวจสอบสถานะ License
- กด "License Info" ในหน้าหลัก
- ดูข้อมูล License และวันหมดอายุ

### 🔧 ประเภท License

#### TRIAL (ทดลองใช้)
- ระยะเวลา: 30 วัน
- ฟีเจอร์: พื้นฐาน
- ไม่ใช้เชิงพาณิชย์

#### STANDARD (มาตรฐาน)  
- ระยะเวลา: 1 ปี
- ฟีเจอร์: ครบทุกอย่าง
- ใช้ส่วนตัวได้

#### PROFESSIONAL (มืออาชีพ)
- ระยะเวลา: 1 ปี
- ฟีเจอร์: ครบ + เครื่องมือขั้นสูง
- ใช้เชิงพาณิชย์ได้

#### ENTERPRISE (องค์กร)
- ระยะเวลา: ไม่จำกัด
- ฟีเจอร์: ทั้งหมด
- ใช้องค์กรได้

---

## 💿 การสร้าง Installer

### 📥 ติดตั้ง Inno Setup
1. ดาวน์โหลดจาก: https://jrsoftware.org/isinfo.php
2. ติดตั้งตามปกติ

### 🛠️ สร้าง Installer
1. เปิด Inno Setup Compiler
2. เปิดไฟล์ `installer/setup.iss`
3. กด Compile (F9)
4. รอจนเสร็จ

### 📋 ไฟล์ที่ได้
- `installer/DroneOdysseyFieldCreator_Setup.exe`

---

## 🚀 การ Deploy และ Distribution

### 📦 เตรียมไฟล์สำหรับ Distribution

#### ไฟล์ที่ต้องมี:
1. **DroneOdysseyFieldCreator.exe** - ไฟล์หลัก
2. **DroneOdysseyFieldCreator_Setup.exe** - Installer
3. **User Manual** - คู่มือการใช้งาน
4. **License Information** - ข้อมูล License

#### โครงสร้างโฟลเดอร์:
```
📦 Distribution Package
├── 📁 Standalone/
│   └── DroneOdysseyFieldCreator.exe
├── 📁 Installer/
│   └── DroneOdysseyFieldCreator_Setup.exe
├── 📁 Documentation/
│   ├── User_Manual.pdf
│   ├── Installation_Guide.pdf
│   └── License_Terms.pdf
└── 📄 README.txt
```

### 🔐 การจัดการ License

#### สำหรับ Developer:
```python
# สร้าง License สำหรับลูกค้า
python license_generator.py

# ตรวจสอบ License
from license_manager import LicenseManager
lm = LicenseManager()
valid, info = lm.verify_license()
```

#### สำหรับ Customer Support:
1. รับข้อมูลลูกค้า (ชื่อ, อีเมล, Machine ID)
2. ใช้ License Generator สร้าง License
3. ส่ง License ให้ลูกค้า
4. ช่วยลูกค้า Activate

### 📊 การ Monitoring และ Analytics

#### ติดตาม License Usage:
```python
# เพิ่มใน license_manager.py
def log_license_usage():
    """บันทึกการใช้งาน License"""
    # บันทึกลง log file หรือส่งไป server
    pass
```

### 🔄 การ Update โปรแกรม

#### Auto Update (อนาคต):
1. ตรวจสอบเวอร์ชันจาก server
2. ดาวน์โหลด update ถ้าจำเป็น
3. แจ้งผู้ใช้และ restart

---

## 🎯 Quick Start Guide

### สำหรับ Developer:
```bash
# 1. ป้องกันโค้ด
protect.bat

# 2. สร้าง .exe
build.bat

# 3. สร้าง License (ถ้าต้องการ)
python license_generator.py
```

### สำหรับ End User:
1. ดาวน์โหลดและติดตั้งโปรแกรม
2. เปิดโปรแกรม
3. ใส่ข้อมูล License (ถ้าจำเป็น)
4. เริ่มใช้งาน

---

## 🛠️ การแก้ไขปัญหา

### ปัญหา PyArmor:
```bash
# รีเซ็ต PyArmor
pyarmor gen --clean

# ตรวจสอบเวอร์ชัน
pyarmor --version
```

### ปัญหา PyInstaller:
```bash
# ลบ cache
pip cache purge
pip install --upgrade pyinstaller

# สร้าง virtual environment ใหม่
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### ปัญหา License:
```python
# ตรวจสอบ License
from license_manager import LicenseManager
lm = LicenseManager()
print(f"Machine ID: {lm.machine_id}")
valid, info = lm.verify_license()
print(f"Valid: {valid}, Info: {info}")
```

---

## 🎉 เสร็จสิ้น!

ตอนนี้คุณมีโปรแกรมที่:
- 🔒 ป้องกันโค้ดด้วย PyArmor
- 📦 สร้างเป็นไฟล์ .exe
- 🔐 มีระบบ License ครบครัน
- 💿 สร้าง Installer ได้
- 🚀 พร้อม Deploy และ Distribution

Good luck! 🎯
