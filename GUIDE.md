# คู่มือการใช้งาน PyArmor และ PyInstaller สำหรับ Drone Odyssey Field Creator

## ภาพรวม
ระบบนี้จะช่วยคุณ:
1. 🔒 ป้องกันโค้ด Python ด้วย PyArmor  
2. 📦 สร้างไฟล์ .exe ด้วย PyInstaller
3. 🔑 จัดการระบบ License
4. 📋 สร้างตัวติดตั้งแบบอัตโนมัติ

## วิธีการใช้งาน

### 1. การเตรียมโครงการ
```bash
# ติดตั้ง Dependencies ที่จำเป็น
pip install pyarmor pyinstaller cryptography pyyaml

# ตรวจสอบไฟล์ที่จำเป็น
- launcher.py ✓
- license_manager.py ✓  
- protected_launcher.py ✓
- field_creator_gui.py ✓
- field_creator_gui_advanced.py ✓
- create_field/ ✓
```

### 2. การ Build แบบอัตโนมัติ (แนะนำ)
```bash
# รันสคริปต์ build all-in-one
python build_all.py
```

สคริปต์นี้จะทำทุกอย่างให้อัตโนมัติ:
- ป้องกันโค้ดด้วย PyArmor
- สร้างไฟล์ .exe
- สร้างตัวติดตั้ง
- สร้างเครื่องมือจัดการ License

### 3. การ Build แบบทีละขั้นตอน

#### ขั้นตอนที่ 1: ป้องกันโค้ดด้วย PyArmor
```bash
python pyarmor_setup.py
```
ผลลัพธ์:
- โฟลเดอร์ `protected_build/` ที่มีไฟล์ป้องกันแล้ว
- ไฟล์ `license_generator.py` สำหรับสร้าง License Key

#### ขั้นตอนที่ 2: สร้างไฟล์ .exe
```bash
python pyinstaller_build.py
```
ผลลัพธ์:
- โฟลเดอร์ `dist/` ที่มีไฟล์ .exe และตัวติดตั้ง

### 4. การจัดการ License

#### สร้าง License Key (สำหรับผู้พัฒนา)
```bash
python license_generator.py
```

ตัวอย่างการใช้งาน:
```
Enter user name: John Doe
Enter machine ID (leave blank for any machine): 
Enter expiration days (default 365): 30
Select features (1-4, default 4): 4

Generated License Key: ABCDEF-123456-GHIJKL-789012
```

#### การให้ License แก่ผู้ใช้
1. รัน `license_generator.py` 
2. ใส่ข้อมูลผู้ใช้
3. ได้ License Key
4. ส่ง License Key ให้ผู้ใช้

### 5. โครงสร้างไฟล์หลังการ Build

```
📁 Project Root
├── 📁 dist/                          # ไฟล์สำหรับแจกจ่าย
│   ├── 📁 DroneOdysseyFieldCreator/   # โปรแกรมหลัก
│   │   ├── DroneOdysseyFieldCreator.exe
│   │   ├── uninstall.bat
│   │   └── [ไฟล์อื่นๆ]
│   ├── install.bat                    # ตัวติดตั้งอัตโนมัติ
│   └── README.txt                     # คู่มือติดตั้ง
├── 📁 protected_build/                # โค้ดที่ป้องกันแล้ว
├── license_generator.py               # เครื่องมือสร้าง License
└── BUILD_INFO.txt                     # ข้อมูลการ Build
```

## คำแนะนำการใช้งาน

### สำหรับผู้พัฒนา

1. **การ Build โครงการ:**
   ```bash
   python build_all.py
   ```

2. **การสร้าง License Key:**
   ```bash
   python license_generator.py
   ```

3. **การทดสอบ:**
   - ทดสอบไฟล์ .exe ใน `dist/DroneOdysseyFieldCreator/`
   - ทดสอบระบบ License ด้วย License Key ที่สร้าง

### สำหรับผู้ใช้

1. **การติดตั้ง:**
   - Double-click `install.bat`
   - ปฏิบัติตามคำแนะนำ

2. **การใช้งาน:**
   - เปิดโปรแกรมจาก Desktop หรือ Start Menu  
   - ใส่ License Key ที่ได้รับ
   - เลือก Interface ที่ต้องการ

3. **การถอนการติดตั้ง:**
   - รัน `uninstall.bat` ในโฟลเดอร์ติดตั้ง

## ฟีเจอร์ของระบบ

### 🔒 ระบบป้องกันโค้ด
- ป้องกันโค้ด Python ด้วย PyArmor
- เข้ารหัสไฟล์ .py เป็น .pyc ที่ป้องกัน
- ป้องกันการแก้ไขและการดู source code

### 🔑 ระบบ License
- License Key ผูกกับเครื่องใช้งาน
- ตั้งวันหมดอายุได้
- ควบคุมฟีเจอร์ที่ใช้งานได้
- เข้ารหัสข้อมูล License

### 📦 ระบบติดตั้ง
- สร้างไฟล์ .exe แบบ standalone
- ตัวติดตั้งอัตโนมัติ (install.bat)
- สร้าง shortcut บน Desktop และ Start Menu
- ตัวถอนการติดตั้ง (uninstall.bat)

### 🎨 GUI เดิมไม่เปลี่ยน
- Launcher GUI คงเดิม
- เพิ่มปุ่ม License Info
- ระบบตรวจสอบ License ทำงานเบื้องหลัง

## การแก้ปัญหา

### ปัญหาการ Build
```bash
# ถ้า PyArmor ไม่ทำงาน
pip install --upgrade pyarmor

# ถ้า PyInstaller ไม่ทำงาน  
pip install --upgrade pyinstaller

# ถ้าไฟล์ไม่ครบ
python -c "import os; print([f for f in os.listdir('.') if f.endswith('.py')])"
```

### ปัญหา License
```bash
# ลบไฟล์ License เก่า
del license.dat

# สร้าง License Key ใหม่
python license_generator.py
```

### ปัญหาการติดตั้ง
- ตรวจสอบสิทธิ์ Administrator
- ปิด Antivirus ชั่วคราว
- ตรวจสอบพื้นที่ฮาร์ดดิสก์

## ข้อควรระวัง

1. **License Key:** เก็บ License Key ให้ปลอดภัย
2. **Machine ID:** License ผูกกับเครื่องเฉพาะ
3. **Backup:** สำรองโครงการก่อน Build
4. **Testing:** ทดสอบบนเครื่องอื่นก่อนแจกจ่าย

## การปรับแต่ง

### เปลี่ยน License Duration
แก้ไขใน `license_generator.py`:
```python
expire_days = int(input("Enter expiration days (default 365): ") or "365")
```

### เปลี่ยน App Icon
วางไฟล์ `app_icon.ico` ในโฟลเดอร์หลัก

### เปลี่ยนชื่อ Executable
แก้ไขใน `pyinstaller_build.py`:
```python
name='DroneOdysseyFieldCreator',
```

## บทสรุป

ระบบนี้ให้ความสะดวกในการ:
- ป้องกันโค้ด Python อย่างมีประสิทธิภาพ
- สร้างโปรแกรมแจกจ่ายแบบ standalone  
- จัดการ License อย่างเป็นระบบ
- ติดตั้งใช้งานง่าย พร้อม GUI เดิม

ผลลัพธ์คือโปรแกรมที่พร้อมแจกจ่าย มีระบบป้องกัน และใช้งานง่าย!
