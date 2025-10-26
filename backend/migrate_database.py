#!/usr/bin/env python3
"""
Database migration script to add TreatmentPlan table
Run this script to update the database schema
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add TreatmentPlan table to the existing database"""
    
    # Database path
    db_path = "stroke.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Please ensure the database exists.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if TreatmentPlan table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='treatmentplans'
        """)
        
        if cursor.fetchone():
            print("TreatmentPlan table already exists. Migration not needed.")
            return True
        
        # Create TreatmentPlan table
        cursor.execute("""
            CREATE TABLE treatmentplans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                scan_id INTEGER NOT NULL,
                plan_type VARCHAR(50),
                ai_generated_plan TEXT,
                physician_notes TEXT,
                status VARCHAR(20) DEFAULT 'draft',
                created_by VARCHAR(100),
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (scan_id) REFERENCES strokescans (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_treatmentplans_patient_id ON treatmentplans (patient_id)")
        cursor.execute("CREATE INDEX idx_treatmentplans_scan_id ON treatmentplans (scan_id)")
        cursor.execute("CREATE INDEX idx_treatmentplans_status ON treatmentplans (status)")
        
        # Commit changes
        conn.commit()
        print("TreatmentPlan table created successfully!")
        print("Indexes created for better performance")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    db_path = "stroke.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(treatmentplans)")
        columns = cursor.fetchall()
        
        print("\nTreatmentPlan table structure:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # Check indexes
        cursor.execute("PRAGMA index_list(treatmentplans)")
        indexes = cursor.fetchall()
        
        print("\nIndexes created:")
        for index in indexes:
            print(f"  - {index[1]}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Verification error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    print("=" * 50)
    
    if migrate_database():
        print("\nVerifying migration...")
        verify_migration()
        print("\nMigration completed successfully!")
        print("\nNext steps:")
        print("1. Set your OpenAI API key in the .env file")
        print("2. Install new dependencies: pip install -r requirements.txt")
        print("3. Restart the FastAPI server")
    else:
        print("\nMigration failed!")
