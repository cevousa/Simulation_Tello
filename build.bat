@echo off
echo 🚀 Drone Odyssey Field Creator - Build Script
echo =============================================
echo.

REM ตรวจสอบว่ามี PyInstaller หรือไม่
python -c "import PyInstaller" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ PyInstaller not found! Installing...
    pip install pyinstaller
)

REM ตรวจสอบว่ามี cryptography หรือไม่
python -c "import cryptography" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ cryptography not found! Installing...
    pip install cryptography
)

echo 📦 Step 1: Protecting Python code with PyArmor...
call protect.bat

if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to protect code!
    pause
    exit /b 1
)

echo.
echo 🔧 Step 2: Building executable with PyInstaller...

REM สร้างไฟล์ .exe จากโค้ดที่ป้องกันแล้ว
cd protected

pyinstaller --clean --onefile --windowed ^
    --name "DroneOdysseyFieldCreator" ^
    --add-data "mission_pad_templates;mission_pad_templates" ^
    --add-data "export_model;export_model" ^
    --add-data "Qrcode;Qrcode" ^
    --add-data "create_field;create_field" ^
    --add-data "requirements.txt;." ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.filedialog ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import zmq ^
    --hidden-import qrcode ^
    --hidden-import pyzbar ^
    --hidden-import cryptography ^
    --hidden-import cryptography.fernet ^
    --hidden-import create_field.field_manager ^
    --hidden-import create_field.basic_objects ^
    --hidden-import create_field.field_config ^
    --hidden-import create_field.field_parser ^
    --hidden-import create_field.pingpong_system ^
    --hidden-import create_field.simulation_manager ^
    --distpath ../dist ^
    --workpath ../build ^
    --specpath .. ^
    launcher.py

cd ..

if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to build executable!
    pause
    exit /b 1
)

echo.
echo 📝 Step 3: Creating installer script...

REM สร้างไฟล์ installer script
if not exist "installer" mkdir installer

echo ; Drone Odyssey Field Creator Installer > installer\setup.iss
echo ; Generated automatically >> installer\setup.iss
echo. >> installer\setup.iss
echo [Setup] >> installer\setup.iss
echo AppName=Drone Odyssey Field Creator >> installer\setup.iss
echo AppVersion=2.0 >> installer\setup.iss
echo AppPublisher=Your Company >> installer\setup.iss
echo DefaultDirName={autopf}\DroneOdysseyFieldCreator >> installer\setup.iss
echo DefaultGroupName=Drone Odyssey Field Creator >> installer\setup.iss
echo OutputDir=. >> installer\setup.iss
echo OutputBaseFilename=DroneOdysseyFieldCreator_Setup >> installer\setup.iss
echo Compression=lzma >> installer\setup.iss
echo SolidCompression=yes >> installer\setup.iss
echo WizardStyle=modern >> installer\setup.iss
echo. >> installer\setup.iss
echo [Files] >> installer\setup.iss
echo Source: "..\dist\DroneOdysseyFieldCreator.exe"; DestDir: "{app}"; Flags: ignoreversion >> installer\setup.iss
echo. >> installer\setup.iss
echo [Icons] >> installer\setup.iss
echo Name: "{group}\Drone Odyssey Field Creator"; Filename: "{app}\DroneOdysseyFieldCreator.exe" >> installer\setup.iss
echo Name: "{autodesktop}\Drone Odyssey Field Creator"; Filename: "{app}\DroneOdysseyFieldCreator.exe" >> installer\setup.iss

echo.
echo ✅ Build completed successfully!
echo.
echo 📁 Results:
echo   • Executable: dist\DroneOdysseyFieldCreator.exe
echo   • Installer Script: installer\setup.iss
echo.
echo 💡 Next Steps:
echo   1. Test the executable: dist\DroneOdysseyFieldCreator.exe
echo   2. Install Inno Setup to create installer from setup.iss
echo   3. Distribute your protected application!
echo.
pause
