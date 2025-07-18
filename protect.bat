@echo off
echo 🔒 PyArmor Code Protection Script
echo =================================
echo.

REM สร้างโฟลเดอร์สำหรับไฟล์ที่ป้องกันแล้ว
if not exist "protected" mkdir protected
if not exist "protected\create_field" mkdir protected\create_field

echo กำลังป้องกันไฟล์ Python หลัก...

REM ป้องกันไฟล์หลักด้วย PyArmor
pyarmor gen --output protected ^
    --platform windows.x86_64 ^
    --enable-jit ^
    --mix-str ^
    --assert-call ^
    --assert-import ^
    --private ^
    --restrict ^
    launcher.py ^
    drone_controller.py ^
    field_creator_gui.py ^
    field_creator_gui_advanced.py ^
    mission_pad_detector.py ^
    improved_mission_pad_detector.py ^
    zmqRemoteApi.py ^
    config.py ^
    license_manager.py

if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to protect main files!
    pause
    exit /b 1
)

echo กำลังป้องกันโฟลเดอร์ create_field...

REM ป้องกันไฟล์ในโฟลเดอร์ create_field
pyarmor gen --output protected/create_field ^
    --platform windows.x86_64 ^
    --enable-jit ^
    --mix-str ^
    --private ^
    --restrict ^
    create_field/__init__.py ^
    create_field/basic_objects.py ^
    create_field/field_config.py ^
    create_field/field_manager.py ^
    create_field/field_parser.py ^
    create_field/pingpong_system.py ^
    create_field/simulation_manager.py

if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to protect create_field module!
    pause
    exit /b 1
)

echo กำลังคัดลอกไฟล์ที่จำเป็น...

REM คัดลอกโฟลเดอร์ resource ทั้งหมด
if exist "mission_pad_templates" (
    xcopy mission_pad_templates protected\mission_pad_templates\ /E /I /Y > nul
    echo ✓ Copied mission_pad_templates
)

if exist "export_model" (
    xcopy export_model protected\export_model\ /E /I /Y > nul
    echo ✓ Copied export_model
)

if exist "Qrcode" (
    xcopy Qrcode protected\Qrcode\ /E /I /Y > nul
    echo ✓ Copied Qrcode
)

if exist "captured_images" (
    xcopy captured_images protected\captured_images\ /E /I /Y > nul
    echo ✓ Copied captured_images
)

REM คัดลอกไฟล์สำคัญ
copy requirements.txt protected\ > nul 2>&1
echo ✓ Copied requirements.txt

echo.
echo ✅ ป้องกันโค้ดเสร็จสิ้น!
echo 📁 ไฟล์ที่ป้องกันแล้วอยู่ในโฟลเดอร์ 'protected'
echo.
echo 🛡️ คุณสมบัติการป้องกัน:
echo   • JIT Protection (--enable-jit)
echo   • String Encryption (--mix-str)
echo   • Call Protection (--assert-call)
echo   • Import Protection (--assert-import)
echo   • Private Mode (--private)
echo   • Restricted Mode (--restrict)
echo.
pause
