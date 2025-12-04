from fastapi import FastAPI, Depends, HTTPException, status, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
from collections import defaultdict
from sqlalchemy import func
import traceback
import logging
import shutil
from datetime import date as date_module, date  # Import date

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
    AlumnoTitulacion as DBAlumnoTitulacion,
    Pago as DBPago,
    CatTiposDocumento as DBCatTiposDocumento,
    CatRoles as DBCatRoles,
    CatEstatusAlumnos as DBCatEstatusAlumnos # Import CatEstatusAlumnos
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
    PartialGrade as SchemaPartialGrade,
    Pago as SchemaPago,
    TeacherGroup,
    StudentGrade,
    StudentGradeUpdate,
    AttendanceSaveRequest,
    AttendanceEntry,
    StudentRegister
)

# 1. UPDATE THIS IMPORT: Add 'get_current_user'
from .auth import verify_password, create_access_token, get_current_user, get_password_hash
from jose import JWTError, jwt
import os
import uuid
from sqlalchemy.exc import IntegrityError

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_if_not_set")
ALGORITHM = "HS256"

app = FastAPI()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")
allowed_origins = [o.strip() for o in ALLOWED_ORIGINS.split(",")] if ALLOWED_ORIGINS else [
    "https://esiimav3-frontend-cchnfzcbbzgegucu.mexicocentral-01.azurewebsites.net",
    "http://localhost:5173",
    "http://localhost:3000",
]
allow_origin_regex = os.getenv("ALLOW_ORIGIN_REGEX") or r"https://.*azurewebsites\.net"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
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
    user = db.query(DBUsuario).options(
        joinedload(DBUsuario.rol),
        joinedload(DBUsuario.alumno),
        joinedload(DBUsuario.docente)
    ).filter(DBUsuario.email == user_credentials.email).first()

    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user_id = user.docente_id if user.docente_id else user.alumno_id
    if user_id is None:
        raise HTTPException(status_code=403, detail="User account is not fully configured")

    role = "unknown"
    full_name = "Usuario"
    if user.rol.nombre.lower() == "docente" and user.docente:
        role = "teacher"
        full_name = f"{user.docente.nombre} {user.docente.apellido_paterno} {user.docente.apellido_materno or ''}".strip()
    elif user.rol.nombre.lower() == "alumno" and user.alumno:
        role = "student"
        full_name = f"{user.alumno.nombre} {user.alumno.apellido_paterno} {user.alumno.apellido_materno or ''}".strip()

    token = create_access_token({
        "sub": user.email,
        "user_id": user_id,
        "role": role,
        "full_name": full_name
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role,
        "full_name": full_name,
        "message": "login ok"
    }

@app.post("/enroll/register", status_code=status.HTTP_201_CREATED)
def register_student(student_data: StudentRegister, db: Session = Depends(get_db)):
    logging.info(f"Received student registration data: {student_data.dict()}") # Log incoming data

    # Check if email or CURP already exists
    if db.query(DBUsuario).filter(DBUsuario.email == student_data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if db.query(DBAlumno).filter(DBAlumno.curp == student_data.curp).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CURP already registered")

    # Get default student status
    default_status = db.query(DBCatEstatusAlumnos).filter(DBCatEstatusAlumnos.nombre == "Activo").first()
    if not default_status:
        default_status = DBCatEstatusAlumnos(nombre="Activo", descripcion="Alumno activo", es_baja=False, orden=1)
        db.add(default_status)
        db.flush()

    # Create Alumno record
    temp_matricula = f"TEMP-{uuid.uuid4().hex[:12]}"
    new_alumno = DBAlumno(
        nombre=student_data.nombre,
        apellido_paterno=student_data.apellidoPaterno,
        apellido_materno=student_data.apellidoMaterno,
        fecha_nacimiento=student_data.fechaNacimiento,
        curp=student_data.curp,
        email=student_data.email,
        matricula=temp_matricula,
        estatus_id=default_status.id, # Set the default status
        fecha_ingreso=date.today() # Set the current date as fecha_ingreso
    )
    db.add(new_alumno)
    try:
        db.flush() # Use flush to get the new_alumno.id before commit
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error creando alumno: {str(e.orig) if hasattr(e, 'orig') else str(e)}")

    # Get student role
    student_role = db.query(DBCatRoles).filter(DBCatRoles.nombre == "alumno").first()
    if not student_role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Student role not found in catalog")

    # Create Usuario record
    hashed_password = get_password_hash(student_data.password)
    new_user = DBUsuario(
        email=student_data.email,
        password_hash=hashed_password,
        rol_id=student_role.id,
        alumno_id=new_alumno.id,
        debe_cambiar_password=True # Force password change on first login
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error creando usuario: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    db.refresh(new_alumno)
    db.refresh(new_user)

    # Generate access token
    full_name = f"{new_alumno.nombre} {new_alumno.apellido_paterno} {new_alumno.apellido_materno or ''}".strip()
    access_token = create_access_token({
        "sub": new_user.email,
        "user_id": new_alumno.id,
        "role": "student",
        "full_name": full_name
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "student",
        "full_name": full_name,
        "message": "Student registered successfully"
    }


# ------------------------------------------------------------------
# DELETE THE "def get_current_user(request: Request)" FUNCTION HERE
# The import from .auth will handle it automatically now.
# ------------------------------------------------------------------

@app.get("/alumnos/me", response_model=SchemaAlumno)
def read_alumnos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno = db.query(DBAlumno).options(
        joinedload(DBAlumno.plan_estudio).joinedload(DBPlanEstudio.carrera)
    ).filter(DBAlumno.id == current_user["user_id"]).first()

    if alumno is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return alumno


@app.get("/extracurriculares/me", response_model=List[SchemaAlumnoExtracurricular])
def read_alumno_extracurriculares_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
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
        if current_user.get("role") != "student":
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

    if not verify_password(key_update.current_verification_key, user.verification_key_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current verification key")

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

    if not verify_password(password_update.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current password")

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

    return get_user_me(current_user, db)

@app.get("/profesores/me", response_model=List[SchemaProfesor])
def get_profesores_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
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
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    # Enforce one evaluation per alumno-profesor-materia
    existing = db.query(DBEvaluacion).filter(
        DBEvaluacion.profesor_id == evaluacion.profesor_id,
        DBEvaluacion.alumno_id == alumno_id,
        DBEvaluacion.materia_id == evaluacion.materia_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya has evaluado a este profesor para esta materia.")

    db_evaluacion = DBEvaluacion(
        profesor_id=evaluacion.profesor_id,
        alumno_id=alumno_id,
        materia_id=evaluacion.materia_id,
        calificacion=evaluacion.calificacion
    )
    db.add(db_evaluacion)
    db.commit()
    return {"message": "Evaluación enviada exitosamente."}

@app.get("/evaluaciones/me")
def get_evaluaciones_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    evaluaciones = db.query(DBEvaluacion).filter(DBEvaluacion.alumno_id == alumno_id).all()
    return [
        {
            "profesor_id": ev.profesor_id,
            "materia_id": ev.materia_id,
            "calificacion": ev.calificacion
        } for ev in evaluaciones
    ]

@app.get("/documentos/me", response_model=List[SchemaDocumento])
def get_documentos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    # Get all document types from the catalog
    tipos_documento = db.query(DBCatTiposDocumento).filter(DBCatTiposDocumento.activo == True).all()
    
    # Get all documents uploaded by the student
    documentos_alumno = db.query(DBDocumento).filter(DBDocumento.alumno_id == alumno_id).all()
    
    # Create a dictionary for quick lookup of uploaded documents
    mapa_documentos_alumno = {doc.tipo_id: doc for doc in documentos_alumno}
    
    # Prepare the response
    documentos_a_mostrar = []
    for tipo_doc in tipos_documento:
        doc_alumno = mapa_documentos_alumno.get(tipo_doc.id)
        documentos_a_mostrar.append({
            "id": tipo_doc.id,
            "nombre": tipo_doc.nombre,
            "entregado": doc_alumno is not None,
            "observaciones": doc_alumno.comentarios if doc_alumno else None
        })
        
    return documentos_a_mostrar

@app.post("/documentos/{doc_id}/upload")
async def upload_document(doc_id: int, file: UploadFile = File(...), current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    # Check if a document of this type already exists for the student
    doc = db.query(DBDocumento).filter(DBDocumento.tipo_id == doc_id, DBDocumento.alumno_id == alumno_id).first()

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if doc:
        # Update existing document
        doc.ruta_archivo = file_path
        doc.nombre_archivo = file.filename
        doc.tamano_bytes = file.file.tell()
        doc.mime_type = file.content_type
        doc.fecha_subida = func.now()
        doc.estatus_id = 1 # Assuming 1 is "Uploaded"
    else:
        # Create new document
        doc = DBDocumento(
            alumno_id=alumno_id,
            tipo_id=doc_id,
            nombre_archivo=file.filename,
            ruta_archivo=file_path,
            tamano_bytes=file.file.tell(),
            mime_type=file.content_type,
            estatus_id=1 # Assuming 1 is "Uploaded"
        )
        db.add(doc)

    db.commit()

    return {"message": "Document uploaded successfully"}

@app.get("/inscripciones/me", response_model=List[SchemaInscripcion])
def get_inscripciones_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
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
        if current_user.get("role") != "student":
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
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    practicas = db.query(DBPracticasProfesionales).filter(DBPracticasProfesionales.alumno_id == alumno_id).all()
    return practicas

@app.get("/kardex/me", response_model=Dict[str, List[SchemaKardexEntry]])
def get_kardex_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if current_user.get("role") != "student":
            raise HTTPException(status_code=403, detail="Access denied: User is not a student")

        alumno_id = current_user["user_id"]
        
        inscripciones = db.query(DBInscripcion).filter(DBInscripcion.alumno_id == alumno_id).options(
            joinedload(DBInscripcion.kardex),
            joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
            joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.periodo)
        ).all()

        kardex_data = defaultdict(list)
        for inscripcion in inscripciones:
            if not inscripcion.docente_materia or not inscripcion.docente_materia.materia or not inscripcion.docente_materia.periodo:
                continue

            materia = inscripcion.docente_materia.materia
            periodo = inscripcion.docente_materia.periodo
            kardex = inscripcion.kardex

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
                id=materia.id,
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
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred: {str(e)}"
        )

@app.get("/materias/me", response_model=List[SchemaMateriaFaltas])
def get_materias_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
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
            faltas_permitidas=materia.faltas_permitidas or 10,
            total_faltas=total_faltas,
            horas_teoricas=materia.horas_teoricas or 0,
            horas_practicas=materia.horas_practicas or 0
        )
        materias_data.append(entry)

    return materias_data

@app.get("/faltas/me/{materia_id}", response_model=List[SchemaFaltaDetalle])
def get_faltas_me(materia_id: int, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
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
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    kardex_entries = db.query(DBKardex).join(DBInscripcion).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBKardex.tipo_examen != None
    ).options(
        joinedload(DBKardex.inscripcion).joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.materia),
        joinedload(DBKardex.inscripcion).joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.docente)
    ).all()

    examenes = []
    seen_materia_ids = set()
    for entry in kardex_entries:
        materia = entry.inscripcion.docente_materia.materia
        docente = entry.inscripcion.docente_materia.docente
        examenes.append({
            "materia": materia.nombre,
            "semestre": materia.cuatrimestre,
            "calificacion": entry.calificacion_final,
            "maestro": docente.nombre,
            "lugar_fecha_hora": "Not specified"
        })
        if materia and materia.id:
            seen_materia_ids.add(materia.id)

    # Include solicitudes pendientes como próximos extraordinarios
    solicitudes = db.query(DBSolicitud).filter(DBSolicitud.alumno_id == alumno_id).options(
        joinedload(DBSolicitud.materia)
    ).all()
    for sol in solicitudes:
        if not sol.materia:
            continue
        mid = sol.materia.id
        if mid in seen_materia_ids:
            continue
        # Try to find current docente for this materia from an inscripcion
        insc = db.query(DBInscripcion).filter(
            DBInscripcion.alumno_id == alumno_id,
            DBInscripcion.docente_materia.has(materia_id=mid)
        ).options(joinedload(DBInscripcion.docente_materia).joinedload(DBDocenteMateria.docente)).first()
        docente_nombre = insc.docente_materia.docente.nombre if insc and insc.docente_materia and insc.docente_materia.docente else "Pendiente"
        examenes.append({
            "materia": sol.materia.nombre,
            "semestre": sol.materia.cuatrimestre,
            "calificacion": None,
            "maestro": docente_nombre,
            "lugar_fecha_hora": "Pendiente"
        })
        seen_materia_ids.add(mid)

    return examenes

@app.get("/horario/me", response_model=Dict[str, Dict[str, str]])
def get_horario_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    alumno = db.query(DBAlumno).filter(DBAlumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Student not found")
    
    current_cuatrimestre = alumno.cuatrimestre_actual

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
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    
    materias = db.query(DBMateria).join(DBDocenteMateria).join(DBInscripcion).join(DBKardex).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBKardex.aprobado == False
    ).all()

    # Excluir materias ya solicitadas
    solicitudes_materia_ids = set(
        m_id for (m_id,) in db.query(DBSolicitud.materia_id).filter(DBSolicitud.alumno_id == alumno_id).all()
    )
    materias_filtradas = [m for m in materias if m.id not in solicitudes_materia_ids]

    return materias_filtradas

@app.post("/solicitudes", status_code=status.HTTP_201_CREATED)
def create_solicitud(solicitud: SchemaSolicitudCreate, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
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
    if current_user.get("role") != "student":
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
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]

    inscription = db.query(DBInscripcion).filter(
        DBInscripcion.alumno_id == alumno_id,
        DBInscripcion.docente_materia.has(materia_id=materia_id)
    ).first()

    if not inscription:
        raise HTTPException(status_code=404, detail="Inscription not found for this student and materia.")

    kardex_entry = db.query(DBKardex).filter(
        DBKardex.inscripcion_id == inscription.id
    ).first()

    if not kardex_entry:
        return []

    partial_grades = db.query(DBCalificacionParcial).filter(
        DBCalificacionParcial.kardex_id == kardex_entry.id
    ).all()

    return partial_grades

@app.get("/pagos/me", response_model=List[SchemaPago])
def get_pagos_me(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access denied: User is not a student")

    alumno_id = current_user["user_id"]
    pagos = db.query(DBPago).filter(DBPago.alumno_id == alumno_id).options(
        joinedload(DBPago.estatus),
        joinedload(DBPago.periodo)
    ).all()

    if not pagos:
        return []

    return [
        {
            "estado": pago.estatus.nombre,
            "ciclo": pago.periodo.nombre,
            "cargo": pago.monto_total,
            "abono": pago.monto_pagado,
            "saldo": pago.monto_total - pago.monto_pagado
        } for pago in pagos
    ]

@app.get("/teacher/groups", response_model=List[TeacherGroup])
def get_teacher_groups(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Access denied: User is not a teacher")

    docente_id = current_user["user_id"]
    
    docente_materias = db.query(DBDocenteMateria).filter(
        DBDocenteMateria.docente_id == docente_id,
        DBDocenteMateria.activo == True
    ).options(
        joinedload(DBDocenteMateria.materia),
        joinedload(DBDocenteMateria.grupo)
    ).all()

    if not docente_materias:
        return []

    teacher_groups = []
    for dm in docente_materias:
        if dm.grupo and dm.materia:
            teacher_groups.append(
                TeacherGroup(
                    id=dm.grupo.id,
                    nombre=dm.grupo.nombre,
                    materia=dm.materia
                )
            )
            
    return teacher_groups

@app.get("/groups/{group_id}/students", response_model=List[SchemaAlumno])
def get_group_students(group_id: int, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Access denied: User is not a teacher")

    inscripciones = db.query(DBInscripcion).filter(
        DBInscripcion.docente_materia.has(grupo_id=group_id)
    ).options(
        joinedload(DBInscripcion.alumno)
    ).all()

    unique_alumnos: Dict[int, DBAlumno] = {}
    for inscripcion in inscripciones:
        alumno = inscripcion.alumno
        if alumno and alumno.id not in unique_alumnos:
            unique_alumnos[alumno.id] = alumno

    return list(unique_alumnos.values())

@app.get("/groups/{group_id}/grades", response_model=List[StudentGrade])
def get_group_grades(group_id: int, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Access denied: User is not a teacher")

    inscripciones = db.query(DBInscripcion).filter(
        DBInscripcion.docente_materia.has(grupo_id=group_id)
    ).options(
        joinedload(DBInscripcion.alumno),
        joinedload(DBInscripcion.kardex).joinedload(DBKardex.calificaciones_parciales)
    ).all()

    student_grades = []
    for inscripcion in inscripciones:
        parciales = {cp.unidad: cp.calificacion for cp in inscripcion.kardex.calificaciones_parciales} if inscripcion.kardex else {}
        student_grades.append(
            StudentGrade(
                student=inscripcion.alumno,
                parcial1=parciales.get(1),
                parcial2=parciales.get(2),
                parcial3=parciales.get(3)
            )
        )
    return student_grades

@app.post("/groups/{group_id}/grades", status_code=status.HTTP_204_NO_CONTENT)
def update_group_grades(group_id: int, grades: List[StudentGradeUpdate], current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Access denied: User is not a teacher")

    for grade_update in grades:
        inscripcion = db.query(DBInscripcion).filter(
            DBInscripcion.alumno_id == grade_update.student_id,
            DBInscripcion.docente_materia.has(grupo_id=group_id)
        ).first()

        if not inscripcion:
            continue

        kardex = db.query(DBKardex).filter(DBKardex.inscripcion_id == inscripcion.id).first()
        if not kardex:
            kardex = DBKardex(inscripcion_id=inscripcion.id, estatus_id=1)
            db.add(kardex)
            db.flush()

        for parcial, calificacion in [ (1, grade_update.parcial1), (2, grade_update.parcial2), (3, grade_update.parcial3) ]:
            if calificacion is None:
                continue
            
            calificacion_parcial = db.query(DBCalificacionParcial).filter(
                DBCalificacionParcial.kardex_id == kardex.id,
                DBCalificacionParcial.unidad == parcial
            ).first()

            if calificacion_parcial:
                calificacion_parcial.calificacion = calificacion
            else:
                db.add(DBCalificacionParcial(kardex_id=kardex.id, unidad=parcial, calificacion=calificacion))

    db.commit()

@app.get("/groups/{group_id}/attendance", response_model=List[AttendanceEntry])
def get_group_attendance(group_id: int, date: str, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Access denied: User is not a teacher")

    docente_id = current_user["user_id"]
    dm = db.query(DBDocenteMateria).filter(
        DBDocenteMateria.docente_id == docente_id,
        DBDocenteMateria.grupo_id == group_id,
        DBDocenteMateria.activo == True
    ).first()
    if not dm:
        raise HTTPException(status_code=403, detail="Access denied: Group not assigned to teacher")

    try:
        query_date = date_module.fromisoformat(date)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    inscripciones = db.query(DBInscripcion).filter(
        DBInscripcion.docente_materia_id == dm.id
    ).options(joinedload(DBInscripcion.alumno)).all()

    entries: List[AttendanceEntry] = []
    for inscripcion in inscripciones:
        asistencia = db.query(DBAsistencia).filter(
            DBAsistencia.inscripcion_id == inscripcion.id,
            DBAsistencia.fecha == query_date
        ).order_by(DBAsistencia.created_at.desc()).first()
        if asistencia:
            entries.append(AttendanceEntry(student_id=inscripcion.alumno_id, status="presente" if asistencia.presente else "ausente"))

    return entries

@app.post("/groups/{group_id}/attendance", status_code=status.HTTP_204_NO_CONTENT)
def save_group_attendance(group_id: int, payload: AttendanceSaveRequest, current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Access denied: User is not a teacher")

    docente_id = current_user["user_id"]
    dm = db.query(DBDocenteMateria).filter(
        DBDocenteMateria.docente_id == docente_id,
        DBDocenteMateria.grupo_id == group_id,
        DBDocenteMateria.activo == True
    ).first()
    if not dm:
        raise HTTPException(status_code=403, detail="Access denied: Group not assigned to teacher")

    horario = db.query(DBHorarioDetalle).filter(DBHorarioDetalle.docente_materia_id == dm.id).first()
    horario_id = horario.id if horario else None

    for entry in payload.attendance:
        inscripcion = db.query(DBInscripcion).filter(
            DBInscripcion.alumno_id == entry.student_id,
            DBInscripcion.docente_materia_id == dm.id
        ).first()
        if not inscripcion:
            continue

        asistencia = db.query(DBAsistencia).filter(
            DBAsistencia.inscripcion_id == inscripcion.id,
            DBAsistencia.fecha == payload.date
        ).order_by(DBAsistencia.created_at.desc()).first()

        if asistencia:
            asistencia.presente = (entry.status == "presente")
        else:
            db.add(DBAsistencia(
                inscripcion_id=inscripcion.id,
                horario_detalle_id=horario_id,
                fecha=payload.date,
                presente=(entry.status == "presente"),
                retardo=False,
                justificada=False
            ))

    db.commit()
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={
        "detail": "Internal server error",
        "error": str(exc)
    })
@app.get("/debug/cors")
def debug_cors():
    return {
        "allowed_origins": allowed_origins,
        "allow_origin_regex": allow_origin_regex
    }
