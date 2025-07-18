#!/usr/bin/env python3
"""
System Test Script
สคริปต์ทดสอบระบบทั้งหมด
"""

import os
import sys
import subprocess
import importlib

def test_dependencies():
    """ทดสอบ dependencies ที่จำเป็น"""
    print("🧪 Testing Dependencies...")
    
    required_packages = [
        'tkinter',
        'PIL', 
        'cv2',
        'numpy',
        'zmq',
        'qrcode',
        'pyzbar',
        'cryptography'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'cv2':
                import cv2
            else:
                importlib.import_module(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All dependencies satisfied!")
        return True

def test_license_system():
    """ทดสอบระบบ License"""
    print("\n🔐 Testing License System...")
    
    try:
        from license_manager import LicenseManager
        
        # สร้าง LicenseManager
        lm = LicenseManager()
        print(f"  ✓ Machine ID: {lm.machine_id}")
        
        # ทดสอบสร้าง License
        license_data = lm.create_license("Test User", "test@example.com", days_valid=30)
        print("  ✓ License creation")
        
        # ทดสอบตรวจสอบ License
        valid, result = lm.verify_license()
        if valid:
            print("  ✓ License verification")
            print(f"  ✓ License valid until: {result.get('expiry_date', 'Unknown')[:10]}")
        else:
            print(f"  ❌ License verification failed: {result}")
            return False
            
        # ทดสอบข้อมูล License
        license_info = lm.get_license_info()
        if license_info["valid"]:
            print(f"  ✓ License info: {license_info['days_left']} days left")
        else:
            print(f"  ❌ License info failed: {license_info.get('error')}")
            return False
            
        print("✅ License system working!")
        return True
        
    except Exception as e:
        print(f"❌ License system error: {e}")
        return False

def test_pyarmor():
    """ทดสอบ PyArmor"""
    print("\n🔒 Testing PyArmor...")
    
    try:
        result = subprocess.run(['pyarmor', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✓ PyArmor installed: {version}")
            return True
        else:
            print("  ❌ PyArmor not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ❌ PyArmor not found")
        print("  Install with: pip install pyarmor")
        return False

def test_pyinstaller():
    """ทดสอบ PyInstaller"""
    print("\n📦 Testing PyInstaller...")
    
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✓ PyInstaller installed: {version}")
            return True
        else:
            print("  ❌ PyInstaller not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ❌ PyInstaller not found")
        print("  Install with: pip install pyinstaller")
        return False

def test_file_structure():
    """ทดสอบโครงสร้างไฟล์"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        'launcher.py',
        'license_manager.py',
        'protect.bat',
        'build.bat',
        'requirements.txt',
        'create_field/__init__.py',
        'create_field/basic_objects.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files present!")
        return True

def test_gui_imports():
    """ทดสอบการ import GUI components"""
    print("\n🖼️ Testing GUI Imports...")
    
    try:
        import tkinter as tk
        from tkinter import messagebox, filedialog, ttk
        print("  ✓ tkinter components")
        
        # ทดสอบสร้างหน้าต่างง่ายๆ
        root = tk.Tk()
        root.withdraw()  # ซ่อนหน้าต่าง
        print("  ✓ tkinter window creation")
        root.destroy()
        
        print("✅ GUI components working!")
        return True
        
    except Exception as e:
        print(f"❌ GUI import error: {e}")
        return False

def run_full_test():
    """รันการทดสอบทั้งหมด"""
    print("🧪 Drone Odyssey Field Creator - System Test")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("File Structure", test_file_structure),
        ("GUI Components", test_gui_imports),
        ("License System", test_license_system),
        ("PyArmor", test_pyarmor),
        ("PyInstaller", test_pyinstaller)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # สรุปผล
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! System ready for deployment.")
        print("\n🚀 Next steps:")
        print("  1. Run: protect.bat")
        print("  2. Run: build.bat")
        print("  3. Test the generated .exe file")
    else:
        print("⚠️ Some tests failed. Please fix the issues before proceeding.")
        print("\n🔧 Recommendations:")
        print("  1. Install missing dependencies: pip install -r requirements.txt")
        print("  2. Check file paths and permissions")
        print("  3. Verify PyArmor and PyInstaller installations")
    
    return all_passed

if __name__ == "__main__":
    run_full_test()
