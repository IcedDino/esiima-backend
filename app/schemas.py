from pydantic import BaseModel, Field
from typing import List, Optional, Dict
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
    id: int
    nombre: str
    faltas_permitidas: Optional[int] = None

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
    promedio_semestral: Optional[float] = None

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
    materia: str
    materia_id: int

    class Config:
        from_attributes = True

class EvaluacionCreate(BaseModel):
    profesor_id: int
    materia_id: int
    calificacion: int

class Inscripcion(BaseModel):
    materia: MateriaSchema
    calificacion_parcial1: Optional[float]
    calificacion_parcial2: Optional[float]
    calificacion_parcial3: Optional[float]
    promedio_final: Optional[float]

    class Config:
        from_attributes = True

class ServicioSocial(BaseModel):
    institucion: str
    dependencia: str
    programa: str
    horas_requeridas: int
    horas_cumplidas: int
    fecha_inicio: date
    fecha_fin: date
    estatus_id: int
    documento_url: Optional[str] = None
    carta_aceptacion_url: Optional[str] = None

    class Config:
        from_attributes = True

class PracticasProfesionales(BaseModel):
    empresa: str
    puesto: str
    area: str
    horas_requeridas: int
    horas_cumplidas: int
    fecha_inicio: date
    fecha_fin: date
    estatus_id: int
    documento_url: Optional[str] = None
    carta_aceptacion_url: Optional[str] = None

    class Config:
        from_attributes = True

class KardexEntry(BaseModel):
    clave: str
    materia: str
    oports_agotadas: int
    alto_riesgo: bool
    periodo: str
    calificacion: Optional[float]
    tipo_examen: Optional[str]
    id: int # Added materia ID for frontend detail link

    class Config:
        from_attributes = True

class MateriaFaltas(BaseModel):
    id: int
    horas_semana: int
    nombre: str
    semestre: int
    grupo: str
    faltas_permitidas: Optional[int]
    total_faltas: int
    horas_teoricas: int
    horas_practicas: int

    class Config:
        from_attributes = True

class Examen(BaseModel):
    materia: str
    semestre: int
    calificacion: Optional[float]
    maestro: str
    lugar_fecha_hora: str

    class Config:
        from_attributes = True

class Horario(BaseModel):
    hora: str
    LUNES: Optional[str] = None
    MARTES: Optional[str] = None
    MIERCOLES: Optional[str] = None
    JUEVES: Optional[str] = None
    VIERNES: Optional[str] = None
    SABADO: Optional[str] = None

    class Config:
        from_attributes = True

class MateriaNoAprobada(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class SolicitudCreate(BaseModel):
    materias: List[int]

class RequisitoTitulacion(BaseModel):
    nombre: str
    unidades_a_cubrir: int
    tipo_unidad: str
    unidades_cubiertas: int

    class Config:
        from_attributes = True

class FaltaDetalle(BaseModel):
    fecha: date

    class Config:
        from_attributes = True

class PartialGrade(BaseModel):
    parcial: int = Field(..., alias="unidad")
    calificacion: Optional[float]

    class Config:
        from_attributes = True
        populate_by_name = True
