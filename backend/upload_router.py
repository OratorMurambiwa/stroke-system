from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
from .database import SessionLocal
from .models import Patient, StrokeScan
from .tpa_eligibility import check_tpa_eligibility

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
