from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    time_since_onset = Column(String)
    chief_complaint = Column(String)
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    heart_rate = Column(Integer)
    oxygen_saturation = Column(Integer)
    temperature = Column(Float)
    glucose = Column(Float)
    platelet_count = Column(Integer)
    inr = Column(Float)
    code = Column(String, unique=True)
    linked_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    scans = relationship("StrokeScan", back_populates="patient")

class StrokeScan(Base):
    __tablename__ = "strokescans"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    image_path = Column(String)
    prediction = Column(String)
    timestamp = Column(DateTime)
    doctor_comment = Column(String)
    eligibility_result = Column(String)
    eligible = Column(Boolean)
    technician_notes = Column(String)
    status = Column(String, default="pending")  # pending, saved, ready_for_review, reviewed

    patient = relationship("Patient", back_populates="scans")

class NIHSSAssessment(Base):
    __tablename__ = "nihssassessments"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    consciousness = Column(Integer)
    gaze = Column(Integer)
    visual = Column(Integer)
    facial = Column(Integer)
    motor_arm_left = Column(Integer)
    motor_arm_right = Column(Integer)
    motor_leg_left = Column(Integer)
    motor_leg_right = Column(Integer)
    ataxia = Column(Integer)
    sensory = Column(Integer)
    language = Column(Integer)
    dysarthria = Column(Integer)
    extinction = Column(Integer)
    total_score = Column(Integer)
    timestamp = Column(DateTime)

    patient = relationship("Patient")

class TreatmentPlan(Base):
    __tablename__ = "treatmentplans"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    scan_id = Column(Integer, ForeignKey("strokescans.id"))
    plan_type = Column(String)  # "tpa_eligible", "not_eligible", "alternative"
    ai_generated_plan = Column(String)  # ChatGPT generated treatment plan
    physician_notes = Column(String)  # Physician's additional notes/modifications
    status = Column(String, default="draft")  # draft, approved, implemented
    created_by = Column(String)  # physician username
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    patient = relationship("Patient")
    scan = relationship("StrokeScan")

