#!/usr/bin/env python3
"""
Script to update database schema
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base
from models import Patient, User, StrokeScan, NIHSSAssessment

def update_database():
    try:
        print("Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("Creating new tables with updated schema...")
        Base.metadata.create_all(bind=engine)
        
        print("Database schema updated successfully!")
        print("The 'time_since_onset' field has been added to the Patient table.")
        
    except Exception as e:
        print(f"Error updating database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    update_database()
