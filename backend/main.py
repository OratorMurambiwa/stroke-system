from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil
from dotenv import load_dotenv
from tpa_eligibility import check_tpa_eligibility

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Continuing without .env file...")

# Import database and models
from database import Base, engine, get_db
import models  # this line ensures all models are registered
from auth import router as auth_router
from upload_router import router as upload_router

app = FastAPI()

# ✅ Create tables after models are imported
Base.metadata.create_all(bind=engine)

# Helper function to get current user from session (imported from auth module)
def get_current_user_from_session(request: Request):
    """Get current user from session cookie"""
    from auth import active_sessions
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        return active_sessions[session_id]
    return None

# Pydantic models for API
class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    time_since_onset: str
    consent_confirmed: bool
    code: str

class PatientResponse(BaseModel):
    patient_id: int
    patient_code: str
    message: str

class PatientVitalsUpdate(BaseModel):
    chief_complaint: str
    systolic_bp: int
    diastolic_bp: int
    heart_rate: int
    oxygen_saturation: int
    temperature: float
    glucose: float
    platelet_count: int
    inr: float

class NIHSSAssessment(BaseModel):
    consciousness: int
    gaze: int
    visual: int
    facial: int
    motorArmLeft: int
    motorArmRight: int
    motorLegLeft: int
    motorLegRight: int
    ataxia: int
    sensory: int
    language: int
    dysarthria: int
    extinction: int
    total_score: int

# ✅ Mount static and upload folders
app.mount("/static", StaticFiles(directory="../frontend"), name="static")
app.mount("/uploads", StaticFiles(directory="../uploads"), name="uploads")

# ✅ Include route handlers
app.include_router(auth_router)
app.include_router(upload_router)

# ---------- Frontend Page Routes ----------
@app.get("/")
def serve_home():
    return FileResponse(os.path.join("../frontend", "index.html"))

@app.get("/login-page")
def serve_login_page():
    return FileResponse(os.path.join("../frontend", "login.html"))

@app.get("/register-page")
def serve_register_page():
    return FileResponse(os.path.join("../frontend", "register.html"))

@app.get("/upload-form")
def serve_upload_form():
    return FileResponse(os.path.join("../frontend", "upload.html"))

@app.get("/patient-view")
def serve_patient_view():
    return FileResponse(os.path.join("../frontend", "patient_view.html"))

@app.get("/physician-dashboard")
def serve_physician_dashboard():
    return FileResponse(os.path.join("../frontend", "physician_dashboard.html"))

@app.get("/view-case")
def serve_view_case():
    return FileResponse(os.path.join("../frontend", "view_case.html"))

@app.get("/technician-dashboard")
def serve_technician_dashboard():
    return FileResponse(os.path.join("../frontend", "technician_dashboard.html"))

@app.get("/patient-details")
def serve_patient_details():
    return FileResponse(os.path.join("../frontend", "patient_details.html"))

@app.get("/add-patient")
def serve_add_patient():
    return FileResponse(os.path.join("../frontend", "add_patient.html"))

@app.get("/patient-vitals")
def serve_patient_vitals():
    return FileResponse(os.path.join("../frontend", "patient_vitals.html"))

@app.get("/nihss-assessment")
def serve_nihss_assessment():
    return FileResponse(os.path.join("../frontend", "nihss_assessment.html"))

@app.get("/patient-dashboard")
def serve_patient_dashboard():
    return FileResponse(os.path.join("../frontend", "patient_dashboard.html"))

# API endpoint to create a new patient
@app.post("/api/patients", response_model=PatientResponse)
def create_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
    try:
        # Validate consent
        if not patient_data.consent_confirmed:
            raise HTTPException(status_code=400, detail="Patient consent is required")
        
        # Check if patient code already exists
        existing_patient = db.query(models.Patient).filter(models.Patient.code == patient_data.code).first()
        if existing_patient:
            raise HTTPException(status_code=400, detail="Patient code already exists")
        
        # Create new patient
        new_patient = models.Patient(
            name=patient_data.name,
            age=patient_data.age,
            gender=patient_data.gender,
            time_since_onset=patient_data.time_since_onset,
            code=patient_data.code,
            chief_complaint="",  # Will be filled in vitals page
            systolic_bp=None,
            diastolic_bp=None,
            glucose=None,
            inr=None
        )
        
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        return PatientResponse(
            patient_id=new_patient.id,
            patient_code=new_patient.code,
            message="Patient created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")

