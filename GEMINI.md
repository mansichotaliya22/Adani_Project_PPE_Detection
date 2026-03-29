# SafeSight AI - Engineering Mandates

## Workflow Orchestration
1. **Safety-First Validation:**
   - Before deploying any change to the detection logic (PPE checks, ROI math), you MUST verify it against the `tests/` suite.
   - For UI changes, ensure real-time video stream latency is minimized (aim for < 50ms overhead).

2. **Model Integrity:**
   - ALWAYS verify the existence of `models/ppe_yolov8s.pt` before starting implementation of inference-related features.
   - If the model is missing, proactively suggest running `download_model.py`.

3. **Privacy & Logging:**
   - Ensure all violation snapshots are stored in the `data/violations/` structure correctly.
   - Never log raw frame data to the console; only log metadata (timestamps, violation types).

4. **Alerting Reliability:**
   - When modifying `src/utils/mailer.py` or `src/utils/alert.py`, perform a "dry run" check to ensure throttling logic (e.g., 1 email per minute) is preserved.

5. **Plan Mode for Logic:**
   - Use `enter_plan_mode` for any changes involving coordinate geometry (ROI polygons) or centroid tracking.

## Technical Standards
- **Vision:** Use `opencv-python` for frame manipulation and `ultralytics` for inference.
- **Frontend:** React (TypeScript) for the dashboard, using WebSockets or a optimized FastAPI bridge for real-time video.
- **Database:** SQLite for violation history, following the schema in `migrate.py`.

## Self-Improvement Loop
- If the detection confidence is too low or alerts are firing incorrectly, update `lessons.md` with the specific lighting or distance parameters that caused the edge case.
