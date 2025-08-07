#!/usr/bin/env python3
"""
Database initialization script for ChatScribe
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.database import engine
from app.models.models import Base

def create_tables():
    """Create database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    return True

if __name__ == "__main__":
    create_tables()
