# Plan: SafeSight AI Frontend Upgrade (React + FastAPI)

## Objective
Replace the current Streamlit UI with a high-fidelity React-based dashboard served by a FastAPI backend to improve real-time performance, interactivity, and visual design.

## Key Files & Context
- `app.py`: Current Streamlit implementation (to be deprecated).
- `server.py`: New FastAPI backend.
- `src/ui/`: New React frontend directory.
- `safesight.db`: SQLite database for violations.

## Implementation Steps

### Phase 1: FastAPI Backend (`server.py`)
1.  **Core API Setup:**
    - Initialize FastAPI with CORS support for the React frontend.
    - Define a background task manager for the YOLO inference loop.
2.  **Streaming Endpoint:**
    - Implement `/api/video_feed` using `StreamingResponse` with MJPEG encoding.
3.  **Data Endpoints:**
    - `/api/violations`: GET recent violations from SQLite.
    - `/api/stats`: GET aggregate metrics (People, PPE, ROI).
    - `/api/settings`: GET/POST for monitoring configuration (confidence, ROI coordinates, email).
4.  **Control Endpoints:**
    - `/api/start`: Trigger the background monitoring task.
    - `/api/stop`: Gracefully stop the stream and background task.

### Phase 2: React Frontend (via Stitch)
1.  **Design System:**
    - Initialize a modern dashboard layout using Tailwind CSS.
2.  **Dashboard Components:**
    - `LiveStreamView`: Displays the video feed and provides a canvas for drawing ROI.
    - `MetricsCard`: Reusable component for "People Count", "PPE Violations", etc.
    - `ViolationLog`: A sidebar or bottom panel showing recent violation snapshots and metadata.
    - `ControlPanel`: Sidebar for confidence sliders, work area selection, and toggle buttons.
3.  **State Management:**
    - Use `react-query` or `useEffect` hooks to fetch stats and logs at regular intervals (polling).

### Phase 3: Integration & Migration
1.  **Refactor Inference:**
    - Decouple the YOLO logic from `app.py` into a reusable `src/detection/engine.py`.
2.  **Asset Management:**
    - Ensure the frontend can access the `data/violations/` folder to display snapshot thumbnails (FastAPI `StaticFiles`).
3.  **Testing:**
    - Verify the React dashboard correctly updates metrics and displays the video feed without significant lag.

## Verification & Testing
- **Latency Check:** Measure FPS in the browser vs. the Streamlit version.
- **Database Consistency:** Ensure violations logged via the new backend appear correctly in `safesight.db`.
- **E2E Flow:** Start monitoring -> Trigger violation -> Confirm visual alert in React UI -> Check email.
