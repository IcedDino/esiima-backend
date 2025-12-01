from sqlalchemy import (Column, Integer, String, Boolean, Float, Text, JSON, 
                        ForeignKey, DateTime, Date, Time, Index, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Forward declarations for relationships
class Alumno(Base):
    __tablename__ = 'alumnos'
    id = Column(Integer, primary_key=True)
    matricula = Column(String(255), unique=True, nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    apellido_paterno = Column(String(255), nullable=False)
    apellido_materno = Column(String(255))
    fecha_nacimiento = Column(Date)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_institucional = Column(String(255), unique=True)
    telefono = Column(String(255))
    celular = Column(String(255))
    curp = Column(String(255), unique=True, index=True)
    plan_estudio_id = Column(Integer, ForeignKey("planes_estudio.id"))
    cuatrimestre_actual = Column(Integer)
    estatus_id = Column(Integer, ForeignKey("cat_estatus_alumnos.id"), nullable=False, index=True)
    fecha_ingreso = Column(Date, nullable=False)
    fecha_egreso = Column(Date, nullable=True)
    porcentaje_beca = Column(Float, default=0)
    promedio_general = Column(Float, nullable=True)
    creditos_cursados = Column(Integer, default=0)
    creditos_aprobados = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    calle = Column(String(255))
    num_ext = Column(String(255))
    num_int = Column(String(255))
    colonia = Column(String(255))
    codigo_postal = Column(String(255))
    municipio = Column(String(255))
    estado = Column(String(255))
    ciclo_escolar = Column(String(255))
    nivel_estudios = Column(String(255))
    semestre_grupo = Column(String(255))
    cursa_actualmente = Column(String(255))

    usuario = relationship("Usuario", back_populates="alumno", uselist=False)
    plan_estudio = relationship("PlanEstudio")
    estatus = relationship("CatEstatusAlumnos")

class Docente(Base):
    __tablename__ = 'docentes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    apellido_paterno = Column(String(255), nullable=False)
    apellido_materno = Column(String(255))
    email = Column(String(255), unique=True, nullable=False, index=True)
    telefono = Column(String(255))
    celular = Column(String(255))
    especialidad = Column(String(255))
    grado_academico = Column(String(255))
    cedula_profesional = Column(String(255), unique=True, index=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario", back_populates="docente", uselist=False)

# ============================================
# CATALOG TABLES (LOOKUP TABLES)
# ============================================

class CatRoles(Base):
    __tablename__ = "cat_roles"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))
    permisos = Column(JSON)
    activo = Column(Boolean, default=True)

class CatEstatusAlumnos(Base):
    __tablename__ = "cat_estatus_alumnos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))
    es_baja = Column(Boolean, default=False)
    orden = Column(Integer)

class CatConceptosPago(Base):
    __tablename__ = "cat_conceptos_pago"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))
    monto_default = Column(Float, nullable=True)
    activo = Column(Boolean, default=True)

class CatTiposDocumento(Base):
    __tablename__ = "cat_tipos_documento"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))
    obligatorio = Column(Boolean, default=False)
    formato_aceptado = Column(String(255))
    tamano_max_mb = Column(Integer, default=5)
    activo = Column(Boolean, default=True)

class CatEstatusDocumento(Base):
    __tablename__ = "cat_estatus_documento"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))

class CatEstatusInscripcion(Base):
    __tablename__ = "cat_estatus_inscripcion"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))

class CatEstatusKardex(Base):
    __tablename__ = "cat_estatus_kardex"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))

class CatEstatusPago(Base):
    __tablename__ = "cat_estatus_pago"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))

class CatMetodosPago(Base):
    __tablename__ = "cat_metodos_pago"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))
    activo = Column(Boolean, default=True)

class CatEstatusServicio(Base):
    __tablename__ = "cat_estatus_servicio"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))

class CatTiposNotificacion(Base):
    __tablename__ = "cat_tipos_notificacion"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))
    plantilla_mensaje = Column(Text)

class CatTiposEventoCalendario(Base):
    __tablename__ = "cat_tipos_evento_calendario"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    descripcion = Column(String(255))
    color = Column(String(255))

