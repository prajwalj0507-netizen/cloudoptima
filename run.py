#!/usr/bin/env python3
"""
CloudOptima Launch Runner
Starts the FastAPI backend and serves the interactive multi-cloud optimization dashboard.
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)

import uvicorn
import threading
import time
import webbrowser

def open_browser():
    time.sleep(1.2)
    try:
        webbrowser.open("http://localhost:8000/")
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 70)
    print(" CloudOptima: Multi-Cloud Waste Detection & Risk Governance Pipeline")
    print("=" * 70)
    print(" Starting server on http://localhost:8000")
    print(" - Web Dashboard: http://localhost:8000/")
    print(" - Interactive API Docs: http://localhost:8000/docs")
    print(" - Demo Mode: ENABLED (Zero AWS/Azure/GCP billing required)")
    print("=" * 70)
    
    # Launch browser automatically
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
