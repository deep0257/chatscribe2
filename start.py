#!/usr/bin/env python3
"""
Production startup script for ChatScribe on Render
"""
import os
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