# ============================================
# CORE ACADEMIC STRUCTURE
# ============================================

class Carrera(Base):
    __tablename__ = "carreras"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    numero_cuatrimestres = Column(Integer)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PlanEstudio(Base):
    __tablename__ = "planes_estudio"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date, nullable=True)
    carrera_id = Column(Integer, ForeignKey("carreras.id"))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    carrera = relationship("Carrera")

class Materia(Base):
    __tablename__ = "materias"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    clave = Column(String(255), unique=True, index=True)
    cuatrimestre = Column(Integer)
    creditos = Column(Integer)
    horas_teoricas = Column(Integer)
    horas_practicas = Column(Integer)
    es_optativa = Column(Boolean, default=False)
    plan_estudio_id = Column(Integer, ForeignKey("planes_estudio.id"))
    activo = Column(Boolean, default=True)
    faltas_permitidas = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    plan_estudio = relationship("PlanEstudio")
    __table_args__ = (Index("idx_materias_plan_cuatrimestre", "plan_estudio_id", "cuatrimestre"),)

class Prerequisito(Base):
    __tablename__ = "prerequisitos"
    id = Column(Integer, primary_key=True)
    materia_id = Column(Integer, ForeignKey("materias.id"))
    materia_prerequisito_id = Column(Integer, ForeignKey("materias.id"))
    es_requisito_estricto = Column(Boolean, default=True)
    materia = relationship("Materia", foreign_keys="Prerequisito.materia_id")
    materia_prerequisito = relationship("Materia", foreign_keys="Prerequisito.materia_prerequisito_id")
    __table_args__ = (UniqueConstraint("materia_id", "materia_prerequisito_id", name="uq_prerequisitos_materia_prereq"),)

class Periodo(Base):
    __tablename__ = "periodos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False, unique=True, index=True)
    anio = Column(Integer, nullable=False)
    periodo = Column(String(255), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    activo = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("anio", "periodo", name="uq_periodos_anio_periodo"),)

class Grupo(Base):
    __tablename__ = "grupos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    carrera_id = Column(Integer, ForeignKey("carreras.id"))
    cuatrimestre = Column(Integer, nullable=False)
    plan_estudio_id = Column(Integer, ForeignKey("planes_estudio.id"))
    periodo_id = Column(Integer, ForeignKey("periodos.id"))
    cupo_maximo = Column(Integer)
    cupo_actual = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    carrera = relationship("Carrera")
    plan_estudio = relationship("PlanEstudio")
    periodo = relationship("Periodo")
    __table_args__ = (UniqueConstraint("carrera_id", "periodo_id", "cuatrimestre", "nombre", name="uq_grupos_carrera_periodo_cuatri_nombre"),)

# ============================================
# USERS & AUTHENTICATION
# ============================================

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("cat_roles.id"), nullable=False, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=True, index=True)
    docente_id = Column(Integer, ForeignKey("docentes.id"), nullable=True, index=True)
    activo = Column(Boolean, default=True)
    ultimo_acceso = Column(DateTime(timezone=True))
    debe_cambiar_password = Column(Boolean, default=True)
    verification_key_hash = Column(String(255), nullable=True)
    debe_cambiar_clave_verificacion = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    rol = relationship("CatRoles")
    alumno = relationship("Alumno", back_populates="usuario", uselist=False)
    docente = relationship("Docente", back_populates="usuario", uselist=False)

# ============================================
# STUDENTS
# ============================================

# ============================================
# TEACHERS
# ============================================

# ============================================
# CLASS SECTIONS (SECCIONES)
# ============================================

