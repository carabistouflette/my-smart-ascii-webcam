# Smart ASCII Webcam

A high-tech, "Cyber-Glass" webcam application that transforms your video feed into dynamic ASCII art in real-time. It uses Computer Vision to detect your hand, automatically adjusting the resolution based on proximity and changing color themes based on gestures.

## Features

- **Smart Hand Detection**: 
  - Uses **YCrCb skin-color segmentation** for robust detection across lighting conditions.
  - **Intelligent Face Rejection**: Automatically detects and ignores your face (top 20% of screen) to focus solely on hand interactions.
- **Dynamic Resolution**: 
  - **Close Hand**: High resolution (up to 180 chars wide) for detailed ASCII.
  - **Far Hand**: Low resolution (down to 40 chars wide) for an abstract, blocky aesthetic.
- **Gesture Control**:
  - **No Hand / Standby**: 🔴 **Red** (Neon Red).
  - **Fist (Compact Shape)**: 🔵 **Blue** (Neon Blue).
  - **Open Hand (Fingers detected)**: 🟢 **Green** (Neon Green).
- **Style**:
  - CRT Scanline effects & Vignette.
  - Neon glows and Glassmorphism UI.
  - Smooth 60FPS CSS transitions and adaptive resolution smoothing.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd my-smart-ascii-webcam
   ```

2. **Setup Python Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the Interface**:
   Open [http://localhost:8000/client](http://localhost:8000/client) in your browser.

## Technical Implementation

The application uses a sophisticated pipeline to ensure real-time performance and stability:

1. **Backend (Python/OpenCV)**:
    - **Preprocessing**: Frame is resized and blurred to reduce noise.
    - **Segmentation**: Converts RGB to YCrCb color space to isolate skin tones.
    - **Logic**: 
        - Calculates **Contours** and **Convexity Defects** to count fingers.
        - Computes **Solidity** (Area / Convex Hull Area) to distinguish between a Fist (solid) and Open Hand (sparse).
        - **Face Heuristic**: Rejects large centroids in the upper screen area.
    - **Smoothing**: Uses `deque` buffers and weighted moving averages to prevent flickering colors or jittery resolution changes.

2. **Frontend (Vanilla JS/CSS)**:
    - **Rendering**: Receives raw ASCII strings via WebSocket and renders them into a pre-formatted HTML container.
    - **Cyber-Glass UI**: Heavy use of `backdrop-filter: blur`, `box-shadow` for neon glows, and distinct CSS variables for theme switching.

## Troubleshooting

- **No Camera Found**: The app will automatically fallback to a "Dummy" noise generator if no webcam is accessible.
- **Colors flickering**: Try improving your lighting. The system uses skin-color detection which requires decent, warm lighting to work best against the background.
- **Hand not detected**: Ensure your hand is the primary skin-colored object in the frame and not too close to your face.
