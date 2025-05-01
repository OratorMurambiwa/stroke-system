from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import User, Patient

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper: shared HTML message page
def message_page(title: str, message: str, link_url: str, link_text: str, color: str = "white", title_color: str = "red") -> HTMLResponse:
    return HTMLResponse(content=f"""
        <html><body style='background:#000;color:{color};text-align:center;padding-top:100px;'>
        <h2 style='color:{title_color};'>{title}</h2>
        <p>{message}</p>
        <a href="{link_url}" style="color:#FDB927;">{link_text}</a>
        </body></html>
    """, status_code=200)

# 🔐 Patient Registration
@router.post("/register")
def register_patient(
    username: str = Form(...),
    password: str = Form(...),
    code: str = Form(...),
    db: Session = Depends(get_db)
):
    # Username already exists?
    if db.query(User).filter_by(username=username).first():
        return message_page("Username already exists", "Please choose a different username.", "/register-page")

    # Check if a patient with the code exists
    patient = db.query(Patient).filter_by(code=code).first()

    # Create the user
    user = User(username=username, password=password, role="Patient")
    db.add(user)
    db.commit()
    db.refresh(user)

    if patient:
        patient.linked_user_id = user.id
        db.commit()
        success_msg = "Your account is now linked to a patient record."
    else:
        success_msg = f"No matching patient code was found now, but your account was created. A technician can link it later using code {code}."

    return message_page("Registration successful!", success_msg, "/login-page", "Go to Login", title_color="green")

# 🔓 Login for all roles
@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(username=username, role=role).first()

    if not user:
        return HTMLResponse(content=f"""
            <script>alert("User not found. Please check the username and role."); window.location.href = "/login-page";</script>
        """, status_code=401)

    if user.password != password:
        return HTMLResponse(content=f"""
            <script>alert("Invalid password. Please try again."); window.location.href = "/login-page";</script>
        """, status_code=401)

    if role == "Patient":
        patient = db.query(Patient).filter_by(linked_user_id=user.id).first()
        if not patient:
            return HTMLResponse(content="""
                <script>alert("Patient record not found. Please wait for technician upload."); window.location.href = "/login-page";</script>
            """, status_code=404)
        return RedirectResponse(url=f"/patient-view?code={patient.code}", status_code=302)

    elif role == "Technician":
        return RedirectResponse(url="/technician-dashboard", status_code=302)

    elif role == "Physician":
        return RedirectResponse(url=f"/physician-dashboard", status_code=302)

    return HTMLResponse(content="Unknown role", status_code=400)