class DocenteMateria(Base):
    __tablename__ = "docente_materia"
    id = Column(Integer, primary_key=True)
    docente_id = Column(Integer, ForeignKey("docentes.id"))
    materia_id = Column(Integer, ForeignKey("materias.id"))
    grupo_id = Column(Integer, ForeignKey("grupos.id"))
    periodo_id = Column(Integer, ForeignKey("periodos.id"))
    cupo_maximo = Column(Integer, nullable=True)
    cupo_actual = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    docente = relationship("Docente")
    materia = relationship("Materia")
    grupo = relationship("Grupo")
    periodo = relationship("Periodo")
    __table_args__ = (
        UniqueConstraint("docente_id", "materia_id", "grupo_id", "periodo_id", name="uq_docente_materia_periodo"),
        Index("idx_docente_materia_grupo_materia_periodo", "grupo_id", "materia_id", "periodo_id"),
    )

class HorarioDetalle(Base):
    __tablename__ = "horarios_detalle"
    id = Column(Integer, primary_key=True)
    docente_materia_id = Column(Integer, ForeignKey("docente_materia.id"))
    dia_semana = Column(Integer, nullable=False)
    horario_inicio = Column(Time, nullable=False)
    horario_fin = Column(Time, nullable=False)
    aula = Column(String(255))
    edificio = Column(String(255))
    docente_materia = relationship("DocenteMateria")
    __table_args__ = (
        UniqueConstraint("docente_materia_id", "dia_semana", "horario_inicio", name="uq_horario_detalle_docente_materia_dia_inicio"),
        Index("idx_horario_detalle_aula_dia_inicio", "aula", "dia_semana", "horario_inicio"),
    )

# ============================================
# ENROLLMENTS & GRADES
# ============================================

class Inscripcion(Base):
    __tablename__ = "inscripciones"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    docente_materia_id = Column(Integer, ForeignKey("docente_materia.id"))
    fecha_inscripcion = Column(DateTime(timezone=True), server_default=func.now())
    estatus_id = Column(Integer, ForeignKey("cat_estatus_inscripcion.id"), nullable=False)
    fecha_baja = Column(DateTime(timezone=True), nullable=True)
    motivo_baja = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    alumno = relationship("Alumno")
    docente_materia = relationship("DocenteMateria")
    estatus = relationship("CatEstatusInscripcion")
    __table_args__ = (
        UniqueConstraint("alumno_id", "docente_materia_id", name="uq_inscripciones_alumno_docente_materia"),
        Index("idx_inscripciones_docente_materia_id", "docente_materia_id"),
        Index("idx_inscripciones_estatus_id", "estatus_id"),
    )

class Kardex(Base):
    __tablename__ = "kardex"
    id = Column(Integer, primary_key=True)
    inscripcion_id = Column(Integer, ForeignKey("inscripciones.id"), unique=True)
    intento = Column(Integer, default=1)
    calificacion_final = Column(Float, nullable=True)
    aprobado = Column(Boolean, nullable=True)
    estatus_id = Column(Integer, ForeignKey("cat_estatus_kardex.id"), nullable=False)
    publicado_visible_alumno = Column(Boolean, default=False)
    fecha_captura = Column(DateTime(timezone=True), nullable=True)
    fecha_publicacion = Column(DateTime(timezone=True), nullable=True)
    observaciones = Column(Text)
    tipo_examen = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    inscripcion = relationship("Inscripcion")
    estatus = relationship("CatEstatusKardex")
    __table_args__ = (
        Index("idx_kardex_inscripcion_id", "inscripcion_id"),
        Index("idx_kardex_estatus_id", "estatus_id"),
    )

class CalificacionParcial(Base):
    __tablename__ = "calificaciones_parciales"
    id = Column(Integer, primary_key=True)
    kardex_id = Column(Integer, ForeignKey("kardex.id"))
    unidad = Column(Integer, nullable=False)
    calificacion = Column(Float)
    porcentaje_peso = Column(Float)
    fecha_captura = Column(DateTime(timezone=True), server_default=func.now())
    publicado = Column(Boolean, default=False)
    kardex = relationship("Kardex")
    __table_args__ = (UniqueConstraint("kardex_id", "unidad", name="uq_calificaciones_parciales_kardex_unidad"),)

