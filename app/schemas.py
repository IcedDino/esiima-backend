from pydantic import BaseModel
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
