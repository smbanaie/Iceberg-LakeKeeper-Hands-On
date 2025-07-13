#!/usr/bin/env python3
"""
Script to start the banking reconciliation API.
"""

import os
import sys
import uvicorn

# Add the project root to the Python path
sys.path.append("/opt/spark")

# Import the API app
from src.main.python.api.app import app

def main():
    """Start the API server."""
    print("Starting Banking Reconciliation API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
