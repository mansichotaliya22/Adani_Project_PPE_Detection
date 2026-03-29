import subprocess
import time
import sys
import os

def run():
    print("Starting SafeSight AI...")

    # Start FastAPI Backend
    print("Starting Backend (FastAPI) on http://localhost:8001...")
    backend_proc = subprocess.Popen([sys.executable, "server.py"])

    # Start Frontend (Vite)
    print("Starting Frontend (React) on http://localhost:5173...")
    # Note: Requires 'npm install' to be run first in frontend/
    try:
        frontend_proc = subprocess.Popen(["npm", "run", "dev"], cwd="frontend", shell=True)
    except FileNotFoundError:
        print("Error: 'npm' not found. Please ensure Node.js is installed.")
        backend_proc.terminate()
        return

    print("\nSafeSight AI is running!")
    print("- Dashboard: http://localhost:5173")
    print("- API Docs: http://localhost:8001/docs")
    print("\nPress Ctrl+C to stop all services.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    run()