class Asistencia(Base):
    __tablename__ = "asistencias"
    id = Column(Integer, primary_key=True)
    inscripcion_id = Column(Integer, ForeignKey("inscripciones.id"))
    horario_detalle_id = Column(Integer, ForeignKey("horarios_detalle.id"))
    fecha = Column(Date, nullable=False)
    presente = Column(Boolean, default=False)
    retardo = Column(Boolean, default=False)
    justificada = Column(Boolean, default=False)
    observaciones = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    inscripcion = relationship("Inscripcion")
    horario_detalle = relationship("HorarioDetalle")
    __table_args__ = (
        UniqueConstraint("inscripcion_id", "fecha", "horario_detalle_id", name="uq_asistencias_inscripcion_fecha_horario"),
        Index("idx_asistencias_horario_detalle_fecha", "horario_detalle_id", "fecha"),
    )

# ============================================
# ENROLLMENT PERIODS
# ============================================

class PeriodoInscripcion(Base):
    __tablename__ = "periodos_inscripcion"
    id = Column(Integer, primary_key=True)
    periodo_id = Column(Integer, ForeignKey("periodos.id"))
    carrera_id = Column(Integer, ForeignKey("carreras.id"))
    cuatrimestre = Column(Integer)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    activo = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    periodo = relationship("Periodo")
    carrera = relationship("Carrera")
    __table_args__ = (UniqueConstraint("periodo_id", "carrera_id", "cuatrimestre", name="uq_periodos_inscripcion_periodo_carrera_cuatri"),)

# ============================================
# PAYMENTS
# ============================================

class Pago(Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    periodo_id = Column(Integer, ForeignKey("periodos.id"))
    concepto_id = Column(Integer, ForeignKey("cat_conceptos_pago.id"), nullable=False)
    monto = Column(Float, nullable=False)
    descuento_beca = Column(Float, default=0)
    otros_descuentos = Column(Float, default=0)
    monto_total = Column(Float, nullable=False)
    monto_pagado = Column(Float, default=0)
    fecha_vencimiento = Column(Date)
    fecha_pago = Column(DateTime(timezone=True), nullable=True)
    estatus_id = Column(Integer, ForeignKey("cat_estatus_pago.id"), nullable=False)
    metodo_pago_id = Column(Integer, ForeignKey("cat_metodos_pago.id"), nullable=True)
    referencia = Column(String(255), nullable=True)
    comprobante_url = Column(String(255), nullable=True)
    notas = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    alumno = relationship("Alumno")
    periodo = relationship("Periodo")
    concepto = relationship("CatConceptosPago")
    estatus = relationship("CatEstatusPago")
    metodo_pago = relationship("CatMetodosPago")
    __table_args__ = (
        Index("idx_pagos_alumno_periodo", "alumno_id", "periodo_id"),
        Index("idx_pagos_estatus_id", "estatus_id"),
        Index("idx_pagos_fecha_vencimiento", "fecha_vencimiento"),
    )

# ============================================
# DOCUMENTS
# ============================================

class Documento(Base):
    __tablename__ = "documentos"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    tipo_id = Column(Integer, ForeignKey("cat_tipos_documento.id"), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(255), nullable=False)
    tamano_bytes = Column(Integer)
    mime_type = Column(String(255))
    fecha_subida = Column(DateTime(timezone=True), server_default=func.now())
    estatus_id = Column(Integer, ForeignKey("cat_estatus_documento.id"), nullable=False)
    comentarios = Column(Text, nullable=True)
    revisado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_revision = Column(DateTime(timezone=True), nullable=True)
    alumno = relationship("Alumno")
    tipo = relationship("CatTiposDocumento")
    estatus = relationship("CatEstatusDocumento")
    revisado_por = relationship("Usuario")
    __table_args__ = (
        Index("idx_documentos_alumno_tipo", "alumno_id", "tipo_id"),
        Index("idx_documentos_estatus_id", "estatus_id"),
    )

# ============================================
# EXTRACURRICULAR ACTIVITIES
# ============================================

class Extracurricular(Base):
    __tablename__ = "extracurriculares"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(255))
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    cupo_maximo = Column(Integer)
    cupo_actual = Column(Integer, default=0)
    responsable_id = Column(Integer, ForeignKey("docentes.id"), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    responsable = relationship("Docente")

class AlumnoExtracurricular(Base):
    __tablename__ = "alumno_extracurriculares"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    extracurricular_id = Column(Integer, ForeignKey("extracurriculares.id"))
    fecha_inscripcion = Column(DateTime(timezone=True), server_default=func.now())
    calificacion = Column(Float, nullable=True)
    horas_cumplidas = Column(Integer, default=0)
    completado = Column(Boolean, default=False)
    fecha_completado = Column(DateTime(timezone=True), nullable=True)
    alumno = relationship("Alumno")
    extracurricular = relationship("Extracurricular")
    __table_args__ = (UniqueConstraint("alumno_id", "extracurricular_id", name="uq_alumno_extracurricular"),)

# ============================================
# SOCIAL SERVICE & INTERNSHIPS
# ============================================

class ServicioSocial(Base):
    __tablename__ = "servicio_social"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), index=True)
    institucion = Column(String(255), nullable=False)
    dependencia = Column(String(255))
    programa = Column(String(255))
    descripcion = Column(Text)
    horas_requeridas = Column(Integer, default=480)
    horas_cumplidas = Column(Integer, default=0)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date, nullable=True)
    estatus_id = Column(Integer, ForeignKey("cat_estatus_servicio.id"), nullable=False, index=True)
    documento_url = Column(String(255), nullable=True)
    carta_aceptacion_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    alumno = relationship("Alumno")
    estatus = relationship("CatEstatusServicio")

