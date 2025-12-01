from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

class UserLogin(BaseModel):
    email: str
    password: str

class Carrera(BaseModel):
    id: int
    nombre: str
    numero_cuatrimestres: Optional[int] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlanEstudio(BaseModel):
    id: int
    nombre: str
    carrera: Carrera

    class Config:
        from_attributes = True

class Alumno(BaseModel):
    id: int
    matricula: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    email: str
    cuatrimestre_actual: Optional[int] = None
    promedio_general: Optional[float] = None
    plan_estudio: Optional[PlanEstudio] = None

    class Config:
        from_attributes = True

class Extracurricular(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    activo: bool

    class Config:
        from_attributes = True

class AlumnoExtracurricular(BaseModel):
    id: int
    fecha_inscripcion: datetime
    calificacion: Optional[float] = None
    horas_cumplidas: int
    completado: bool
    fecha_completado: Optional[datetime] = None
    extracurricular: Extracurricular

    class Config:
        from_attributes = True

class MateriaSchema(BaseModel):
    nombre: str

    class Config:
        from_attributes = True

class GrupoSchema(BaseModel):
    nombre: str

    class Config:
        from_attributes = True

class Calificacion(BaseModel):
    materia: MateriaSchema
    calificacion_parcial1: Optional[float] = None
    calificacion_parcial2: Optional[float] = None
    calificacion_parcial3: Optional[float] = None
    promedio_final: Optional[float] = None

    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class VerificationKeyUpdate(BaseModel):
    current_verification_key: str
    new_verification_key: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class User(BaseModel):
    nombre: str
    email: str
    calle: Optional[str] = None
    num_ext: Optional[str] = None
    num_int: Optional[str] = None
    colonia: Optional[str] = None
    codigo_postal: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    telefono: Optional[str] = None
    ciclo_escolar: Optional[str] = None
    nivel_estudios: Optional[str] = None
    carrera: Optional[str] = None
    semestre_grupo: Optional[str] = None
    cursa_actualmente: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: str
    calle: Optional[str] = None
    num_ext: Optional[str] = None
    num_int: Optional[str] = None
    colonia: Optional[str] = None
    codigo_postal: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    telefono: Optional[str] = None

class Documento(BaseModel):
    clave_doc: str
    nombre: str
    entregado: bool
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True

class Profesor(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class EvaluacionCreate(BaseModel):
    profesor_id: int
    calificacion: int

class Inscripcion(BaseModel):
    materia: MateriaSchema
    calificacion_parcial1: Optional[float]
    calificacion_parcial2: Optional[float]
    calificacion_parcial3: Optional[float]
    promedio_final: Optional[float]

    class Config:
        from_attributes = True
