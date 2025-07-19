#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน ProximitySensorManager แบบง่าย ๆ
"""

import time
import sys
import os



from drone_controller import NaturalDroneController

def simple_height_check():
    """ฟังก์ชันตรวจสอบความสูงแบบง่าย ๆ"""

    # สร้าง drone controller
    drone = NaturalDroneController(use_simulation=True)
    
    if not drone.use_simulation:
        print("❌ ไม่สามารถเชื่อมต่อได้")
        return
    
    try:
        # สร้าง sensor manager
        from drone_controller import ProximitySensorManager
        sensor = ProximitySensorManager(drone.sim, drone.drone_handle)

        drone.enable_mission_pads()
        
        if not sensor.setup():
            print("❌ ไม่สามารถตั้งค่า sensor ได้")
            return
        
        # ขึ้นบิน
        drone.takeoff(1.1)

        drone.move_forward(1.0)
        detected_id2 = drone.get_mission_pad_id()
        print(f"🎯 Detected Mission Pad ID: {detected_id2}")
        time.sleep(1)

        drone.move_forward(1.0)
        detected_id3 = drone.get_mission_pad_id()
        print(f"🎯 Detected Mission Pad ID: {detected_id3}")
        time.sleep(1)

        drone.move_forward(1)
        # วัดความสูง 5 ครั้ง
        for i in range(5):
            height = sensor.get_height()
            if height:
                print(f"ครั้งที่ {i+1}: {height:.2f} เมตร")
            else:
                print(f"ครั้งที่ {i+1}: ไม่มีข้อมูล")
            time.sleep(1)
        
        # ลงจอด
        drone.land()
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        drone.land()

    finally:
        # ปิดการใช้งาน Mission Pad detection
        drone.disable_mission_pads()
        drone.disconnect()

if __name__ == "__main__":
    simple_height_check()