# API endpoint to get patient by code
@app.get("/api/patients/{patient_code}")
def get_patient_by_code(patient_code: str, db: Session = Depends(get_db)):
    try:
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "id": patient.id,
            "code": patient.code,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "time_since_onset": patient.time_since_onset,
            "chief_complaint": patient.chief_complaint,
            "systolic_bp": patient.systolic_bp,
            "diastolic_bp": patient.diastolic_bp,
            "heart_rate": patient.heart_rate,
            "oxygen_saturation": patient.oxygen_saturation,
            "temperature": patient.temperature,
            "glucose": patient.glucose,
            "platelet_count": patient.platelet_count,
            "inr": patient.inr
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

# API endpoint to get patient data by logged-in user
@app.get("/api/patients/by-user")
def get_patient_by_user(request: Request, db: Session = Depends(get_db)):
    try:
        # Get current user from session
        user_info = get_current_user_from_session(request)
        if not user_info:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get patient by linked user ID
        patient = db.query(models.Patient).filter(models.Patient.linked_user_id == user_info['user_id']).first()
        if not patient:
            raise HTTPException(status_code=404, detail="No patient record linked to this user")
        
        return {
            "id": patient.id,
            "code": patient.code,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "time_since_onset": patient.time_since_onset,
            "chief_complaint": patient.chief_complaint,
            "systolic_bp": patient.systolic_bp,
            "diastolic_bp": patient.diastolic_bp,
            "heart_rate": patient.heart_rate,
            "oxygen_saturation": patient.oxygen_saturation,
            "temperature": patient.temperature,
            "glucose": patient.glucose,
            "platelet_count": patient.platelet_count,
            "inr": patient.inr
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

# API endpoint to update patient vitals
@app.put("/api/patients/{patient_code}/vitals")
def update_patient_vitals(patient_code: str, vitals_data: PatientVitalsUpdate, db: Session = Depends(get_db)):
    try:
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Update patient vitals
        patient.chief_complaint = vitals_data.chief_complaint
        patient.systolic_bp = vitals_data.systolic_bp
        patient.diastolic_bp = vitals_data.diastolic_bp
        patient.heart_rate = vitals_data.heart_rate
        patient.oxygen_saturation = vitals_data.oxygen_saturation
        patient.temperature = vitals_data.temperature
        patient.glucose = vitals_data.glucose
        patient.platelet_count = vitals_data.platelet_count
        patient.inr = vitals_data.inr
        
        db.commit()
        db.refresh(patient)
        
        return {
            "message": "Patient vitals updated successfully",
            "patient_code": patient.code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update patient vitals: {str(e)}")

# API endpoint to save NIHSS assessment
@app.post("/api/patients/{patient_code}/nihss")
def save_nihss_assessment(patient_code: str, nihss_data: NIHSSAssessment, db: Session = Depends(get_db)):
    try:
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create new NIHSS assessment
        nihss_assessment = models.NIHSSAssessment(
            patient_id=patient.id,
            consciousness=nihss_data.consciousness,
            gaze=nihss_data.gaze,
            visual=nihss_data.visual,
            facial=nihss_data.facial,
            motor_arm_left=nihss_data.motorArmLeft,
            motor_arm_right=nihss_data.motorArmRight,
            motor_leg_left=nihss_data.motorLegLeft,
            motor_leg_right=nihss_data.motorLegRight,
            ataxia=nihss_data.ataxia,
            sensory=nihss_data.sensory,
            language=nihss_data.language,
            dysarthria=nihss_data.dysarthria,
            extinction=nihss_data.extinction,
            total_score=nihss_data.total_score,
            timestamp=datetime.now()
        )
        
        db.add(nihss_assessment)
        db.commit()
        db.refresh(nihss_assessment)
        
        return {
            "message": "NIHSS assessment saved successfully",
            "patient_code": patient.code,
            "nihss_id": nihss_assessment.id,
            "total_score": nihss_assessment.total_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save NIHSS assessment: {str(e)}")

# API endpoint to get NIHSS assessment for a patient
@app.get("/api/patients/{patient_code}/nihss")
def get_nihss_assessment(patient_code: str, db: Session = Depends(get_db)):
    try:
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        nihss_assessment = db.query(models.NIHSSAssessment).filter(
            models.NIHSSAssessment.patient_id == patient.id
        ).order_by(models.NIHSSAssessment.timestamp.desc()).first()
        
        if not nihss_assessment:
            raise HTTPException(status_code=404, detail="NIHSS assessment not found")
        
        return {
            "id": nihss_assessment.id,
            "patient_code": patient_code,
            "consciousness": nihss_assessment.consciousness,
            "gaze": nihss_assessment.gaze,
            "visual": nihss_assessment.visual,
            "facial": nihss_assessment.facial,
            "motor_arm_left": nihss_assessment.motor_arm_left,
            "motor_arm_right": nihss_assessment.motor_arm_right,
            "motor_leg_left": nihss_assessment.motor_leg_left,
            "motor_leg_right": nihss_assessment.motor_leg_right,
            "ataxia": nihss_assessment.ataxia,
            "sensory": nihss_assessment.sensory,
            "language": nihss_assessment.language,
            "dysarthria": nihss_assessment.dysarthria,
            "extinction": nihss_assessment.extinction,
            "total_score": nihss_assessment.total_score,
            "timestamp": nihss_assessment.timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get NIHSS assessment: {str(e)}")

# API endpoint to upload scan and run tPA eligibility check
@app.post("/api/upload-scan")
async def upload_scan_and_check_eligibility(
    patient_code: str = Form(...),
    scan_type: str = Form(...),
    imaging_confirmed: str = Form(...),
    scan_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Get patient data
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get NIHSS assessment
        nihss_assessment = db.query(models.NIHSSAssessment).filter(
            models.NIHSSAssessment.patient_id == patient.id
        ).order_by(models.NIHSSAssessment.timestamp.desc()).first()
        
        if not nihss_assessment:
            raise HTTPException(status_code=400, detail="NIHSS assessment not found for patient")
        
        # Save uploaded file
        upload_dir = "../uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().timestamp()
        filename = f"{timestamp}_{patient_code}_{scan_file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(scan_file.file, buffer)
        
        # Prepare data for tPA eligibility check
        # Convert time since onset to hours (simplified - you might want to parse this better)
        time_since_onset_hours = 2.0  # Default value, you might want to parse from patient.time_since_onset
        
        eligibility_data = {
            "age": patient.age,
            "hours_since_onset": time_since_onset_hours,
            "imaging_confirmed": imaging_confirmed,
            "consent": "yes",  # Assuming consent was given in the workflow
            "nhiss_score": nihss_assessment.total_score,
            "inr": patient.inr or 1.0,
            "heart_rate": patient.heart_rate or 80,
            "respiratory_rate": 16,  # Default value
            "temperature": patient.temperature or 98.6,
            "oxygen_saturation": patient.oxygen_saturation or 98,
            "recent_trauma": "no",  # Default values - you might want to add these fields
            "recent_stroke_or_injury": "no",
            "intracranial_issue": "no",
            "recent_mi": "no",
            "systolic_bp": patient.systolic_bp or 120,
            "diastolic_bp": patient.diastolic_bp or 80,
            "glucose": patient.glucose or 100,
            "anticoagulant_risk": "no",
            "platelet_count": patient.platelet_count or 250,
            "recent_surgery": "no"
        }
        
        # Run tPA eligibility check
        is_eligible, reason = check_tpa_eligibility(eligibility_data)
        
        # Create stroke scan record
        stroke_scan = models.StrokeScan(
            patient_id=patient.id,
            image_path=file_path,
            prediction="Ischemic Stroke" if imaging_confirmed == "yes" else "Not Confirmed",
            timestamp=datetime.now(),
            doctor_comment=f"Scan type: {scan_type}, Imaging confirmed: {imaging_confirmed}",
            eligibility_result=reason,
            eligible=is_eligible
        )
        
        db.add(stroke_scan)
        db.commit()
        db.refresh(stroke_scan)
        
        return {
            "eligible": is_eligible,
            "reason": reason,
            "scan_id": stroke_scan.id,
            "patient_code": patient.code,
            "message": "Scan uploaded and tPA eligibility assessed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process scan: {str(e)}")

# API endpoint to save patient record with technician notes
@app.post("/api/patients/save-record")
async def save_patient_record(
    request: dict,
    db: Session = Depends(get_db)
):
    try:
        patient_code = request.get("patient_code")
        technician_notes = request.get("technician_notes", "")
        status = request.get("status", "saved")
        
        if not patient_code:
            raise HTTPException(status_code=400, detail="Patient code is required")
        
        # Get patient
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get the most recent scan for this patient
        latest_scan = db.query(models.StrokeScan).filter(
            models.StrokeScan.patient_id == patient.id
        ).order_by(models.StrokeScan.timestamp.desc()).first()
        
        if latest_scan:
            # Update the scan with technician notes and status
            latest_scan.technician_notes = technician_notes
            latest_scan.status = status
            db.commit()
            
            return {
                "message": "Record saved successfully",
                "patient_code": patient_code,
                "scan_id": latest_scan.id,
                "status": status
            }
        else:
            raise HTTPException(status_code=404, detail="No scan found for patient")
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save record: {str(e)}")

# API endpoint to send case to doctor for review
@app.post("/api/patients/send-to-doctor")
async def send_to_doctor(
    request: dict,
    db: Session = Depends(get_db)
):
    try:
        patient_code = request.get("patient_code")
        technician_notes = request.get("technician_notes", "")
        
        if not patient_code:
            raise HTTPException(status_code=400, detail="Patient code is required")
        
        # Get patient
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get the most recent scan for this patient
        latest_scan = db.query(models.StrokeScan).filter(
            models.StrokeScan.patient_id == patient.id
        ).order_by(models.StrokeScan.timestamp.desc()).first()
        
        if latest_scan:
            # Update the scan with technician notes and mark as ready for review
            latest_scan.technician_notes = technician_notes
            latest_scan.status = "ready_for_review"
            db.commit()
            
            return {
                "message": "Case sent to doctor successfully",
                "patient_code": patient_code,
                "scan_id": latest_scan.id,
                "status": "ready_for_review"
            }
        else:
            raise HTTPException(status_code=404, detail="No scan found for patient")
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send to doctor: {str(e)}")

# API endpoint to get patient vitals
@app.get("/api/patients/{patient_code}/vitals")
def get_patient_vitals(patient_code: str, db: Session = Depends(get_db)):
    try:
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "patient_code": patient.code,
            "systolic_bp": patient.systolic_bp,
            "diastolic_bp": patient.diastolic_bp,
            "heart_rate": patient.heart_rate,
            "oxygen_saturation": patient.oxygen_saturation,
            "temperature": patient.temperature,
            "glucose": patient.glucose,
            "inr": patient.inr,
            "platelet_count": patient.platelet_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient vitals: {str(e)}")

# API endpoint to get patient scans
@app.get("/api/patients/{patient_code}/scans")
def get_patient_scans(patient_code: str, db: Session = Depends(get_db)):
    try:
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        scans = db.query(models.StrokeScan).filter(
            models.StrokeScan.patient_id == patient.id
        ).order_by(models.StrokeScan.timestamp.desc()).all()
        
        scan_data = []
        for scan in scans:
            scan_data.append({
                "id": scan.id,
                "image_path": scan.image_path,
                "prediction": scan.prediction,
                "timestamp": scan.timestamp,
                "doctor_comment": scan.doctor_comment,
                "eligibility_result": scan.eligibility_result,
                "eligible": scan.eligible,
                "technician_notes": scan.technician_notes,
                "status": scan.status
            })
        
        return scan_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient scans: {str(e)}")

# API endpoint to get patient treatment plans
@app.get("/api/patients/{patient_code}/treatment-plans")
def get_patient_treatment_plans(patient_code: str, db: Session = Depends(get_db)):
    try:
        patient = db.query(models.Patient).filter(models.Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        treatment_plans = db.query(models.TreatmentPlan).filter(
            models.TreatmentPlan.patient_id == patient.id
        ).order_by(models.TreatmentPlan.created_at.desc()).all()
        
        plan_data = []
        for plan in treatment_plans:
            plan_data.append({
                "id": plan.id,
                "patient_id": plan.patient_id,
                "scan_id": plan.scan_id,
                "plan_type": plan.plan_type,
                "ai_generated_plan": plan.ai_generated_plan,
                "physician_notes": plan.physician_notes,
                "status": plan.status,
                "created_by": plan.created_by,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at
            })
        
        return plan_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get treatment plans: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)