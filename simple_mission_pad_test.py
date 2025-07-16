#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน MissionPadDetector แบบง่าย
"""

from drone_controller import NaturalDroneController
import time

def simple_mission_pad_test():
    """ทดสอบการตรวจจับ Mission Pad แบบง่าย"""
    
    print("🚁 Starting simple mission pad test...")
    
    # เริ่มต้น drone controller
    drone = NaturalDroneController(use_simulation=True)
    
    try:
        # เปิดใช้งาน Mission Pad detection
        print("🔧 Enabling Mission Pad detection...")
        drone.enable_mission_pads()

        drone.takeoff(0.4)

        drone.move_forward(1.0)
        detected_id1 = drone.get_mission_pad_id()
        print(f"🎯 Detected Mission Pad ID: {detected_id1}")
        time.sleep(1)

        drone.move_forward(1.0)
        detected_id2 = drone.get_mission_pad_id()
        print(f"🎯 Detected Mission Pad ID: {detected_id2}")
        time.sleep(1)
                
        drone.move_forward(1.0)
        detected_id3 = drone.get_mission_pad_id()
        print(f"🎯 Detected Mission Pad ID: {detected_id3}")
        time.sleep(1)

        drone.move_forward(1.0)
        detected_id4 = drone.get_mission_pad_id()
        print(f"🎯 Detected Mission Pad ID: {detected_id4}")
        time.sleep(1)
            
        drone.land()
            
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        # ปิด Mission Pad detection
        drone.disable_mission_pads()
        drone.disconnect()

if __name__ == "__main__":
    
    # ทดสอบพื้นฐาน
    simple_mission_pad_test()
