from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
from collections import defaultdict
from sqlalchemy import func
import traceback
import logging

##This is a random comment to force redeploy

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
    Periodo as DBPeriodo,
    HorarioDetalle as DBHorarioDetalle,
    Solicitud as DBSolicitud,
    TitulacionRequisito as DBTitulacionRequisito,
    AlumnoTitulacion as DBAlumnoTitulacion
)
#Comment to force redeploy
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
    MateriaFaltas as SchemaMateriaFaltas,
    Examen as SchemaExamen,
    Horario as SchemaHorario,
    MateriaNoAprobada as SchemaMateriaNoAprobada,
    SolicitudCreate as SchemaSolicitudCreate,
    RequisitoTitulacion as SchemaRequisitoTitulacion,
    FaltaDetalle as SchemaFaltaDetalle,
    PartialGrade as SchemaPartialGrade
)

# 1. UPDATE THIS IMPORT: Add 'get_current_user'
from .auth import verify_password, create_access_token, get_current_user, get_password_hash
from jose import JWTError, jwt
import os

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_if_not_set")
ALGORITHM = "HS256"

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
        
        alumno = db.query(DBAlumno).filter(DBAlumno.id == alumno_id).first()
        if not alumno:
            raise HTTPException(status_code=404, detail="Student not found")
        current_cuatrimestre = alumno.cuatrimestre_actual

        inscripciones = db.query(DBInscripcion).join(DBDocenteMateria).join(DBMateria).filter(
            DBInscripcion.alumno_id == alumno_id,
            DBMateria.cuatrimestre == current_cuatrimestre
        ).options(
            joinedload(DBInscripcion.kardex).joinedload(DBKardex.calificaciones_parciales),
            joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
            joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.grupo)
        ).all()

        if not inscripciones:
            return []

        calificaciones_list = []
        for inscripcion in inscripciones:
            if not inscripcion.docente_materia or not inscripcion.docente_materia.materia:
                continue

            kardex = inscripcion.kardex
            
            parcial1, parcial2, parcial3, promedio = None, None, None, None

            if kardex:
                parciales = {cp.unidad: cp.calificacion for cp in kardex.calificaciones_parciales}
                parcial1 = parciales.get(1)
                parcial2 = parciales.get(2)
                parcial3 = parciales.get(3)
                promedio = kardex.calificacion_final

            calificacion_obj = SchemaCalificacion(
                materia=inscripcion.docente_materia.materia,
                calificacion_parcial1=parcial1,
                calificacion_parcial2=parcial2,
                calificacion_parcial3=parcial3,
                promedio_final=promedio
            )
            calificaciones_list.append(calificacion_obj)

        return calificaciones_list
    except Exception as e:
        logging.error(f"Error in /calificaciones/me: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}. Check server logs for more details."
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
    try:
        user_email = current_user.get("sub")
        if not user_email:
            logging.error(f"Error in /users/me: 'sub' key not found in token payload. Payload: {current_user}")
            raise HTTPException(status_code=403, detail="Invalid token: User identifier not found.")

        user = db.query(DBUsuario).options(
            joinedload(DBUsuario.alumno).joinedload(DBAlumno.plan_estudio).joinedload(DBPlanEstudio.carrera),
            joinedload(DBUsuario.docente)
        ).filter(DBUsuario.email == user_email).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email {user_email} not found.")

        if user.alumno:
            full_name = f"{user.alumno.nombre} {user.alumno.apellido_paterno} {user.alumno.apellido_materno or ''}".strip()
            return SchemaUser(
                nombre=full_name,
                email=user.email,
                calle=user.alumno.calle,
                num_ext=user.alumno.num_ext,
                num_int=user.alumno.num_int,
                colonia=user.alumno.colonia,
                codigo_postal=user.alumno.codigo_postal,
                municipio=user.alumno.municipio,
                estado=user.alumno.estado,
                telefono=user.alumno.telefono,
                ciclo_escolar=user.alumno.ciclo_escolar,
                nivel_estudios=user.alumno.nivel_estudios,
                carrera=user.alumno.plan_estudio.carrera.nombre if user.alumno.plan_estudio and user.alumno.plan_estudio.carrera else None,
                semestre_grupo=user.alumno.semestre_grupo,
                cursa_actualmente=user.alumno.cursa_actualmente,
                promedio_semestral=None 
            )
        elif user.docente:
            full_name = f"{user.docente.nombre} {user.docente.apellido_paterno} {user.docente.apellido_materno or ''}".strip()
            return SchemaUser(
                nombre=full_name,
                email=user.email
            )
        else:
            return SchemaUser(
                nombre="Usuario sin rol asignado",
                email=user.email
            )
    except Exception as e:
        logging.error(f"Error in /users/me: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}. Check server logs for more details."
        )

@app.put("/users/me", response_model=SchemaUser)
def update_user_me(user_update: SchemaUserUpdate, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_email = current_user.get("sub")
    if not user_email:
        raise HTTPException(status_code=403, detail="Invalid token: User identifier not found.")

    user = db.query(DBUsuario).filter(DBUsuario.email == user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.alumno:
        update_data = user_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(user.alumno, key):
                setattr(user.alumno, key, value)
        if 'email' in update_data:
            user.email = update_data['email']
    
    db.commit()
    db.refresh(user)
    if user.alumno:
        db.refresh(user.alumno)

    # Re-fetch the updated user to return the correct data
    return get_user_me(current_user, db)

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
    try:
        if current_user["role"].lower() != "alumno":
            raise HTTPException(status_code=403, detail="Access denied: User is not a student")

        alumno_id = current_user["user_id"]
        
        servicio_social_records = db.query(DBServicioSocial).filter(DBServicioSocial.alumno_id == alumno_id).options(
            joinedload(DBServicioSocial.estatus)
        ).all()

        if not servicio_social_records:
            return []

        return servicio_social_records
    except Exception as e:
        logging.error(f"Error in /serviciosocial/me: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}. Check server logs for more details."
        )

@app.get("/practicas/me", response_model=List[SchemaPracticasProfesionales])
def get_practicas_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    practicas = db.query(DBPracticasProfesionales).filter(DBPracticasProfesionales.alumno_id == alumno_id).all()
    return practicas

@app.get("/kardex/me", response_model=Dict[str, List[SchemaKardexEntry]])
def get_kardex_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
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
            # Defensive checks for related objects
            if not inscripcion.docente_materia or not inscripcion.docente_materia.materia or not inscripcion.docente_materia.periodo:
                continue

            materia = inscripcion.docente_materia.materia
            periodo = inscripcion.docente_materia.periodo
            kardex = inscripcion.kardex

            # Handle cases where a kardex record might not exist for an inscription
            if kardex:
                oports_agotadas = kardex.intento or 1
                calificacion = kardex.calificacion_final
                tipo_examen = kardex.tipo_examen or "Ordinario"
            else:
                oports_agotadas = 1
                calificacion = None
                tipo_examen = "N/A"

            semestre = str(materia.cuatrimestre)
            alto_riesgo = oports_agotadas > 1

            entry = SchemaKardexEntry(
                id=materia.id, # Added materia ID
                clave=materia.clave,
                materia=materia.nombre,
                oports_agotadas=oports_agotadas,
                alto_riesgo=alto_riesgo,
                periodo=periodo.nombre,
                calificacion=calificacion,
                tipo_examen=tipo_examen
            )
            kardex_data[semestre].append(entry)

        return kardex_data
    except Exception as e:
        # Log the full error traceback to the server console
        logging.error(traceback.format_exc())
        # Return a more informative error to the client
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred: {str(e)}"
        )

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
            id=materia.id,
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

@app.get("/faltas/me/{materia_id}", response_model=List[SchemaFaltaDetalle])
def get_faltas_me(materia_id: int, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]

    faltas = db.query(DBAsistencia).join(DBInscripcion).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBInscripcion.docente_materia.has(materia_id=materia_id),
        DBAsistencia.presente == False
    ).all()

    return faltas

@app.get("/examenes/me", response_model=List[SchemaExamen])
def get_examenes_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    # This is a placeholder implementation. You will need to adjust it to your actual logic for exams.
    # This example assumes exams are stored in the Kardex table with a type_examen.
    kardex_entries = db.query(DBKardex).join(DBInscripcion).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBKardex.tipo_examen != None
    ).options(
        joinedload(DBKardex.inscripcion).joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
        joinedload(DBKardex.inscripcion).joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.docente)
    ).all()

    examenes = []
    for entry in kardex_entries:
        materia = entry.inscripcion.docente_materia.materia
        docente = entry.inscripcion.docente_materia.docente
        examenes.append({
            "materia": materia.nombre,
            "semestre": materia.cuatrimestre,
            "calificacion": entry.calificacion_final,
            "maestro": docente.nombre,
            "lugar_fecha_hora": "Not specified" # Placeholder
        })

    return examenes

