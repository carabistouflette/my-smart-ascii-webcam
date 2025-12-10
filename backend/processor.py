import cv2
import numpy as np
import math

class ImageProcessor:
    def __init__(self):
        # ASCII ramp
        self.ascii_chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
        
        # Skin color range (HSV)
        # Adjust these if detection is poor
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)

    def frame_to_ascii(self, frame, width=100):
        height, orig_width = frame.shape[:2]
        aspect_ratio = height / orig_width
        new_height = int(width * aspect_ratio * 0.55) 
        
        resized_frame = cv2.resize(frame, (width, new_height))
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
        
        idx = (gray_frame / 255 * (len(self.ascii_chars) - 1)).astype(int)
        
        lines = []
        for row in idx:
            line = "".join([self.ascii_chars[i] for i in row])
            lines.append(line)
            
        return lines

    def process(self, frame):
        # Downscale for processing speed
        proc_frame = cv2.resize(frame, (320, 240))
        hsv = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)
        
        # Morphological operations to clean noise
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.erode(mask, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        target_width = 80
        color_theme = "default"
        
        if contours:
            # Find largest contour (Hand)
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)
            
            if area > 2000: # Threshold to ignore noise
                # Distance Logic
                ratio = area / (proc_frame.shape[0] * proc_frame.shape[1])
                ratio = max(0.0, min(ratio, 0.6))
                target_width = int(60 + (ratio * 300)) # Scale resolution
                
                # Gesture Logic (Convex Hull)
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
                            
                            # Calculate sides of triangle
                            a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                            b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                            c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
                            
                            # Angle using cosine rule
                            angle = math.acos((b**2 + c**2 - a**2) / (2*b*c)) * 57
                            
                            if angle <= 90:
                                count_defects += 1
                    
                    # 0 defects ~= Fist (or 1 finger). 4 defects ~= Open hand (5 fingers)
                    if count_defects >= 3:
                        color_theme = "neon-green" # Open
                    elif count_defects == 0:
                        color_theme = "neon-red"   # Fist
                    else:
                        color_theme = "neon-blue"
                        
                except Exception:
                    pass
        
        ascii_lines = self.frame_to_ascii(frame, width=target_width)
        
        return {
            "ascii": ascii_lines,
            "theme": color_theme,
            "resolution": target_width
        }
