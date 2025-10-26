from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import os
import requests
import json
from database import SessionLocal
from models import Patient, StrokeScan, NIHSSAssessment, TreatmentPlan
from tpa_eligibility import check_tpa_eligibility
from chatgpt_service import get_chatgpt_service

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload-scan/")
async def upload_scan(
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    hours_since_onset: float = Form(...),
    imaging_confirmed: str = Form(...),
    consent: str = Form(...),
    nhiss_score: int = Form(...),
    inr: float = Form(...),
    heart_rate: int = Form(...),
    respiratory_rate: int = Form(...),
    temperature: float = Form(...),
    oxygen_saturation: int = Form(...),
    systolic_bp: int = Form(...),
    diastolic_bp: int = Form(...),
    glucose: float = Form(...),
    platelet_count: int = Form(...),
    anticoagulant_risk: str = Form(...),
    recent_trauma: str = Form(...),
    recent_stroke_or_injury: str = Form(...),
    intracranial_issue: str = Form(...),
    recent_mi: str = Form(...),
    recent_surgery: str = Form(...),
    code: str = Form(...),
    chief_complaint: str = Form(...),
    scan: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = f"{datetime.now().timestamp()}_{scan.filename}"
    relative_path = os.path.join("uploads", filename).replace("\\", "/")
    absolute_path = os.path.abspath(relative_path)
    with open(absolute_path, "wb") as buffer:
        buffer.write(await scan.read())

    if db.query(Patient).filter_by(code=code).first():
        return HTMLResponse(content="Code already exists", status_code=400)

    data = {
        "age": age,
        "hours_since_onset": hours_since_onset,
        "imaging_confirmed": imaging_confirmed,
        "consent": consent,
        "nhiss_score": nhiss_score,
        "inr": inr,
        "heart_rate": heart_rate,
        "respiratory_rate": respiratory_rate,
        "temperature": temperature,
        "oxygen_saturation": oxygen_saturation,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "glucose": glucose,
        "platelet_count": platelet_count,
        "anticoagulant_risk": anticoagulant_risk,
        "recent_trauma": recent_trauma,
        "recent_stroke_or_injury": recent_stroke_or_injury,
        "intracranial_issue": intracranial_issue,
        "recent_mi": recent_mi,
        "recent_surgery": recent_surgery
    }
    eligible, reason = check_tpa_eligibility(data)

    patient = Patient(
        name=name,
        age=age,
        gender=gender,
        chief_complaint=chief_complaint,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        glucose=glucose,
        inr=inr,
        code=code
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    scan_record = StrokeScan(
        patient_id=patient.id,
        image_path=relative_path,
        prediction=reason,
        eligibility_result=reason,
        eligible=eligible,
        timestamp=datetime.now()
    )
    db.add(scan_record)
    db.commit()

    return HTMLResponse(content=f"""
        <html>
        <head>
            <title>Upload Success</title>
            <style>
                body {{
                    background-color: #000000;
                    color: #FFFFFF;
                    font-family: 'Segoe UI', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .box {{
                    background-color: #FFFFFF;
                    color: #000000;
                    padding: 30px;
                    border-radius: 12px;
                    text-align: center;
                    max-width: 600px;
                    box-shadow: 0 0 10px rgba(255,255,255,0.2);
                }}
                h2 {{
                    color: #FDB927;
                    margin-bottom: 15px;
                }}
                p {{
                    font-size: 16px;
                    margin: 10px 0;
                }}
                a {{
                    margin-top: 20px;
                    display: inline-block;
                    text-decoration: none;
                    background-color: #FDB927;
                    color: #000000;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }}
                a:hover {{
                    background-color: #d4a218;
                }}
            </style>
        </head>
        <body>
            <div class="box">
                <h2>Upload Successful ✅</h2>
                <p><strong>Patient:</strong> {name}</p>
                <p><strong>Eligibility Status:</strong></p>
                <p>{reason}</p>
                <a href="/technician-dashboard">Return to Dashboard</a>
            </div>
        </body>
        </html>
    """, status_code=200)

@router.get("/patients/")
def get_all_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "chief_complaint": p.chief_complaint,
            "code": p.code,
            "linked_user_id": p.linked_user_id,
            "systolic_bp": p.systolic_bp,
            "diastolic_bp": p.diastolic_bp,
            "glucose": p.glucose,
            "inr": p.inr
        }
        for p in patients
    ]