@app.get("/horario/me", response_model=Dict[str, Dict[str, str]])
def get_horario_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    # Get the student's current cuatrimestre
    alumno = db.query(DBAlumno).filter(DBAlumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Student not found")
    
    current_cuatrimestre = alumno.cuatrimestre_actual

    # Query for horario details, filtering by the student's current cuatrimestre
    horarios = db.query(DBHorarioDetalle).join(DBDocenteMateria).join(DBInscripcion).join(DBMateria).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBMateria.cuatrimestre == current_cuatrimestre
    ).options(
        joinedload(DBHorarioDetalle.docente_materia).joinedload(DBDocenteMateria.materia)
    ).all()

    horario_data = defaultdict(dict)
    dias_semana = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO"]

    for detalle in horarios:
        hora_inicio = detalle.horario_inicio.strftime("%H:%M")
        hora_fin = detalle.horario_fin.strftime("%H:%M")
        dia = dias_semana[detalle.dia_semana - 1]
        materia = detalle.docente_materia.materia.nombre
        
        horario_data[f"{hora_inicio} - {hora_fin}"][dia] = materia

    return horario_data

@app.get("/materias/no-aprobadas", response_model=List[SchemaMateriaNoAprobada])
def get_materias_no_aprobadas(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    materias = db.query(DBMateria).join(DBDocenteMateria).join(DBInscripcion).join(DBKardex).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBKardex.aprobado == False
    ).all()

    return materias

