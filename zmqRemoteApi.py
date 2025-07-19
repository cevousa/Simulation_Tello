import zmq
import cbor2 as cbor
import uuid

class RemoteAPIClient:
    def __init__(self, host='localhost', port=23000, cntPort=-1, verbose=None):
        """
        เชื่อมต่อกับ CoppeliaSim ผ่าน ZMQ Remote API
        
        Args:
            host: ที่อยู่ของ CoppeliaSim (ปกติ localhost)
            port: พอร์ตหลัก (ปกติ 23000)
            cntPort: พอร์ตสำหรับ continuous data (ปกติ 23001)
            verbose: แสดงข้อความ debug หรือไม่
        """
        self.context = zmq.Context()
        self.verbose = verbose
        # REQ socket สำหรับส่งคำสั่ง
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{host}:{port}')
        
        # REQ socket สำหรับ subscriptions
        if cntPort == -1:
            cntPort = port + 1
        self.cntSocket = self.context.socket(zmq.REQ)
        self.cntSocket.connect(f'tcp://{host}:{cntPort}')
        
        if self.verbose:
            print(f"Connected to CoppeliaSim at {host}:{port}")
        
    def __del__(self):
        """ปิดการเชื่อมต่อเมื่อ object ถูกลบ"""
        try:
            if hasattr(self, 'socket'):
                self.socket.close()
            if hasattr(self, 'cntSocket'):
                self.cntSocket.close()
            if hasattr(self, 'context'):
                self.context.term()
        except:
            pass
    
    def call(self, funcName, args):
        """
        เรียกใช้ฟังก์ชันใน CoppeliaSim
        
        Args:
            funcName: ชื่อฟังก์ชัน เช่น 'sim.startSimulation'
            args: arguments ของฟังก์ชัน
            
        Returns:
            ผลลัพธ์จากฟังก์ชัน
        """
        # สร้างข้อความส่ง
        msg = {
            'func': funcName,
            'args': args,
            'id': str(uuid.uuid4())
        }
        
        # แปลงเป็น CBOR และส่ง
        rawMsg = cbor.dumps(msg)
        
        if self.verbose:
            print(f'Sending: {funcName}({args})')
        
        self.socket.send(rawMsg)
        
        # รับและแปลงผลลัพธ์
        responseRaw = self.socket.recv()
        response = cbor.loads(responseRaw)
        
        if self.verbose:
            print(f'Received: {response}')
            
        # ตรวจสอบผลลัพธ์
        if response.get('success', False):
            return response.get('ret')
        else:
            error_msg = response.get('error', 'Unknown error')
            raise Exception(f"Remote function call failed: {error_msg}")
    
    def getObject(self, name):
        """
        สร้าง object สำหรับเรียกใช้ฟังก์ชัน
        
        Args:
            name: ชื่อ object เช่น 'sim'
            
        Returns:
            RemoteAPIObject ที่สามารถเรียกใช้ฟังก์ชันได้
        """
        return RemoteAPIObject(name, self)

class RemoteAPIObject:
    def __init__(self, name, client):
        """
        Object สำหรับเรียกใช้ฟังก์ชันใน CoppeliaSim
        
        Args:
            name: ชื่อ object
            client: RemoteAPIClient instance
        """
        self._name = name
        self._client = client
    
    def __getattr__(self, name):
        """สร้างฟังก์ชันสำหรับเรียกใช้ method ต่างๆ"""
        def wrapper(*args):
            full_func_name = f'{self._name}.{name}'
            return self._client.call(full_func_name, args)
        return wrapper
    
    def __call__(self, *args):
        """เรียกใช้ object เป็นฟังก์ชัน"""
        return self._client.call(self._name, args)
    
    