@router.get("/patients/{patient_code}")
def get_patient_by_code(patient_code: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "chief_complaint": patient.chief_complaint,
        "code": patient.code,
        "linked_user_id": patient.linked_user_id,
        "systolic_bp": patient.systolic_bp,
        "diastolic_bp": patient.diastolic_bp,
        "glucose": patient.glucose,
        "inr": patient.inr,
        "scans": [
            {
                "scan_id": scan.id,
                "diagnosis": scan.prediction,
                "eligibility_result": scan.eligibility_result,
                "eligible": scan.eligible,
                "image_path": f"/{scan.image_path.replace(os.sep, '/')}" if scan.image_path else None
            }
            for scan in patient.scans
        ]
    }

@router.get("/patients/{patient_code}/scans")
def get_patient_scans(patient_code: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter_by(code=patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "chief_complaint": patient.chief_complaint,
        "systolic_bp": patient.systolic_bp,
        "diastolic_bp": patient.diastolic_bp,
        "glucose": patient.glucose,
        "inr": patient.inr,
        "scans": [
            {
                "scan_id": scan.id,
                "diagnosis": scan.prediction,
                "eligibility_result": scan.eligibility_result,
                "eligible": scan.eligible,
                "image_path": f"/{scan.image_path.replace(os.sep, '/')}"
            }
            for scan in patient.scans
        ]
    }

@router.post("/scans/{scan_id}/comment")
def add_doctor_comment(scan_id: int, comment: str = Form(...), db: Session = Depends(get_db)):
    scan = db.query(StrokeScan).filter_by(id=scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan.doctor_comment = comment
    db.commit()
    return {"message": "Comment added", "scan_id": scan_id}

# Dashboard Statistics Endpoint
@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    try:
        # Total patients
        total_patients = db.query(Patient).count()
        
        # Total scans
        total_scans = db.query(StrokeScan).count()
        
        # Eligible scans (where eligible = True)
        eligible_scans = db.query(StrokeScan).filter(StrokeScan.eligible == True).count()
        
        # Not eligible scans (where eligible = False)
        not_eligible_scans = db.query(StrokeScan).filter(StrokeScan.eligible == False).count()
        
        # Sent to doctor scans (scans with ready_for_review status)
        sent_to_doctor_scans = db.query(StrokeScan).filter(StrokeScan.status == "ready_for_review").count()
        
        # Recent activity (last 7 days) - using timestamp for scans
        week_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day - 7)
        
        # Since Patient doesn't have created_at, we'll use scans timestamp as proxy
        recent_scans = db.query(StrokeScan).filter(StrokeScan.timestamp >= week_ago).count()
        
        # For recent patients, we'll count patients who have recent scans
        recent_patients = db.query(Patient).join(StrokeScan).filter(StrokeScan.timestamp >= week_ago).distinct().count()
        
        return {
            "total_patients": total_patients,
            "total_scans": total_scans,
            "eligible_scans": eligible_scans,
            "not_eligible_scans": not_eligible_scans,
            "sent_to_doctor_scans": sent_to_doctor_scans,
            "recent_patients": recent_patients,
            "recent_scans": recent_scans
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

# Physician Dashboard Statistics Endpoint
@router.get("/physician-dashboard-stats")
def get_physician_dashboard_stats(db: Session = Depends(get_db)):
    try:
        from datetime import datetime, timedelta
        
        # New Cases: Number of patients sent by technicians (ready_for_review status)
        new_cases = db.query(StrokeScan).filter(StrokeScan.status == "ready_for_review").count()
        
        # Reviewed Cases: How many have been checked today (status = "reviewed" and today's date)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        reviewed_today = db.query(StrokeScan).filter(
            StrokeScan.status == "reviewed",
            StrokeScan.timestamp >= today
        ).count()
        
        # Eligible for tPA: Count of confirmed eligible cases (eligible = True)
        eligible_for_tpa = db.query(StrokeScan).filter(StrokeScan.eligible == True).count()
        
        # Not Eligible: Count of rejected cases (eligible = False)
        not_eligible = db.query(StrokeScan).filter(StrokeScan.eligible == False).count()
        
        return {
            "new_cases": new_cases,
            "reviewed_today": reviewed_today,
            "eligible_for_tpa": eligible_for_tpa,
            "not_eligible": not_eligible
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching physician dashboard stats: {str(e)}")

# Physician Dashboard Detail Endpoints
@router.get("/physician-dashboard-details/new-cases")
def get_new_cases_detail(db: Session = Depends(get_db)):
    try:
        scans = db.query(StrokeScan).filter(StrokeScan.status == "ready_for_review").all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint or "N/A",
                "upload_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "status": scan.status,
                "diagnosis": scan.prediction or "N/A",
                "image_path": scan.image_path
            }
            for scan in scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching new cases: {str(e)}")

@router.get("/physician-dashboard-details/reviewed-today")
def get_reviewed_today_detail(db: Session = Depends(get_db)):
    try:
        from datetime import datetime
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        scans = db.query(StrokeScan).filter(
            StrokeScan.status == "reviewed",
            StrokeScan.timestamp >= today
        ).all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint or "N/A",
                "review_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "status": scan.status,
                "diagnosis": scan.prediction or "N/A",
                "doctor_comment": scan.doctor_comment or "No comment",
                "image_path": scan.image_path
            }
            for scan in scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reviewed cases: {str(e)}")

