#!/usr/bin/env python3
"""
Unified Remote Teleprompter Application
Combines backend API and frontend serving with server-side rendering support.
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Change to backend directory to ensure relative paths work
os.chdir(backend_dir)

# Import and run the main application
from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)