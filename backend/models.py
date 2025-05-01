from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

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
    chief_complaint = Column(String)
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    glucose = Column(Float)
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

    patient = relationship("Patient", back_populates="scans")

