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
