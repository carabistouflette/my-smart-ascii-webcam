import cv2
import numpy as np
import math
from collections import deque
import statistics

class ImageProcessor:
    def __init__(self):
        # ASCII ramp (Density)
        self.ascii_chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
        
        # Skin color range (YCrCb)
        self.lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        self.upper_skin = np.array([255, 173, 127], dtype=np.uint8)
        
        # Smoothing buffers
        self.res_history = deque(maxlen=10) # Increased for smoother zoom
        self.theme_history = deque(maxlen=15) # Optimized for responsiveness but stable
        
        # State
        self.prev_res = 100
        self.alpha_res = 0.2 # Smoothing factor for resolution

    def frame_to_ascii(self, frame, width=100):
        # 1. Resize
        height, orig_width = frame.shape[:2]
        aspect_ratio = height / orig_width
        new_height = int(width * aspect_ratio * 0.55) 
        resized = cv2.resize(frame, (width, new_height))
        
        # 2. Grayscale & Contrast
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # 3. Map to characters
        chars = self.ascii_chars
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
        # Pre-processing
        # Resize for consistent detection logic regardless of high-res input
        proc_frame = cv2.resize(frame, (320, 240))
        # Gaussian Blur helps reduce noise in the mask
        proc_frame = cv2.GaussianBlur(proc_frame, (5, 5), 0)
        
        # Skin Detection (YCrCb)
        ycrcb = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2YCrCb)
        mask = cv2.inRange(ycrcb, self.lower_skin, self.upper_skin)
        
        # Morphological Cleanup
        kernel_open = np.ones((5,5), np.uint8)
        kernel_close = np.ones((20,20), np.uint8) # Aggressive closing to fill holes in hand
        
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Logic Variables
        current_theme = "neon-red"
        target_res = 30 # Default low resolution
        has_hand = False # Flag to track if a valid hand was detected
        
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)
            
            # Threshold to consider it a valid hand
            # Added Max Area to prevent full-screen background noise (e.g. lighting change)
            if 2500 < area < 50000: 
                # Face Rejection Heuristic
                M = cv2.moments(max_contour)
                if M["m00"] > 0:
                    cy = int(M["m01"] / M["m00"])
                    
                    # If centroid is in the top 20% of screen, ignore it (likely face)
                    if cy > proc_frame.shape[0] * 0.2:
                        
                        has_hand = True
                        
                        # --- 1. Resolution Logic (Distance) ---
                        normalized_area = min(area / 20000.0, 1.0)
                        target_res = 40 + int(math.sqrt(normalized_area) * 140)
                        
                        # --- 2. Gesture Logic (Convexity Defects + Solidity) ---
                        
                        # Bounding Rect for Aspect Ratio
                        x, y, w, h = cv2.boundingRect(max_contour)
                        aspect_ratio = float(w) / h
                        
                        # Convex Hull & Solidity
                        hull = cv2.convexHull(max_contour, returnPoints=False)
                        hull_points = cv2.convexHull(max_contour, returnPoints=True)
                        hull_area = cv2.contourArea(hull_points)
                        solidity = float(area) / hull_area if hull_area > 0 else 0
                        
                        finger_count = 0
                        if len(hull) > 3:
                            try:
                                defects = cv2.convexityDefects(max_contour, hull)
                                if defects is not None:
                                    for i in range(defects.shape[0]):
                                        s, e, f, d = defects[i, 0]
                                        start = tuple(max_contour[s][0])
                                        end = tuple(max_contour[e][0])
                                        far = tuple(max_contour[f][0])
                                        
                                        a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                                        b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                                        c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
                                        angle = math.acos(max(-1.0, min(1.0, (b**2 + c**2 - a**2) / (2*b*c)))) * 57
                                        
                                        if angle <= 90 and d > 1000: 
                                            finger_count += 1
                            except Exception:
                                pass

                        # Classification using 3 States
                        # 1. Green (Open Hand): Fingers visible OR Low Solidity
                        is_open = (finger_count >= 2) or (solidity < 0.76)
                        
                        # 2. Blue (Fist): High Solidity AND Compact Shape (Square-ish)
                        #    Should not be too elongated (which might comprise noise or arm)
                        is_fist = (solidity > 0.80) and (0.55 < aspect_ratio < 1.8)
                        
                        if is_open:
                            current_theme = "neon-green"
                        elif is_fist:
                            current_theme = "neon-blue"
                        else:
                            current_theme = "neon-red" # Confusing shape -> Treat as noise/nothing
                        
                        # Debug logic
                        if current_theme != "neon-red":
                            print(f"HAND: A:{area:<5.0f} S:{solidity:.2f} AR:{aspect_ratio:.2f} F:{finger_count} -> {current_theme}")
        
        if not has_hand:
            print("NO HAND")

        # --- Smoothing ---
        
        # 1. Smooth Resolution
        self.prev_res = int(self.prev_res * (1 - self.alpha_res) + target_res * self.alpha_res)
        final_res = self.prev_res
        
        # 2. Smooth Theme
        # FAST DECAY: If we don't see a hand (Red), vote multiple times to clear buffer quickly
        if current_theme == "neon-red":
             # Append multiple times to weigh 'No Hand' heavier than 'Hand'
             self.theme_history.append(current_theme)
             self.theme_history.append(current_theme)
             self.theme_history.append(current_theme)
        else:
             self.theme_history.append(current_theme)
             
        try:
            final_theme = statistics.mode(self.theme_history)
        except:
            final_theme = self.theme_history[-1]
            
        # Generate ASCII
        ascii_lines = self.frame_to_ascii(frame, width=final_res)
        
        return {
            "ascii": ascii_lines,
            "theme": final_theme,
            "resolution": final_res
        }
