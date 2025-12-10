# Smart ASCII Webcam

A high-tech, "Cyber-Glass" webcam application that transforms your video feed into dynamic ASCII art in real-time. It uses Computer Vision to detect your hand, adjusting the resolution based on proximity and changing color themes based on gestures.

## Features

- **Smart Hand Detection**: Uses OpenCV/Computer Vision to segment your hand from the background.
- **Dynamic Resolution**: 
  - **Close Hand**: High resolution, detailed ASCII.
  - **Far Hand**: Low resolution, abstract/blocky ASCII.
- **Gesture Control**:
  - **No Hand detected**: 🔴 **Red** (Standby)
  - **Hand Side / Fist**: 🔵 **Blue** (Interactive)
  - **Open Hand**: 🟢 **Green** (Active)
- **Premium Aesthetic**:
  - CRT Scanline effects.
  - Neon glows and Glassmorphism UI.
  - Smooth transitions.

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

## Tech Stack

- **Backend**: Python (FastAPI, OpenCV, NumPy)
- **Frontend**: HTML5, CSS3 (Variables, Flexbox), JavaScript (WebSockets)
- **Protocol**: WebSocket for real-time frame streaming (JSON + ASCII text)

## Troubleshooting

- **No Camera Found**: The app will automatically fallback to a "Dummy" noise generator if no webcam is accessible.
- **Colors flickering**: Try improving your lighting. The system uses skin-color detection which requires decent light.