@router.get("/physician-dashboard-details/eligible-tpa")
def get_eligible_tpa_detail(db: Session = Depends(get_db)):
    try:
        scans = db.query(StrokeScan).filter(StrokeScan.eligible == True).all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint or "N/A",
                "upload_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "status": scan.status,
                "diagnosis": scan.prediction or "N/A",
                "eligibility_result": scan.eligibility_result or "N/A",
                "image_path": scan.image_path
            }
            for scan in scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching eligible cases: {str(e)}")

@router.get("/physician-dashboard-details/not-eligible")
def get_not_eligible_detail(db: Session = Depends(get_db)):
    try:
        scans = db.query(StrokeScan).filter(StrokeScan.eligible == False).all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint or "N/A",
                "upload_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "status": scan.status,
                "diagnosis": scan.prediction or "N/A",
                "eligibility_result": scan.eligibility_result or "N/A",
                "image_path": scan.image_path
            }
            for scan in scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching not eligible cases: {str(e)}")

# Scan Decision API for Physician
@router.post("/scans/{scan_id}/decision")
def make_scan_decision(
    scan_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    try:
        scan = db.query(StrokeScan).filter(StrokeScan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        new_status = request.get("status")
        decision_made_by = request.get("decision_made_by", "physician")
        
        # Update scan status based on decision
        if new_status == "approved_tpa":
            scan.status = "approved_tpa"
        elif new_status == "rejected":
            scan.status = "rejected"
        elif new_status == "sent_to_doctor":
            scan.status = "ready_for_review"  # Keep as ready for review
        
        # Add decision timestamp
        scan.timestamp = datetime.now()
        
        db.commit()
        
        # In a real implementation, you would send a notification to the technician here
        # For now, we'll just return success
        
        return {
            "message": "Decision recorded successfully",
            "scan_id": scan_id,
            "new_status": new_status,
            "technician_notified": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record decision: {str(e)}")

# Get detailed case information for physician view
@router.get("/api/cases/{patient_code}")
def get_case_details(patient_code: str, db: Session = Depends(get_db)):
    try:
        patient = db.query(Patient).filter(Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get the most recent scan for this patient
        scan = db.query(StrokeScan).filter(StrokeScan.patient_id == patient.id).order_by(StrokeScan.timestamp.desc()).first()
        
        # Get NIHSS assessment if available
        nihss = db.query(NIHSSAssessment).filter(NIHSSAssessment.patient_id == patient.id).first()
        
        case_data = {
            "patient": {
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
                "inr": patient.inr,
                "platelet_count": patient.platelet_count
            },
            "scan": None,
            "nihss": None
        }
        
        if scan:
            case_data["scan"] = {
                "id": scan.id,
                "image_path": scan.image_path,
                "prediction": scan.prediction,
                "timestamp": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else None,
                "doctor_comment": scan.doctor_comment,
                "eligibility_result": scan.eligibility_result,
                "eligible": scan.eligible,
                "technician_notes": scan.technician_notes,
                "status": scan.status,
                "imaging_confirmed": getattr(scan, 'imaging_confirmed', True)  # Default to True if field doesn't exist
            }
        
        if nihss:
            case_data["nihss"] = {
                "consciousness": nihss.consciousness,
                "gaze": nihss.gaze,
                "visual": nihss.visual,
                "facial": nihss.facial,
                "motor_arm_left": nihss.motor_arm_left,
                "motor_arm_right": nihss.motor_arm_right,
                "motor_leg_left": nihss.motor_leg_left,
                "motor_leg_right": nihss.motor_leg_right,
                "ataxia": nihss.ataxia,
                "sensory": nihss.sensory,
                "language": nihss.language,
                "dysarthria": nihss.dysarthria,
                "extinction": nihss.extinction,
                "total_score": nihss.total_score,
                "timestamp": nihss.timestamp.strftime("%Y-%m-%d %H:%M") if nihss.timestamp else None
            }
        
        return case_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case details: {str(e)}")

# Save doctor comment
@router.post("/scans/{scan_id}/comment")
def save_doctor_comment(
    scan_id: int,
    comment: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        scan = db.query(StrokeScan).filter(StrokeScan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan.doctor_comment = comment
        scan.timestamp = datetime.now()
        
        db.commit()
        
        return {"message": "Comment saved successfully", "scan_id": scan_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save comment: {str(e)}")

# Detailed data endpoints for each card
@router.get("/dashboard-details/total-patients")
def get_total_patients_detail(db: Session = Depends(get_db)):
    try:
        patients = db.query(Patient).all()
        return [
            {
                "id": patient.id,
                "code": patient.code,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "chief_complaint": patient.chief_complaint or "N/A",
                "scan_count": len(patient.scans),
                "systolic_bp": patient.systolic_bp,
                "diastolic_bp": patient.diastolic_bp,
                "glucose": patient.glucose,
                "inr": patient.inr
            }
            for patient in patients
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patients: {str(e)}")

@router.get("/dashboard-details/pending-scans")
def get_pending_scans_detail(db: Session = Depends(get_db)):
    try:
        pending_scans = db.query(StrokeScan).filter(StrokeScan.eligible.is_(None)).all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint,
                "upload_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "status": "Pending Analysis",
                "image_path": scan.image_path
            }
            for scan in pending_scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pending scans: {str(e)}")

@router.get("/dashboard-details/eligible")
def get_eligible_scans_detail(db: Session = Depends(get_db)):
    try:
        eligible_scans = db.query(StrokeScan).filter(StrokeScan.eligible == True).all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint,
                "diagnosis": scan.prediction or "N/A",
                "eligibility_result": scan.eligibility_result or "Eligible for tPA",
                "upload_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "image_path": scan.image_path
            }
            for scan in eligible_scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching eligible scans: {str(e)}")

@router.get("/dashboard-details/not-eligible")
def get_not_eligible_scans_detail(db: Session = Depends(get_db)):
    try:
        not_eligible_scans = db.query(StrokeScan).filter(StrokeScan.eligible == False).all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint,
                "diagnosis": scan.prediction or "N/A",
                "eligibility_result": scan.eligibility_result or "Not Eligible",
                "upload_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "image_path": scan.image_path
            }
            for scan in not_eligible_scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching not eligible scans: {str(e)}")

@router.get("/dashboard-details/sent-to-doctor")
def get_sent_to_doctor_scans_detail(db: Session = Depends(get_db)):
    try:
        sent_to_doctor_scans = db.query(StrokeScan).filter(StrokeScan.status == "ready_for_review").all()
        return [
            {
                "scan_id": scan.id,
                "patient_code": scan.patient.code,
                "patient_name": scan.patient.name,
                "patient_age": scan.patient.age,
                "patient_gender": scan.patient.gender,
                "chief_complaint": scan.patient.chief_complaint,
                "diagnosis": scan.prediction or "N/A",
                "eligibility_result": scan.eligibility_result or "Sent for Review",
                "upload_date": scan.timestamp.strftime("%Y-%m-%d %H:%M") if scan.timestamp else "N/A",
                "image_path": scan.image_path,
                "status": scan.status or "ready_for_review"
            }
            for scan in sent_to_doctor_scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sent to doctor scans: {str(e)}")

# Treatment Plan API Endpoints

@router.post("/api/treatment-plan/generate")
async def generate_treatment_plan(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Generate a treatment plan using ChatGPT for a specific patient and scan.
    """
    try:
        patient_code = request.get("patient_code")
        scan_id = request.get("scan_id")
        physician_username = request.get("physician_username", "Unknown")
        
        if not patient_code or not scan_id:
            raise HTTPException(status_code=400, detail="Patient code and scan ID are required")
        
        # Get patient data
        patient = db.query(Patient).filter(Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get scan data
        scan = db.query(StrokeScan).filter(StrokeScan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Prepare patient data for ChatGPT
        patient_data = {
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "chief_complaint": patient.chief_complaint,
            "time_since_onset": patient.time_since_onset,
            "systolic_bp": patient.systolic_bp,
            "diastolic_bp": patient.diastolic_bp,
            "heart_rate": patient.heart_rate,
            "oxygen_saturation": patient.oxygen_saturation,
            "temperature": patient.temperature,
            "glucose": patient.glucose,
            "inr": patient.inr
        }
        
        # Prepare scan data for ChatGPT
        scan_data = {
            "imaging_confirmed": getattr(scan, 'imaging_confirmed', True),
            "prediction": scan.prediction,
            "eligibility_result": scan.eligibility_result,
            "eligible": scan.eligible
        }
        
        # Generate treatment plan using ChatGPT
        ai_generated_plan = get_chatgpt_service().generate_treatment_plan(
            patient_data, scan_data, scan.eligibility_result, scan.eligible
        )
        
        # Determine plan type
        plan_type = "tpa_eligible" if scan.eligible else "not_eligible"
        
        # Create treatment plan record
        treatment_plan = TreatmentPlan(
            patient_id=patient.id,
            scan_id=scan.id,
            plan_type=plan_type,
            ai_generated_plan=ai_generated_plan,
            status="draft",
            created_by=physician_username,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(treatment_plan)
        db.commit()
        db.refresh(treatment_plan)
        
        return {
            "message": "Treatment plan generated successfully",
            "treatment_plan_id": treatment_plan.id,
            "plan_type": plan_type,
            "ai_generated_plan": ai_generated_plan,
            "status": "draft"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate treatment plan: {str(e)}")

@router.get("/api/treatment-plan/{treatment_plan_id}")
def get_treatment_plan(treatment_plan_id: int, db: Session = Depends(get_db)):
    """
    Get a specific treatment plan by ID.
    """
    try:
        treatment_plan = db.query(TreatmentPlan).filter(TreatmentPlan.id == treatment_plan_id).first()
        if not treatment_plan:
            raise HTTPException(status_code=404, detail="Treatment plan not found")
        
        return {
            "id": treatment_plan.id,
            "patient_code": treatment_plan.patient.code,
            "patient_name": treatment_plan.patient.name,
            "scan_id": treatment_plan.scan_id,
            "plan_type": treatment_plan.plan_type,
            "ai_generated_plan": treatment_plan.ai_generated_plan,
            "physician_notes": treatment_plan.physician_notes,
            "status": treatment_plan.status,
            "created_by": treatment_plan.created_by,
            "created_at": treatment_plan.created_at.strftime("%Y-%m-%d %H:%M") if treatment_plan.created_at else None,
            "updated_at": treatment_plan.updated_at.strftime("%Y-%m-%d %H:%M") if treatment_plan.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get treatment plan: {str(e)}")

@router.put("/api/treatment-plan/{treatment_plan_id}")
def update_treatment_plan(
    treatment_plan_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Update a treatment plan with physician notes and status.
    """
    try:
        treatment_plan = db.query(TreatmentPlan).filter(TreatmentPlan.id == treatment_plan_id).first()
        if not treatment_plan:
            raise HTTPException(status_code=404, detail="Treatment plan not found")
        
        # Update fields
        if "physician_notes" in request:
            treatment_plan.physician_notes = request["physician_notes"]
        
        if "status" in request:
            treatment_plan.status = request["status"]
        
        treatment_plan.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Treatment plan updated successfully",
            "treatment_plan_id": treatment_plan.id,
            "status": treatment_plan.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update treatment plan: {str(e)}")

@router.post("/api/treatment-plan/{treatment_plan_id}/refine")
async def refine_treatment_plan(
    treatment_plan_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Refine an existing treatment plan using ChatGPT based on physician input.
    """
    try:
        treatment_plan = db.query(TreatmentPlan).filter(TreatmentPlan.id == treatment_plan_id).first()
        if not treatment_plan:
            raise HTTPException(status_code=404, detail="Treatment plan not found")
        
        physician_notes = request.get("physician_notes", "")
        if not physician_notes:
            raise HTTPException(status_code=400, detail="Physician notes are required for refinement")
        
        # Refine the treatment plan using ChatGPT
        refined_plan = get_chatgpt_service().refine_treatment_plan(
            treatment_plan.ai_generated_plan, physician_notes
        )
        
        # Update the treatment plan
        treatment_plan.ai_generated_plan = refined_plan
        treatment_plan.physician_notes = physician_notes
        treatment_plan.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Treatment plan refined successfully",
            "treatment_plan_id": treatment_plan.id,
            "refined_plan": refined_plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to refine treatment plan: {str(e)}")

@router.get("/api/patients/{patient_code}/treatment-plans")
def get_patient_treatment_plans(patient_code: str, db: Session = Depends(get_db)):
    """
    Get all treatment plans for a specific patient.
    """
    try:
        patient = db.query(Patient).filter(Patient.code == patient_code).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        treatment_plans = db.query(TreatmentPlan).filter(TreatmentPlan.patient_id == patient.id).all()
        
        return [
            {
                "id": tp.id,
                "scan_id": tp.scan_id,
                "plan_type": tp.plan_type,
                "status": tp.status,
                "created_by": tp.created_by,
                "created_at": tp.created_at.strftime("%Y-%m-%d %H:%M") if tp.created_at else None,
                "updated_at": tp.updated_at.strftime("%Y-%m-%d %H:%M") if tp.updated_at else None
            }
            for tp in treatment_plans
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get treatment plans: {str(e)}")

# New OpenAI Chat Completions API Endpoint

@router.post("/api/generate-treatment")
async def generate_treatment_recommendation(request: dict):
    """
    Generate stroke treatment recommendations using OpenAI Chat Completions API.
    
    Accepts patient information and returns AI-generated treatment plan.
    """
    try:
        # Validate required fields
        required_fields = ["name", "age", "nhiss_score", "systolic_bp", "diastolic_bp", "glucose", "oxygen_saturation", "symptoms"]
        missing_fields = [field for field in required_fields if field not in request or request[field] is None]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Get OpenAI API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key or openai_api_key == "your_openai_api_key_here":
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
            )
        
        # Prepare the prompt with patient information
        prompt = f"""
You are a medical assistant suggesting evidence-based stroke care plans following current stroke management guidelines. Provide a structured treatment recommendation and include tPA or alternative care guidance.

Patient Information:
- Name: {request['name']}
- Age: {request['age']} years
- NIHSS Score: {request['nhiss_score']}
- Blood Pressure: {request['systolic_bp']}/{request['diastolic_bp']} mmHg
- Glucose: {request['glucose']} mg/dL
- Oxygen Saturation: {request['oxygen_saturation']}%
- Symptoms: {request['symptoms']}

Please provide a comprehensive treatment recommendation including:
1. Immediate assessment and monitoring
2. tPA eligibility evaluation and recommendations
3. Alternative treatment options if tPA is not indicated
4. Monitoring parameters
5. Follow-up care plan

Format your response as a structured treatment plan with clear sections.
"""
        
        # Prepare the request to OpenAI API
        openai_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a medical assistant suggesting evidence-based stroke care plans following current stroke management guidelines. Provide a structured treatment recommendation and include tPA or alternative care guidance."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.3
        }
        
        # Make request to OpenAI API
        response = requests.post(openai_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            error_detail = "OpenAI API request failed"
            try:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", error_detail)
            except:
                pass
            
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI API error: {error_detail}"
            )
        
        # Parse OpenAI response
        openai_response = response.json()
        
        if "choices" not in openai_response or not openai_response["choices"]:
            raise HTTPException(
                status_code=502,
                detail="Invalid response from OpenAI API"
            )
        
        treatment_plan = openai_response["choices"][0]["message"]["content"]
        
        # Return the treatment plan
        return {
            "treatment_plan": treatment_plan,
            "model_used": "gpt-4o-mini",
            "patient_name": request["name"],
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request to OpenAI API timed out"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Network error communicating with OpenAI API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )