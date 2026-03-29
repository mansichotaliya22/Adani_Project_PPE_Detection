# SafeSight AI - PPE & Safety Monitoring Dashboard

SafeSight AI is a computer-vision safety monitoring system that detects PPE compliance (Hard Hats, Vests) and behavioral violations (Running, Danger Zones) in real-time.

## 🚀 NEW: High-Fidelity Dashboard
The system has been upgraded with a modern **React + FastAPI** architecture for improved performance and a professional user experience.

### Features
- **Live Stream:** Processed YOLOv8 feed directly in the browser.
- **Real-time Stats:** Instant updates for People Count and Violations.
- **Violation Logs:** Visual history with snapshots and timestamps.
- **Dynamic Settings:** Adjust confidence and ROI without restarting.
- **Email Alerts:** Automated notifications with violation snapshots.

---

## 🛠️ Quick Start

### 1. Requirements
- **Python 3.9+**
- **Node.js 18+** (for the React Dashboard)

### 2. Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Download YOLOv8 Weights
python download_model.py

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Run
Launch both the backend and frontend with one command:
```bash
python run.py
```
- **Dashboard:** http://localhost:5173
- **Backend API:** http://localhost:8000

---

## 📁 Project Structure
- `server.py`: FastAPI backend & MJPEG stream server.
- `src/detection/engine.py`: Core YOLO inference and safety logic.
- `frontend/`: React dashboard (Vite + Tailwind).
- `safesight.db`: SQLite database for logs.
- `data/violations/`: Snapshot storage.

## ⚠️ Note
If you prefer the original basic Streamlit interface, you can still run it via `streamlit run app.py`.
