import cv2
import time
import threading
import numpy as np

class Camera:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Camera, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.cap = None
        self.use_dummy = False
        self.dummy_step = 0
        self.lock = threading.Lock()
        
        # Explicit priority for Index 0 (Main) then others.
        # Since we use Singleton, we invest time to find the BEST camera once.
        preferred_indices = [0, 1, 2, 3] 
        
        for i in preferred_indices:
            try:
                # Try explicit V4L2 backend
                cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
                # Set format to MJPG which is widely supported and high res
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                if cap.isOpened():
                    # Read one frame to verify
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Heuristic: Reject if Greyscale (possible IR camera)
                        # But OpenCV returns BGR even for grey...
                        # Check resolution. IR is usually small (640x360). Main is usually HD (1280x720).
                        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        
                        if w < 640 and i > 0:
                            print(f"Index {i} opened but resolution {w} is suspicious. Skipping.")
                            cap.release()
                            continue
                            
                        print(f"Index {i} opened and verified. Width: {w}")
                        self.cap = cap
                        break
                    else:
                        print(f"Index {i} opened but failed to read frame.")
                        cap.release()
            except Exception as e:
                print(f"Index {i} exception: {e}")

        if self.cap is None:
            print("Warning: Could not open any physical camera. Using DUMMY CAMERA.")
            self.use_dummy = True

    def get_frame(self):
        with self.lock:
            if self.use_dummy:
                self.dummy_step += 1
                return self._generate_dummy()
                
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    return frame
                else:
                    print("Camera read failed.")
                    return None
            return None

    def _generate_dummy(self):
        # Create a 640x480 frame with some moving pattern
        x = np.linspace(0, 10, 640)
        y = np.linspace(0, 10, 480)
        xv, yv = np.meshgrid(x, y)
        z = np.sin(xv + self.dummy_step * 0.1) * np.cos(yv + self.dummy_step * 0.1)
        frame = ((z + 1) * 127.5).astype(np.uint8)
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    def release(self):
        # In singleton Mode, we rarely assume we want to close it unless app exit.
        # But we provide the method.
        # CAVEAT: If one client calls release, it kills it for everyone.
        # So we should probably NOT release on individual client disconnect.
        pass
