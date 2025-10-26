from fastapi import APIRouter, Form, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Patient
from typing import Optional
import uuid

router = APIRouter()

# Simple in-memory session store (in production, use Redis or database)
active_sessions = {}

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to get current user from session
def get_current_user(request: Request) -> Optional[dict]:
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        return active_sessions[session_id]
    return None

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

    # Create session
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }

    # Create response with session cookie
    if role == "Patient":
        patient = db.query(Patient).filter_by(linked_user_id=user.id).first()
        if not patient:
            return HTMLResponse(content="""
                <script>alert("Patient record not found. Please wait for technician upload."); window.location.href = "/login-page";</script>
            """, status_code=404)
        response = RedirectResponse(url=f"/patient-view?code={patient.code}", status_code=302)
    elif role == "Technician":
        response = RedirectResponse(url="/technician-dashboard", status_code=302)
    elif role == "Physician":
        response = RedirectResponse(url=f"/physician-dashboard", status_code=302)
    else:
        return HTMLResponse(content="Unknown role", status_code=400)

    # Set session cookie
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=3600)  # 1 hour
    return response

# 🔍 Get current user information
@router.get("/current-user")
def get_current_user_info(request: Request):
    user_info = get_current_user(request)
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_info

# 🚪 Logout
@router.post("/logout")
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    response = RedirectResponse(url="/login-page", status_code=302)
    response.delete_cookie(key="session_id")
    return response