class PracticasProfesionales(Base):
    __tablename__ = "practicas_profesionales"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), index=True)
    empresa = Column(String(255), nullable=False)
    puesto = Column(String(255))
    area = Column(String(255))
    descripcion = Column(Text)
    horas_requeridas = Column(Integer, default=300)
    horas_cumplidas = Column(Integer, default=0)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date, nullable=True)
    estatus_id = Column(Integer, ForeignKey("cat_estatus_servicio.id"), nullable=False, index=True)
    documento_url = Column(String(255), nullable=True)
    carta_aceptacion_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    alumno = relationship("Alumno")
    estatus = relationship("CatEstatusServicio")

# ============================================
# GRADUATION REQUIREMENTS
# ============================================

class TitulacionRequisito(Base):
    __tablename__ = "titulacion_requisitos"
    id = Column(Integer, primary_key=True)
    plan_estudio_id = Column(Integer, ForeignKey("planes_estudio.id"))
    carrera_id = Column(Integer, ForeignKey("carreras.id"))
    requisito = Column(String(255), nullable=False)
    descripcion = Column(Text)
    obligatorio = Column(Boolean, default=True)
    orden = Column(Integer)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    plan_estudio = relationship("PlanEstudio")
    carrera = relationship("Carrera")
    __table_args__ = (Index("idx_titulacion_requisitos_plan_orden", "plan_estudio_id", "orden"),)

class AlumnoTitulacion(Base):
    __tablename__ = "alumno_titulacion"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    requisito_id = Column(Integer, ForeignKey("titulacion_requisitos.id"))
    cumplido = Column(Boolean, default=False)
    fecha_cumplimiento = Column(Date, nullable=True)
    documento_url = Column(String(255), nullable=True)
    observaciones = Column(Text)
    validado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_validacion = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    alumno = relationship("Alumno")
    requisito = relationship("TitulacionRequisito")
    validado_por = relationship("Usuario")
    __table_args__ = (UniqueConstraint("alumno_id", "requisito_id", name="uq_alumno_titulacion_requisito"),)

# ============================================
# ALUMNI
# ============================================

class Alumni(Base):
    __tablename__ = "alumni"
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), unique=True, index=True)
    empresa_actual = Column(String(255))
    puesto_actual = Column(String(255))
    sector_industria = Column(String(255))
    salario_rango = Column(String(255))
    linkedin = Column(String(255))
    email_personal = Column(String(255))
    telefono_personal = Column(String(255))
    direccion_actual = Column(Text)
    acepta_contacto = Column(Boolean, default=False)
    disponible_mentoria = Column(Boolean, default=False)
    biografia = Column(Text)
    foto_url = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    alumno = relationship("Alumno")

