import time
from drone_controller import *
    # ตัวอย่างการใช้งาน

# ไฟล์ทดสอบ
def main():
    drone = NaturalDroneController(use_simulation=True)
    
    try:
        print("🚁 Starting flight test...")
        drone.takeoff(1.0)
        drone.move_down(0.5)
        drone.rotate_clockwise(90)
        drone.move_forward(1)
        drone.hover(2.0)
        drone.take_bottom_picture()
        print("take a bottom picture!")
        drone.rotate_clockwise(270)
        drone.take_picture()        
        drone.move_forward(3)
        drone.land()
        print("✅ Flight test complete!")
        
    except KeyboardInterrupt:
        print("\n🚨 Test interrupted")
        drone.emergency_stop()
    
    finally:
        drone.disconnect()

def real():
    drone = NaturalDroneController(use_simulation=True)
    
    try:
        drone.take_picture()        
        print("take a picture!")   
        drone.take_bottom_picture()
        print("take a bottom picture!")
      
        
    except KeyboardInterrupt:
        print("\n🚨 Test interrupted")
        drone.emergency_stop()
    
    finally:
        drone.disconnect()

if __name__ == "__main__":
    #main()
    main()