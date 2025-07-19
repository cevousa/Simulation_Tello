@echo off
title Drone Odyssey Launcher Builder - Final Version
color 0A

echo ==========================================
echo   🚁 Drone Odyssey Launcher Builder
echo   📦 Final Optimized Version
echo ==========================================
echo.

echo 🔍 Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

echo 🔍 Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo 🗑️ Cleaning previous builds...
if exist "dist\DroneOdysseyLauncher" (
    echo    Removing old dist folder...
    rmdir /s /q "dist\DroneOdysseyLauncher"
)
if exist "build\DroneOdysseyLauncher" (
    echo    Removing old build folder...
    rmdir /s /q "build\DroneOdysseyLauncher"
)

echo.
echo 🔨 Building executable (this may take 3-5 minutes)...
echo    Using optimized spec file: DroneOdysseyLauncher_Final.spec
echo.

pyinstaller --clean --noconfirm DroneOdysseyLauncher_Final.spec

echo.
if exist "dist\DroneOdysseyLauncher\DroneOdysseyLauncher.exe" (
    echo ✅ BUILD SUCCESSFUL!
    echo.
    echo 📁 Location: dist\DroneOdysseyLauncher\
    echo 📄 Executable: DroneOdysseyLauncher.exe
    echo 📏 Size: 
    for %%A in ("dist\DroneOdysseyLauncher\DroneOdysseyLauncher.exe") do echo    %%~zA bytes
    echo.
    echo 🧪 TESTING...
    cd dist\DroneOdysseyLauncher
    echo    Starting launcher in 3 seconds...
    timeout /t 3 /nobreak >nul
    start "" "DroneOdysseyLauncher.exe"
    cd ..\..
    echo.
    echo 🎉 Launcher started successfully!
    echo 📋 You can now distribute the entire 'dist\DroneOdysseyLauncher' folder
) else (
    echo ❌ BUILD FAILED!
    echo.
    echo 🔍 Check the output above for errors.
    echo 💡 Common issues:
    echo    - Missing dependencies
    echo    - Python path issues
    echo    - Insufficient disk space
    echo.
    echo 📄 Check these files for more info:
    echo    - build\DroneOdysseyLauncher\warn-DroneOdysseyLauncher.txt
    echo    - build\DroneOdysseyLauncher\xref-DroneOdysseyLauncher.html
)

echo.
echo ✨ Build process completed!
pause
