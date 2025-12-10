import cv2
import numpy as np
import math

class ImageProcessor:
    def __init__(self):
        # ASCII ramp (Density)
        self.ascii_chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
        
        # Skin color range (YCrCb) - Generally better than HSV
        self.lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        self.upper_skin = np.array([255, 173, 127], dtype=np.uint8)

    def frame_to_ascii(self, frame, width=100):
        # 1. Resize
        height, orig_width = frame.shape[:2]
        # Aspect ratio correction for typical fonts (approx 0.55 height/width)
        aspect_ratio = height / orig_width
        new_height = int(width * aspect_ratio * 0.55) 
        resized = cv2.resize(frame, (width, new_height))
        
        # 2. Grayscale & Contrast enhancement (CLAHE)
        # This makes details visible even in bad lighting
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # 3. Map to characters
        # Using a ramp that has good visual weight distribution
        # " " is black. "@" is white (full pixel density).
        chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
        
        lines = []
        rows, cols = gray.shape
        
        for r in range(rows):
            line = ""
            for c in range(cols):
                pixel_val = gray[r, c]
                idx = int(pixel_val / 255 * (len(chars) - 1))
                line += chars[idx]
            lines.append(line)
            
        return lines

    def process(self, frame):
        # Downscale for analysis (Speed)
        proc_frame = cv2.resize(frame, (320, 240))
        proc_frame = cv2.GaussianBlur(proc_frame, (5, 5), 0)
        
        # Convert to YCrCb for skin detection
        ycrcb = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2YCrCb)
        mask = cv2.inRange(ycrcb, self.lower_skin, self.upper_skin)
        
        # Clean mask
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Base resolution higher for better readability
        target_width = 120 
        color_theme = "default"
        
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)
            
            if area > 3000: 
                # Distance Logic
                ratio = area / (proc_frame.shape[0] * proc_frame.shape[1])
                ratio = max(0.0, min(ratio, 0.8))
                
                # Dynamic Resolution: 120 (Far) -> 250 (Close)
                target_width = int(120 + (ratio * 130))
                
                # Gesture Logic
                hull = cv2.convexHull(max_contour)
                hull_indices = cv2.convexHull(max_contour, returnPoints=False)
                
                try:
                    defects = cv2.convexityDefects(max_contour, hull_indices)
                    count_defects = 0
                    
                    if defects is not None:
                        for i in range(defects.shape[0]):
                            s, e, f, d = defects[i, 0]
                            start = tuple(max_contour[s][0])
                            end = tuple(max_contour[e][0])
                            far = tuple(max_contour[f][0])
                            
                            if d > 1000:
                                a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                                b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                                c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
                                angle = math.acos((b**2 + c**2 - a**2) / (2*b*c)) * 57
                                if angle <= 90:
                                    count_defects += 1
                    
                    if count_defects >= 3:
                        color_theme = "neon-green"
                    elif count_defects == 0:
                        color_theme = "neon-red"
                    else:
                        color_theme = "neon-blue"
                        
                except Exception:
                    pass
        
        # Generate ASCII
        ascii_lines = self.frame_to_ascii(frame, width=target_width)
        
        return {
            "ascii": ascii_lines,
            "theme": color_theme,
            "resolution": target_width
        }
