#!/usr/bin/env python3
"""
Script to add sample data to the database for testing
"""
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Patient, User, StrokeScan

def add_sample_data():
    db = SessionLocal()
    try:
        print("Adding sample data to database...")
        
        # Add sample users
        users = [
            User(username="tech1", password="password123", role="Technician"),
            User(username="physician1", password="password123", role="Physician"),
            User(username="admin", password="admin123", role="Admin")
        ]
        
        for user in users:
            existing_user = db.query(User).filter(User.username == user.username).first()
            if not existing_user:
                db.add(user)
        
        db.commit()
        print("Sample users added")
        
        # Add sample patients
        patients = [
            Patient(
                name="John Smith",
                age=65,
                gender="Male",
                time_since_onset="2 hours",
                chief_complaint="Sudden weakness on left side",
                systolic_bp=140,
                diastolic_bp=90,
                glucose=120.5,
                inr=1.2,
                code="P001"
            ),
            Patient(
                name="Mary Johnson",
                age=72,
                gender="Female", 
                time_since_onset="1.5 hours",
                chief_complaint="Difficulty speaking and facial droop",
                systolic_bp=160,
                diastolic_bp=95,
                glucose=145.0,
                inr=1.1,
                code="P002"
            ),
            Patient(
                name="Robert Davis",
                age=58,
                gender="Male",
                time_since_onset="3 hours",
                chief_complaint="Severe headache and vision problems",
                systolic_bp=180,
                diastolic_bp=110,
                glucose=200.0,
                inr=2.5,
                code="P003"
            ),
            Patient(
                name="Sarah Wilson",
                age=45,
                gender="Female",
                time_since_onset="45 minutes",
                chief_complaint="Numbness in right arm and leg",
                systolic_bp=130,
                diastolic_bp=85,
                glucose=95.0,
                inr=1.0,
                code="P004"
            ),
            Patient(
                name="Michael Brown",
                age=67,
                gender="Male",
                time_since_onset="4 hours",
                chief_complaint="Confusion and balance problems",
                systolic_bp=150,
                diastolic_bp=88,
                glucose=110.0,
                inr=1.3,
                code="P005"
            )
        ]
        
        for patient in patients:
            existing_patient = db.query(Patient).filter(Patient.code == patient.code).first()
            if not existing_patient:
                db.add(patient)
        
        db.commit()
        print("Sample patients added")
        
        # Add sample scans
        patients_in_db = db.query(Patient).all()
        
        scans = [
            StrokeScan(
                patient_id=patients_in_db[0].id,
                image_path="uploads/sample_scan_1.jpg",
                prediction="Ischemic Stroke",
                timestamp=datetime.now(),
                doctor_comment="Clear signs of ischemic stroke in left hemisphere",
                eligibility_result="Eligible for tPA treatment",
                eligible=True
            ),
            StrokeScan(
                patient_id=patients_in_db[1].id,
                image_path="uploads/sample_scan_2.jpg", 
                prediction="Hemorrhagic Stroke",
                timestamp=datetime.now(),
                doctor_comment="Intracerebral hemorrhage detected",
                eligibility_result="Not eligible - hemorrhagic stroke",
                eligible=False
            ),
            StrokeScan(
                patient_id=patients_in_db[2].id,
                image_path="uploads/sample_scan_3.jpg",
                prediction="Ischemic Stroke",
                timestamp=datetime.now(),
                doctor_comment="Large vessel occlusion",
                eligibility_result="Eligible for tPA treatment",
                eligible=True
            ),
            StrokeScan(
                patient_id=patients_in_db[3].id,
                image_path="uploads/sample_scan_4.jpg",
                prediction="TIA (Transient Ischemic Attack)",
                timestamp=datetime.now(),
                doctor_comment="Minor ischemic changes",
                eligibility_result="Eligible for tPA treatment",
                eligible=True
            )
        ]
        
        for scan in scans:
            db.add(scan)
        
        db.commit()
        print("Sample scans added")
        
        # Print summary
        patient_count = db.query(Patient).count()
        scan_count = db.query(StrokeScan).count()
        user_count = db.query(User).count()
        
        print(f"\nDatabase Summary:")
        print(f"   Users: {user_count}")
        print(f"   Patients: {patient_count}")
        print(f"   Scans: {scan_count}")
        print(f"\nSample data added successfully!")
        print("The technician dashboard should now show data in the summary cards.")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    add_sample_data()
