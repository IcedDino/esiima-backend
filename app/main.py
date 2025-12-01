from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
from collections import defaultdict
from sqlalchemy import func

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
    Grupo as DBGrupo,
    Docente as DBProfesor,
    Evaluacion as DBEvaluacion,
    Documento as DBDocumento,
    ServicioSocial as DBServicioSocial,
    PracticasProfesionales as DBPracticasProfesionales,
    Asistencia as DBAsistencia,
    Periodo as DBPeriodo
)
from .schemas import (
    Carrera as SchemaCarrera, 
    UserLogin, 
    Alumno as SchemaAlumno, 
    AlumnoExtracurricular as SchemaAlumnoExtracurricular,
    Calificacion as SchemaCalificacion,
    VerificationKeyUpdate,
    PasswordUpdate,
    User as SchemaUser,
    UserUpdate as SchemaUserUpdate,
    Profesor as SchemaProfesor,
    EvaluacionCreate as SchemaEvaluacionCreate,
    Documento as SchemaDocumento,
    Inscripcion as SchemaInscripcion,
    ServicioSocial as SchemaServicioSocial,
    PracticasProfesionales as SchemaPracticasProfesionales,
    KardexEntry as SchemaKardexEntry,
    MateriaFaltas as SchemaMateriaFaltas
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://esiimav3-frontend-cchnfzcbbzgegucu.mexicocentral-01.azurewebsites.net",
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:5500"
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

@app.get("/users/me", response_model=SchemaUser)
def get_user_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    alumno = db.query(DBAlumno).options(
        joinedload(DBAlumno.plan_estudio).joinedload(DBPlanEstudio.carrera)
    ).filter(DBAlumno.id == current_user["user_id"]).first()

    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Calculate promedio_semestral
    current_period = db.query(DBPeriodo).filter(DBPeriodo.activo == True).first()
    promedio_semestral = None
    if current_period and alumno.cuatrimestre_actual:
        grades = db.query(func.avg(DBKardex.calificacion_final)).join(DBInscripcion).join(DBDocenteMateria).filter(
            DBInscripcion.alumno_id == alumno.id,
            DBDocenteMateria.periodo_id == current_period.id,
            DBDocenteMateria.materia.has(cuatrimestre=alumno.cuatrimestre_actual)
        ).scalar()
        promedio_semestral = grades if grades is not None else 0.0

    user_data = {
        "nombre": alumno.nombre,
        "email": alumno.email,
        "calle": alumno.calle,
        "num_ext": alumno.num_ext,
        "num_int": alumno.num_int,
        "colonia": alumno.colonia,
        "codigo_postal": alumno.codigo_postal,
        "municipio": alumno.municipio,
        "estado": alumno.estado,
        "telefono": alumno.telefono,
        "ciclo_escolar": alumno.ciclo_escolar,
        "nivel_estudios": alumno.nivel_estudios,
        "carrera": alumno.plan_estudio.carrera.nombre if alumno.plan_estudio and alumno.plan_estudio.carrera else None,
        "semestre_grupo": alumno.semestre_grupo,
        "cursa_actualmente": alumno.cursa_actualmente,
        "promedio_semestral": promedio_semestral
    }
    return SchemaUser(**user_data)

@app.put("/users/me", response_model=SchemaUser)
def update_user_me(user_update: SchemaUserUpdate, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(DBUsuario).filter(DBUsuario.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

@app.get("/profesores/me", response_model=List[SchemaProfesor])
def get_profesores_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    inscripciones = db.query(DBInscripcion).filter(DBInscripcion.alumno_id == alumno_id).options(
        joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.docente),
        joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia)
    ).all()
    
    profesores = []
    for inscripcion in inscripciones:
        profesor = inscripcion.docente_materia.docente
        materia = inscripcion.docente_materia.materia
        profesores.append({
            "id": profesor.id,
            "nombre": profesor.nombre,
            "materia": materia.nombre,
            "materia_id": materia.id
        })
    return profesores

@app.post("/evaluaciones", status_code=status.HTTP_201_CREATED)
def create_evaluacion(evaluacion: SchemaEvaluacionCreate, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    db_evaluacion = DBEvaluacion(
        profesor_id=evaluacion.profesor_id,
        alumno_id=alumno_id,
        materia_id=evaluacion.materia_id,
        calificacion=evaluacion.calificacion
    )
    db.add(db_evaluacion)
    db.commit()
    return {"message": "Evaluación enviada exitosamente."}

@app.get("/documentos/me", response_model=List[SchemaDocumento])
def get_documentos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    documentos = db.query(DBDocumento).filter(DBDocumento.alumno_id == alumno_id).all()
    
    # This is a placeholder as there is no direct mapping for clave_doc and entregado
    # in the Documento model. You might need to adjust this based on your actual model logic.
    return [{"clave_doc": "N/A", "nombre": doc.nombre_archivo, "entregado": True, "observaciones": doc.comentarios} for doc in documentos]

@app.get("/inscripciones/me", response_model=List[SchemaInscripcion])
def get_inscripciones_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    inscripciones = db.query(DBInscripcion).filter(DBInscripcion.alumno_id == alumno_id).options(
        joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
        joinedload(DBInscripcion.kardex).joinedload(DBKardex.calificaciones_parciales)
    ).all()

    results = []
    for inscripcion in inscripciones:
        kardex = inscripcion.kardex
        parciales = {cp.unidad: cp.calificacion for cp in kardex.calificaciones_parciales} if kardex else {}
        
        results.append({
            "materia": inscripcion.docente_materia.materia,
            "calificacion_parcial1": parciales.get(1),
            "calificacion_parcial2": parciales.get(2),
            "calificacion_parcial3": parciales.get(3),
            "promedio_final": kardex.calificacion_final if kardex else None
        })
    return results

@app.get("/serviciosocial/me", response_model=List[SchemaServicioSocial])
def get_servicio_social_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    servicio_social = db.query(DBServicioSocial).filter(DBServicioSocial.alumno_id == alumno_id).all()
    return servicio_social

@app.get("/practicas/me", response_model=List[SchemaPracticasProfesionales])
def get_practicas_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    practicas = db.query(DBPracticasProfesionales).filter(DBPracticasProfesionales.alumno_id == alumno_id).all()
    return practicas

@app.get("/kardex/me", response_model=Dict[str, List[SchemaKardexEntry]])
def get_kardex_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    inscripciones = db.query(DBInscripcion).filter(DBInscripcion.alumno_id == alumno_id).options(
        joinedload(DBInscripcion.kardex),
        joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
        joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.periodo)
    ).all()

    kardex_data = defaultdict(list)
    for inscripcion in inscripciones:
        materia = inscripcion.docente_materia.materia
        periodo = inscripcion.docente_materia.periodo
        kardex = inscripcion.kardex

        if not all([materia, periodo, kardex]):
            continue

        semestre = str(materia.cuatrimestre)
        
        # Placeholder logic for oports_agotadas and alto_riesgo
        oports_agotadas = kardex.intento or 1
        alto_riesgo = oports_agotadas > 1

        entry = SchemaKardexEntry(
            clave=materia.clave,
            materia=materia.nombre,
            oports_agotadas=oports_agotadas,
            alto_riesgo=alto_riesgo,
            periodo=periodo.nombre,
            calificacion=kardex.calificacion_final,
            tipo_examen=kardex.tipo_examen or "Ordinario"
        )
        kardex_data[semestre].append(entry)

    return kardex_data

@app.get("/materias/me", response_model=List[SchemaMateriaFaltas])
def get_materias_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    inscripciones = db.query(DBInscripcion).filter(DBInscripcion.alumno_id == alumno_id).options(
        joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
        joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.grupo)
    ).all()

    materias_data = []
    for inscripcion in inscripciones:
        materia = inscripcion.docente_materia.materia
        grupo = inscripcion.docente_materia.grupo

        if not all([materia, grupo]):
            continue

        total_faltas = db.query(DBAsistencia).filter(
            DBAsistencia.inscripcion_id == inscripcion.id,
            DBAsistencia.presente == False
        ).count()
        
        horas_semana = (materia.horas_teoricas or 0) + (materia.horas_practicas or 0)

        entry = SchemaMateriaFaltas(
            horas_semana=horas_semana,
            nombre=materia.nombre,
            semestre=materia.cuatrimestre,
            grupo=grupo.nombre,
            faltas_permitidas=materia.faltas_permitidas or 10, # Default to 10 if not set
            total_faltas=total_faltas,
            horas_teoricas=materia.horas_teoricas or 0,
            horas_practicas=materia.horas_practicas or 0
        )
        materias_data.append(entry)

    return materias_data