@app.post("/solicitudes", status_code=status.HTTP_201_CREATED)
def create_solicitud(solicitud: SchemaSolicitudCreate, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    for materia_id in solicitud.materias:
        db_solicitud = DBSolicitud(
            alumno_id=alumno_id,
            materia_id=materia_id
        )
        db.add(db_solicitud)
    
    db.commit()
    return {"message": "Solicitud enviada exitosamente."}

@app.get("/requisitos/me", response_model=List[SchemaRequisitoTitulacion])
def get_requisitos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    alumno = db.query(DBAlumno).filter(DBAlumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Student not found")

    requisitos = db.query(DBTitulacionRequisito).filter(
        DBTitulacionRequisito.plan_estudio_id == alumno.plan_estudio_id
    ).all()

    results = []
    for req in requisitos:
        alumno_req = db.query(DBAlumnoTitulacion).filter(
            DBAlumnoTitulacion.alumno_id == alumno_id,
            DBAlumnoTitulacion.requisito_id == req.id
        ).first()

        results.append({
            "nombre": req.requisito,
            "unidades_a_cubrir": req.unidades_requeridas or 0,
            "tipo_unidad": req.tipo_unidad or "N/A",
            "unidades_cubiertas": (alumno_req.unidades_cubiertas or 0) if alumno_req else 0
        })

    return results

@app.get("/calificaciones/parciales/materia/{materia_id}", response_model=List[SchemaPartialGrade])
def get_partial_grades_for_materia(
    materia_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"].lower() != "alumno":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]

    # Find the inscription for this student and materia
    inscription = db.query(DBInscripcion).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBInscripcion.docente_materia.has(materia_id=materia_id)
    ).first()

    if not inscription:
        raise HTTPException(status_code=404, detail="Inscription not found for this student and materia.")

    # Find the kardex entry for this inscription
    kardex_entry = db.query(DBKardex).filter(
        DBKardex.inscripcion_id == inscription.id
    ).first()

    if not kardex_entry:
        return [] # No partial grades if no kardex entry

    # Get all partial grades for this kardex entry
    partial_grades = db.query(DBCalificacionParcial).filter(
        DBCalificacionParcial.kardex_id == kardex_entry.id
    ).all()

    return partial_grades