class EventoAlumni(Base):
    __tablename__ = "eventos_alumni"
    id = Column(Integer, primary_key=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    fecha_evento = Column(DateTime, nullable=False)
    ubicacion = Column(String(255))
    modalidad = Column(String(255))
    url_virtual = Column(String(255), nullable=True)
    cupo_maximo = Column(Integer, nullable=True)
    cupo_actual = Column(Integer, default=0)
    costo = Column(Float, default=0)
    requiere_registro = Column(Boolean, default=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InscripcionEvento(Base):
    __tablename__ = "inscripciones_eventos"
    id = Column(Integer, primary_key=True)
    evento_id = Column(Integer, ForeignKey("eventos_alumni.id"))
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    fecha_inscripcion = Column(DateTime(timezone=True), server_default=func.now())
    asistio = Column(Boolean, nullable=True)
    cancelado = Column(Boolean, default=False)
    fecha_cancelacion = Column(DateTime(timezone=True), nullable=True)
    evento = relationship("EventoAlumni")
    alumno = relationship("Alumno")
    __table_args__ = (UniqueConstraint("evento_id", "alumno_id", name="uq_inscripciones_eventos_evento_alumno"),)

# ============================================
# NOTIFICATIONS
# ============================================

class Notificacion(Base):
    __tablename__ = "notificaciones"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    tipo_id = Column(Integer, ForeignKey("cat_tipos_notificacion.id"), nullable=False, index=True)
    titulo = Column(String(255), nullable=False)
    mensaje = Column(Text, nullable=False)
    url = Column(String(255), nullable=True)
    prioridad = Column(String(255), default='normal')
    leida = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_lectura = Column(DateTime(timezone=True), nullable=True)
    fecha_expiracion = Column(DateTime(timezone=True), nullable=True)
    usuario = relationship("Usuario")
    tipo = relationship("CatTiposNotificacion")
    __table_args__ = (Index("idx_notificaciones_usuario_leida_fecha", "usuario_id", "leida", "fecha_creacion"),)

# ============================================
# AUDIT LOG
# ============================================

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    tabla = Column(String(255), nullable=False)
    registro_id = Column(Integer, nullable=False)
    accion = Column(String(255), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    datos_anteriores = Column(JSON, nullable=True)
    datos_nuevos = Column(JSON, nullable=True)
    ip_address = Column(String(255))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    usuario = relationship("Usuario")
    __table_args__ = (
        Index("idx_audit_log_tabla_registro_fecha", "tabla", "registro_id", "created_at"),
        Index("idx_audit_log_usuario_fecha", "usuario_id", "created_at"),
    )

# ============================================
# ACADEMIC CALENDAR
# ============================================

class CalendarioAcademico(Base):
    __tablename__ = "calendario_academico"
    id = Column(Integer, primary_key=True)
    periodo_id = Column(Integer, ForeignKey("periodos.id"))
    tipo_id = Column(Integer, ForeignKey("cat_tipos_evento_calendario.id"), nullable=False, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)
    aplica_carreras = Column(JSON, nullable=True)
    todo_el_dia = Column(Boolean, default=True)
    hora_inicio = Column(Time, nullable=True)
    hora_fin = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    periodo = relationship("Periodo")
    tipo = relationship("CatTiposEventoCalendario")
    __table_args__ = (Index("idx_calendario_academico_periodo_fecha", "periodo_id", "fecha_inicio"),)

class Evaluacion(Base):
    __tablename__ = 'evaluaciones'
    id = Column(Integer, primary_key=True)
    profesor_id = Column(Integer, ForeignKey('docentes.id'), nullable=False)
    alumno_id = Column(Integer, ForeignKey('alumnos.id'), nullable=False)
    materia_id = Column(Integer, ForeignKey('materias.id'), nullable=False)
    calificacion = Column(Integer, nullable=False)
    
    profesor = relationship("Docente")
    alumno = relationship("Alumno")
    materia = relationship("Materia")
