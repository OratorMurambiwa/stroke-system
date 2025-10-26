# create_users.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, Patient

# Create database session
db = SessionLocal()

def get_or_create_user(username, password, role):
    user = db.query(User).filter_by(username=username).first()
    if user:
        print(f"User '{username}' already exists.")
        return user
    user = User(username=username, password=password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created user: {username} ({role})")
    return user

# Create users if not present
tech = get_or_create_user("tech1", "password123", "Technician")
doc = get_or_create_user("doc1", "password123", "Physician")
pat = get_or_create_user("pat1", "password123", "Patient")

# Create and link patient if it doesn't already exist
existing_patient = db.query(Patient).filter_by(code="P001").first()
if not existing_patient:
    patient = Patient(
        name="Test Patient",
        age=30,
        gender="Female",
        code="P001",
        linked_user_id=pat.id
    )
    db.add(patient)
    db.commit()
    print("Created patient 'Test Patient' linked to 'pat1'")
else:
    print("Patient with code 'P001' already exists.")

# Close session
db.close()
print("Done.")
