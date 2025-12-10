import cv2
import numpy as np
import math
from collections import deque
import statistics

class ImageProcessor:
    def __init__(self):
        # ASCII ramp (Density)
        self.ascii_chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
        
        # Skin color range (YCrCb) - Generally better than HSV
        self.lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        self.upper_skin = np.array([255, 173, 127], dtype=np.uint8)
        
        # Smoothing History
        self.res_history = deque(maxlen=5) # Smooth resolution (Responsive)
        self.theme_history = deque(maxlen=30) # Heavy smoothing for stability

    def frame_to_ascii(self, frame, width=100):
        # 1. Resize
        height, orig_width = frame.shape[:2]
        # Aspect ratio correction for typical fonts (approx 0.55 height/width)
        aspect_ratio = height / orig_width
        new_height = int(width * aspect_ratio * 0.55) 
        resized = cv2.resize(frame, (width, new_height))
        
        # 2. Grayscale & Contrast enhancement (CLAHE)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        # This makes details visible even in bad lighting
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # 3. Map to characters
        # Standard balanced ramp for better detail preservation
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
        
        # Default: No Hand -> Red
        raw_target_width = 40 
        raw_theme = "neon-red"
        
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)
            
            # Moderate threshold
            if area > 4000: 
                # Filter out face: Check if contour is in the TOP 40% of the frame
                # Face is usually at the top, hand is usually in the middle/bottom
                M = cv2.moments(max_contour)
                is_hand = True
                
                if M["m00"] > 0:
                    cy = int(M["m01"] / M["m00"]) # Centroid Y
                    frame_height = proc_frame.shape[0]
                    
                    # If centroid is in top 40%, it's likely the face -> ignore
                    if cy < frame_height * 0.4:
                        is_hand = False
                
                if is_hand:
                    # Distance Logic: Map Area Ratio to Width
                    frame_area = proc_frame.shape[0] * proc_frame.shape[1]
                    ratio = area / frame_area
                    
                    # More aggressive scaling for visible effect
                    # Far (small ratio ~0.02) -> 20 chars (very blocky)
                    # Close (large ratio ~0.5) -> 400 chars (detailed)
                    norm_dist = math.sqrt(ratio)
                    
                    raw_target_width = int(20 + (norm_dist * 600))
                    raw_target_width = max(20, min(raw_target_width, 400))
                    
                    # Gesture Logic using Hull Ratio
                    # Fist is compact (hull area ~ contour area)
                    # Open hand has gaps (hull area > contour area)
                    hull = cv2.convexHull(max_contour)
                    hull_area = cv2.contourArea(hull)
                    
                    if hull_area > 0:
                        # Ratio: 1.0 = perfect match (fist), > 1.0 = gaps (open)
                        solidity = area / hull_area
                        
                        # Fist: solidity close to 1.0 (compact)
                        # Open hand: solidity lower (gaps between fingers)
                        if solidity > 0.85:
                            raw_theme = "neon-blue"  # Fist (compact)
                        else:
                            raw_theme = "neon-green" # Open Hand (has gaps)
                    else:
                        raw_theme = "neon-green" # Fallback
        
        # Smoothing
        self.res_history.append(raw_target_width)
        self.theme_history.append(raw_theme)
        
        # Average Resolution
        smoothed_width = int(sum(self.res_history) / len(self.res_history))
        
        # Mode Theme (Most frequent in history)
        try:
            smoothed_theme = statistics.mode(self.theme_history)
        except:
            smoothed_theme = self.theme_history[-1]
        
        # Generate ASCII
        ascii_lines = self.frame_to_ascii(frame, width=smoothed_width)
        
        return {
            "ascii": ascii_lines,
            "theme": smoothed_theme,
            "resolution": smoothed_width
        }
