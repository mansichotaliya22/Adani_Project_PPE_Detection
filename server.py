from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import sqlite3
import os
import asyncio
from utils import init_db, violation_worker_task, violation_queue
from src.detection.engine import DetectionEngine
 
# ── Step 1: Create app ────────────────────────────────────────────────────
app = FastAPI(title="SafeSight AI API")
 
# ── Step 2: Add ALL middleware IMMEDIATELY after app creation ─────────────
# This MUST come before any @app.on_event, @app.websocket, @app.get, app.mount
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ── Step 3: Mount static files ────────────────────────────────────────────
if not os.path.exists("data/violations"):
    os.makedirs("data/violations")
app.mount("/data/violations", StaticFiles(directory="data/violations"), name="violations")
 
# ── Step 4: Create engine ─────────────────────────────────────────────────
engine: DetectionEngine = None
 
# ── Step 5: Define helper functions ───────────────────────────────────────
async def violation_bridge():
    """Polls engine stats for pending violations and moves them to the async queue."""
    while True:
        try:
            if engine and engine.is_running and 'pending_violation' in engine.stats:
                v_data = engine.stats.pop('pending_violation')
                violation_queue.put_nowait({
                    'type': v_data['type'],
                    'area': engine.settings.get('work_area', 'Factory'),
                    'frame': v_data['frame'],
                    'email_alerts': True
                })
        except Exception:
            pass
        await asyncio.sleep(0.1)
 
# ── Step 6: Register startup event ───────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    global engine
    engine = DetectionEngine()
    await init_db()
    asyncio.create_task(violation_worker_task())
    asyncio.create_task(violation_bridge())
 
# ── Step 7: WebSocket route ───────────────────────────────────────────────
@app.websocket("/ws/video")
async def video_websocket(websocket: WebSocket):
    origin = websocket.headers.get("origin", "")
    if origin not in ["http://localhost:5173"]:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    try:
        while True:
            if engine and engine.is_running:
                frame, _ = engine.get_frame()
                if frame is not None:
                    _, buffer = cv2.imencode(
                        '.jpg', frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 60]  # Reduce from 70 to 60
                    )
                    await websocket.send_bytes(buffer.tobytes())
                    await asyncio.sleep(0)  # Yield to event loop but no fixed delay
                else:
                    await asyncio.sleep(0.01)  # Only sleep if no frame available
            else:
                await asyncio.sleep(0.1)  # Sleep longer when engine not running
    except WebSocketDisconnect:
        print("Video WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
 
# ── Step 8: HTTP routes ───────────────────────────────────────────────────
@app.get("/api/stats")
async def get_stats():
    if not engine:
        return {"people_count": 0, "ppe_violations": 0, "roi_violations": 0, "running": False}
    return engine.get_stats()
 
@app.get("/api/violations")
async def get_violations(limit: int = 20):
    conn = sqlite3.connect("safesight.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM violations ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    violations = [dict(row) for row in rows]
    conn.close()
    return violations
 
@app.post("/api/start")
async def start_monitoring(source: str = "0", conf: float = 0.5):
    try:
        engine.settings['conf'] = conf
        src = int(source) if source.isdigit() else source
        engine.start(source=src)
        return {"status": "started", "source": source}
    except Exception as e:
        return {"status": "error", "message": str(e)}
 
@app.post("/api/stop")
async def stop_monitoring():
    engine.stop()
    return {"status": "stopped"}
 
@app.post("/api/settings")
async def update_settings(settings: dict):
    if "conf_threshold" in settings:
        engine.settings['conf'] = settings["conf_threshold"]
    if "work_area" in settings:
        engine.settings['work_area'] = settings["work_area"]
    return {"status": "updated", "settings": settings}
 
# ── Step 9: Entrypoint ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)