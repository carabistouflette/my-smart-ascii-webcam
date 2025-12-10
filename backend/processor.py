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
        aspect_ratio = height / orig_width
        new_height = int(width * aspect_ratio * 0.55) 
        resized = cv2.resize(frame, (width, new_height))
        
        # 2. Edge Detection (Sobel) for "Precision" look
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        mag, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)
        
        # 3. Map to characters
        lines = []
        rows, cols = gray.shape
        
        # Edge threshold
        edge_thresh = 150
        
        for r in range(rows):
            line = ""
            for c in range(cols):
                pixel_mag = mag[r, c]
                pixel_val = gray[r, c]
                
                if pixel_mag > edge_thresh:
                    # Use directional edges
                    ang = angle[r, c] % 180
                    if 45 <= ang < 135:
                        char = "|"
                    elif 0 <= ang < 45 or 135 <= ang < 180:
                        char = "-" # or _
                    else:
                        char = "+"
                else:
                    # Use density
                    idx = int(pixel_val / 255 * (len(self.ascii_chars) - 1))
                    char = self.ascii_chars[idx]
                line += char
            lines.append(line)
            
        return lines

    def process(self, frame):
        # Downscale for analysis (Speed)
        proc_frame = cv2.resize(frame, (320, 240))
        proc_frame = cv2.GaussianBlur(proc_frame, (5, 5), 0) # Reduce noise
        
        # Convert to YCrCb for skin detection
        ycrcb = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2YCrCb)
        mask = cv2.inRange(ycrcb, self.lower_skin, self.upper_skin)
        
        # Clean mask
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) # Remove specks
        mask = cv2.dilate(mask, kernel, iterations=1)         # Fill holes
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        target_width = 80
        color_theme = "default"
        
        if contours:
            # Find largest contour (Hand) used to ignore face/bg
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)
            
            # Simple heuristic: Hands are usually central or bottom. Faces are top.
            # But let's just stick to area for now.
            if area > 3000: 
                # Distance Logic
                ratio = area / (proc_frame.shape[0] * proc_frame.shape[1])
                ratio = max(0.0, min(ratio, 0.6))
                target_width = int(60 + (ratio * 150)) # Less aggressive scaling
                
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
                            
                            # Filter small defects (noise between fingers)
                            if d > 1000: # Depth threshold
                                a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                                b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                                c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
                                angle = math.acos((b**2 + c**2 - a**2) / (2*b*c)) * 57
                                if angle <= 90:
                                    count_defects += 1
                    
                    if count_defects >= 3:
                        color_theme = "neon-green" # Open
                    elif count_defects == 0:
                        color_theme = "neon-red"   # Fist
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
