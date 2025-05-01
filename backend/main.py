from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Import database and models
from backend.database import Base, engine
from backend import models  # this line ensures all models are registered
from backend.auth import router as auth_router
from backend.upload_router import router as upload_router

app = FastAPI()

# ✅ Create tables after models are imported
Base.metadata.create_all(bind=engine)

# ✅ Mount static and upload folders
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ Include route handlers
app.include_router(auth_router)
app.include_router(upload_router)

# ---------- Frontend Page Routes ----------
@app.get("/")
def serve_home():
    return FileResponse(os.path.join("frontend", "index.html"))

@app.get("/login-page")
def serve_login_page():
    return FileResponse(os.path.join("frontend", "login.html"))

@app.get("/register-page")
def serve_register_page():
    return FileResponse(os.path.join("frontend", "register.html"))

@app.get("/upload-form")
def serve_upload_form():
    return FileResponse(os.path.join("frontend", "upload.html"))

@app.get("/patient-view")
def serve_patient_view():
    return FileResponse(os.path.join("frontend", "patient_view.html"))

@app.get("/physician-dashboard")
def serve_physician_dashboard():
    return FileResponse(os.path.join("frontend", "physician_dashboard.html"))

@app.get("/technician-dashboard")
def serve_technician_dashboard():
    return FileResponse(os.path.join("frontend", "technician_dashboard.html"))
