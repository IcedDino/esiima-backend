from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict

from .database import SessionLocal, engine, Base
from .models import Carrera as DBCarrera, Usuario as DBUsuario, Alumno as DBAlumno, PlanEstudio as DBPlanEstudio
from .schemas import Carrera as SchemaCarrera, UserLogin, Alumno as SchemaAlumno
# IMPORT get_current_user FROM auth.py
from .auth import verify_password, create_access_token, get_current_user
from jose import JWTError, jwt
import os

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_if_not_set")
ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://esiimav3-frontend-cchnfzcbbzgegucu.mexicocentral-01.azurewebsites.net"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------------------------
# LOGIN - MODIFIED to return Token in Body
# ----------------------------------------------------------
@app.post("/login")
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(DBUsuario).options(joinedload(DBUsuario.rol)).filter(
        DBUsuario.email == user_credentials.email).first()

    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user_id = user.docente_id if user.docente_id else user.alumno_id
    if user_id is None:
        raise HTTPException(status_code=403, detail="User account is not fully configured")

    token = create_access_token({
        "sub": user.email,
        "user_id": user_id,
        "role": user.rol.nombre
    })

    # CHANGE: Return the token directly in the JSON
    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "login ok"
    }

# ----------------------------------------------------------
# REMOVED custom get_current_user
# We now use the one imported from .auth which checks headers
# ----------------------------------------------------------

@app.get("/alumnos/me", response_model=SchemaAlumno)
def read_alumnos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "Alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno = db.query(DBAlumno).options(
        joinedload(DBAlumno.plan_estudio).joinedload(DBPlanEstudio.carrera)
    ).filter(DBAlumno.id == current_user["user_id"]).first()

    if alumno is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return alumno

@app.get("/")
def read_root():
    return {"message": "Welcome to the ESIIMA API"}

@app.get("/carreras/", response_model=List[SchemaCarrera])
def read_carreras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(DBCarrera).offset(skip).limit(limit).all()