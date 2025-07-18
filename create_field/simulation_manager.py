"""
Simulation Management Module
จัดการการเชื่อมต่อและควบคุม CoppeliaSim
"""

import time
try:
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from zmqRemoteApi import RemoteAPIClient

class SimulationManager:
    """คลาสสำหรับจัดการการจำลอง CoppeliaSim"""
    
    def __init__(self):
        self.client = RemoteAPIClient()
        self.sim = self.client.getObject('sim')
        self.simulation_running = False
        self._physics_fixed = False
        
        print("🔗 Connected to CoppeliaSim")
    
    def start_simulation(self):
        """เริ่มการจำลอง"""
        try:
            self.sim.startSimulation()
            self.simulation_running = True
            print("✅ Simulation started")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Failed to start simulation: {e}")
            return False
    
    def stop_simulation(self):
        """หยุดการจำลอง"""
        try:
            self.sim.stopSimulation()
            self.simulation_running = False
            print("⏹️ Simulation stopped")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Failed to stop simulation: {e}")
            return False
    
    def pause_simulation(self):
        """หยุดชั่วคราว"""
        try:
            self.sim.pauseSimulation()
            print("⏸️ Simulation paused")
            return True
        except Exception as e:
            print(f"❌ Failed to pause simulation: {e}")
            return False
    
    def setup_physics_engine(self, config):
        """ตั้งค่า Physics Engine"""
        if self._physics_fixed:
            return
        
        print("🔍 Setting up physics engine...")
        
        try:
            self.sim.setFloatParameter(
                self.sim.floatparam_simulation_time_step, 
                config.physics['simulation_time_step']
            )
            self.sim.setBoolParameter(
                self.sim.boolparam_realtime_simulation, 
                config.physics['realtime_simulation']
            )
            print("✅ Physics engine configured")
        except Exception as e:
            print(f"⚠️ Physics engine warning: {e}")
        
        self._physics_fixed = True
    
    def remove_objects(self, handles):
        """ลบวัตถุจากการจำลอง"""
        if not handles:
            return
        
        try:
            self.sim.removeObjects(handles)
            print(f"🗑️ Removed {len(handles)} objects")
        except Exception as e:
            print(f"⚠️ Warning during object removal: {e}")
    
    def is_simulation_running(self):
        """ตรวจสอบว่าการจำลองกำลังทำงานหรือไม่"""
        try:
            return self.sim.getSimulationState() != self.sim.simulation_stopped
        except:
            return False
