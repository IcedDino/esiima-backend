from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict

from .database import SessionLocal, engine, Base
from .models import Carrera as DBCarrera, Usuario as DBUsuario, Alumno as DBAlumno, PlanEstudio as DBPlanEstudio
from .schemas import Carrera as SchemaCarrera, UserLogin, Alumno as SchemaAlumno
from .auth import verify_password, create_access_token, get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    user = db.query(DBUsuario).options(joinedload(DBUsuario.rol)).filter(DBUsuario.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = user.docente_id if user.docente_id is not None else user.alumno_id
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user_id, "role": user.rol.nombre}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/alumnos/me", response_model=SchemaAlumno)
def read_alumnos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "Alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    alumno = db.query(DBAlumno).options(
        joinedload(DBAlumno.plan_estudio).joinedload(DBPlanEstudio.carrera)
    ).filter(DBAlumno.id == alumno_id).first()

    if alumno is None:
        raise HTTPException(status_code=404, detail="Student not found")
        
    return alumno

@app.get("/")
def read_root():
    return {"message": "Welcome to the ESIIMA API"}

@app.get("/carreras/", response_model=List[SchemaCarrera])
def read_carreras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    carreras = db.query(DBCarrera).offset(skip).limit(limit).all()
    return carreras
