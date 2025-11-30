from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict

from .database import SessionLocal, engine, Base
from .models import (
    Carrera as DBCarrera, 
    Usuario as DBUsuario, 
    Alumno as DBAlumno, 
    PlanEstudio as DBPlanEstudio, 
    AlumnoExtracurricular as DBAlumnoExtracurricular,
    Inscripcion as DBInscripcion,
    Kardex as DBKardex,
    CalificacionParcial as DBCalificacionParcial,
    DocenteMateria as DBDocenteMateria,
    Materia as DBMateria,
    Grupo as DBGrupo
)
from .schemas import (
    Carrera as SchemaCarrera, 
    UserLogin, 
    Alumno as SchemaAlumno, 
    AlumnoExtracurricular as SchemaAlumnoExtracurricular,
    Calificacion as SchemaCalificacion,
    VerificationKeyUpdate,
    PasswordUpdate
)

# 1. UPDATE THIS IMPORT: Add 'get_current_user'
from .auth import verify_password, create_access_token, get_current_user, get_password_hash
from jose import JWTError, jwt
import os

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_if_not_set")
ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "https://esiimav3-frontend-cchnfzcbbzgegucu.mexicocentral-01.azurewebsites.net",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

    # Return token in JSON body (Compatible with your current main.js)
    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "login ok"
    }


# ------------------------------------------------------------------
# DELETE THE "def get_current_user(request: Request)" FUNCTION HERE
# The import from .auth will handle it automatically now.
# ------------------------------------------------------------------

@app.get("/alumnos/me", response_model=SchemaAlumno)
def read_alumnos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # The 'get_current_user' imported from auth.py will now read the
    # 'Authorization: Bearer ...' header sent by your main.js

    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno = db.query(DBAlumno).options(
        joinedload(DBAlumno.plan_estudio).joinedload(DBPlanEstudio.carrera)
    ).filter(DBAlumno.id == current_user["user_id"]).first()

    if alumno is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return alumno


@app.get("/extracurriculares/me", response_model=List[SchemaAlumnoExtracurricular])
def read_alumno_extracurriculares_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    extracurriculares = db.query(DBAlumnoExtracurricular).options(
        joinedload(DBAlumnoExtracurricular.extracurricular)
    ).filter(DBAlumnoExtracurricular.alumno_id == current_user["user_id"]).all()

    if not extracurriculares:
        return []

    return extracurriculares

@app.get("/calificaciones/me", response_model=List[SchemaCalificacion])
async def read_alumno_calificaciones_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if current_user["role"].lower() != "alumno":
            raise HTTPException(status_code=403, detail="Access denied: User is not a student")

        alumno_id = current_user["user_id"]

        inscripciones = db.query(DBInscripcion).filter(DBInscripcion.alumno_id == alumno_id).options(
            joinedload(DBInscripcion.kardex).joinedload(DBKardex.calificaciones_parciales),
            joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
            joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.grupo)
        ).all()

        if not inscripciones:
            return []

        calificaciones_list = []
        for inscripcion in inscripciones:
            kardex = inscripcion.kardex
            if not kardex:
                continue

            parciales = {cp.unidad: cp.calificacion for cp in kardex.calificaciones_parciales}

            calificacion_data = {
                "materia": {"nombre": inscripcion.docente_materia.materia.nombre},
                "grupo": {"nombre": inscripcion.docente_materia.grupo.nombre},
                "parcial1": parciales.get(1),
                "parcial2": parciales.get(2),
                "parcial3": parciales.get(3),
                "promedio": kardex.calificacion_final
            }
            calificaciones_list.append(calificacion_data)

        return calificaciones_list
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.put("/users/me/verification-key")
def update_verification_key(
    key_update: VerificationKeyUpdate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(DBUsuario).filter(DBUsuario.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify the current verification key
    if not verify_password(key_update.current_verification_key, user.verification_key_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current verification key")

    # Hash the new verification key and update the user
    user.verification_key_hash = get_password_hash(key_update.new_verification_key)
    user.debe_cambiar_clave_verificacion = False
    db.commit()

    return {"message": "Verification key updated successfully"}

@app.put("/users/me/password")
def update_password(
    password_update: PasswordUpdate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(DBUsuario).filter(DBUsuario.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify the current password
    if not verify_password(password_update.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current password")

    # Hash the new password and update the user
    user.password_hash = get_password_hash(password_update.new_password)
    user.debe_cambiar_password = False
    db.commit()

    return {"message": "Password updated successfully"}


@app.get("/")
def read_root():
    return {"message": "Welcome to the ESIIMA API"}


@app.get("/carreras/", response_model=List[SchemaCarrera])
def read_carreras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(DBCarrera).offset(skip).limit(limit).all()