from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from backend.camera import Camera
from backend.processor import ImageProcessor
import asyncio
import logging
import os

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ascii-webcam")

# Serve Frontend
app.mount("/client", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
async def root():
    return {"message": "Go to /client for the interface"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected")
    
    camera = None
    processor = None
    
    try:
        camera = Camera()
        processor = ImageProcessor()
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                await asyncio.sleep(0.01)
                continue
            
            # Process frame
            try:
                result = processor.process(frame)
                await websocket.send_json(result)
            except Exception as e:
                logger.error(f"Processing error: {e}")
                
            # Cap frame rate slightly to avoid overwhelming
            await asyncio.sleep(0.03) # ~30 FPS
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if camera:
            camera.release()
            logger.info("Camera released")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
