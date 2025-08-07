#!/usr/bin/env python3
"""
Create a test user for ChatScribe
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.database import SessionLocal
from app.crud.crud import create_user, get_user_by_username
from app.schemas.schemas import UserCreate

def create_test_user():
    """Create a test user"""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = get_user_by_username(db, "demo")
        if existing_user:
            print("Test user 'demo' already exists!")
            return
        
        # Create test user
        user_data = UserCreate(
            username="demo",
            email="demo@example.com",
            password="password123"
        )
        
        user = create_user(db, user_data)
        print(f"Test user created successfully!")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print("Password: password123")
        
    except Exception as e:
        print(f"Error creating test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
