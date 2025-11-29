#!/usr/bin/env python3
"""
seed_all.py
Full single-file seeder for the entire schema provided by the user.
MySQL-compatible. Medium dataset.
Run: python seed_all.py
"""

import sys
import random
import math
from datetime import date, datetime, timedelta, time
from collections import defaultdict

from faker import Faker
fake = Faker("es_MX")

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from sqlalchemy import text

# Adjust imports to match your project structure:
from app.database import engine, Base
from app.models import *  # noqa: F401,F403
from app.auth import get_password_hash

# ---------------------------
# CONFIG (medium dataset)
# ---------------------------
CONFIG = {
    "ALUMNOS": 200,
    "DOCENTES": 30,
    "CARRERAS": 3,
    "PLANES_PER_CARRERA": 1,
    "MATERIAS_PER_PLAN": 36,
    "PERIODOS": 4,
    "GROUPS_PER_CUATRIMESTRE": 2,  # groups per cuatri per carrera
    "EXTRACURRICULARES": 10,
    "EVENTOS_ALUMNI": 8,
}

# ---------------------------
# HELPERS
# ---------------------------

def unique_email_generator(existing_set):
    """Return an email that is unique within existing_set"""
    while True:
        name = fake.user_name()
        suffix = random.randint(100, 999999)
        e = f"{name}{suffix}@example.com"
        if e not in existing_set:
            existing_set.add(e)
            return e

def unique_matricula_generator(existing_set):
    while True:
        m = f"M{random.randint(100000, 999999)}"
        if m not in existing_set:
            existing_set.add(m)
            return m

def unique_curp_generator(existing_set):
    while True:
        # not a real CURP algorithm, but unique-looking
        curp = fake.lexify(text='????######??????').upper()
        if curp not in existing_set:
            existing_set.add(curp)
            return curp

def unique_cedula_generator(existing_set):
    while True:
        c = f"CED{random.randint(1000000, 9999999)}"
        if c not in existing_set:
            existing_set.add(c)
            return c

def unique_clave_materia(existing_set):
    while True:
        clave = f"MAT-{random.randint(1000,99999)}"
        if clave not in existing_set:
            existing_set.add(clave)
            return clave

def get_or_create(session, model, defaults=None, **kwargs):
    """
    Safe create for unique catalog rows.
    Returns the instance (existing or newly created).
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    session.commit()
    return instance

def exists_unique_constraint(session, model, **kwargs):
    return session.query(model).filter_by(**kwargs).first() is not None

# ---------------------------
# CLEAR DB
# ---------------------------

def clear_database(session: Session):
    """
    Drops all tables defined in the Base metadata.
    """
    print("⚠️  Dropping all tables...")
    # drop_all issues DROP TABLE statements for all tables
    # It respects foreign key constraints for ordering.
    Base.metadata.drop_all(session.bind)
    print("✔ All tables dropped.\n")


# ---------------------------
# SEED CATALOGS
# ---------------------------

def seed_catalogs(session: Session):
    print("Seeding catalog tables...")
    # Roles
    r_admin = get_or_create(session, CatRoles, nombre="admin", defaults={"descripcion": "Administrador", "permisos": {}, "activo": True})
    r_alumno = get_or_create(session, CatRoles, nombre="alumno", defaults={"descripcion": "Alumno", "permisos": {}, "activo": True})
    r_docente = get_or_create(session, CatRoles, nombre="docente", defaults={"descripcion": "Docente", "permisos": {}, "activo": True})

    # Estatus alumnos
    get_or_create(session, CatEstatusAlumnos, nombre="Activo", defaults={"descripcion":"Alumno activo", "es_baja": False, "orden": 1})
    get_or_create(session, CatEstatusAlumnos, nombre="Baja Temporal", defaults={"descripcion":"Baja temporal", "es_baja": True, "orden": 2})
    get_or_create(session, CatEstatusAlumnos, nombre="Egresado", defaults={"descripcion":"Egresado", "es_baja": False, "orden": 3})

    # Conceptos pago
    get_or_create(session, CatConceptosPago, nombre="Inscripción", defaults={"descripcion":"Pago de inscripción", "monto_default":1500, "activo":True})
    get_or_create(session, CatConceptosPago, nombre="Mensualidad", defaults={"descripcion":"Pago mensual", "monto_default":1200, "activo":True})
    get_or_create(session, CatConceptosPago, nombre="Examen Extraordinario", defaults={"descripcion":"Examen extra", "monto_default":450, "activo":True})

    # Tipos de documento
    get_or_create(session, CatTiposDocumento, nombre="INE", defaults={"descripcion":"Identificación oficial", "obligatorio":True, "formato_aceptado":"pdf,jpg", "tamano_max_mb":5, "activo":True})
    get_or_create(session, CatTiposDocumento, nombre="Acta Nacimiento", defaults={"descripcion":"Acta de nacimiento", "obligatorio":True, "formato_aceptado":"pdf,jpg", "activo":True})

    # Estatus documento
    get_or_create(session, CatEstatusDocumento, nombre="Pendiente", defaults={"descripcion":"Pendiente de revisión"})
    get_or_create(session, CatEstatusDocumento, nombre="Aprobado", defaults={"descripcion":"Documento aprobado"})
    get_or_create(session, CatEstatusDocumento, nombre="Rechazado", defaults={"descripcion":"Documento rechazado"})

    # Estatus inscripcion
    get_or_create(session, CatEstatusInscripcion, nombre="Inscrito", defaults={"descripcion":"Inscrito"})
    get_or_create(session, CatEstatusInscripcion, nombre="Baja", defaults={"descripcion":"Baja"})

    # Estatus kardex
    get_or_create(session, CatEstatusKardex, nombre="Capturado", defaults={"descripcion":"Calificación capturada"})
    get_or_create(session, CatEstatusKardex, nombre="Publicada", defaults={"descripcion":"Calificación publicada"})

    # Estatus pago
    get_or_create(session, CatEstatusPago, nombre="Pendiente", defaults={"descripcion":"Pago pendiente"})
    get_or_create(session, CatEstatusPago, nombre="Pagado", defaults={"descripcion":"Pago pagado"})
    get_or_create(session, CatEstatusPago, nombre="Vencido", defaults={"descripcion":"Pago vencido"})

    # Metodos pago
    get_or_create(session, CatMetodosPago, nombre="Tarjeta", defaults={"descripcion":"Pago con tarjeta", "activo":True})
    get_or_create(session, CatMetodosPago, nombre="Efectivo", defaults={"descripcion":"Pago en efectivo", "activo":True})
    get_or_create(session, CatMetodosPago, nombre="Transferencia", defaults={"descripcion":"Transferencia bancaria", "activo":True})

    # Estatus servicio
    get_or_create(session, CatEstatusServicio, nombre="En Proceso", defaults={"descripcion":"En proceso"})
    get_or_create(session, CatEstatusServicio, nombre="Completado", defaults={"descripcion":"Completado"})

    # Tipos notificacion
    get_or_create(session, CatTiposNotificacion, nombre="General", defaults={"descripcion":"Notificación general", "plantilla_mensaje":"{titulo}: {mensaje}"})

    # Tipos evento calendario
    get_or_create(session, CatTiposEventoCalendario, nombre="Examen", defaults={"descripcion":"Examen", "color":"#FF0000"})
    get_or_create(session, CatTiposEventoCalendario, nombre="Registro", defaults={"descripcion":"Periodo de registro", "color":"#00FF00"})

    session.commit()
    print("Catalogs done.\n")

# ---------------------------
# SEED CORE ACADEMIC STRUCTURE
# ---------------------------

def seed_carreras_planes_materias(session: Session):
    print("Seeding carreras, planes y materias...")
    carreras = []
    for i in range(CONFIG["CARRERAS"]):
        nombre = f"Carrera {i+1} - Ciencias Computacionales"
        carrera = get_or_create(session, Carrera, nombre=nombre, defaults={"numero_cuatrimestres":9, "activo":True})
        carreras.append(carrera)

    plans = []
    materias_all = []
    for carrera in carreras:
        for p in range(CONFIG["PLANES_PER_CARRERA"]):
            plan_nombre = f"Plan {carrera.id}-{p+1}"
            plan = get_or_create(session, PlanEstudio, nombre=plan_nombre, defaults={"fecha_inicio": date(2020,1,1), "carrera_id": carrera.id, "activo":True})
            plans.append(plan)

            # Create materias
            materias = []
            mcount = CONFIG["MATERIAS_PER_PLAN"]
            # distribute across 9 cuatrimestres
            cuatri_count = 9
            per_cuatri = math.ceil(mcount / cuatri_count)
            for cuatri in range(1, cuatri_count+1):
                for j in range(per_cuatri):
                    if len(materias) >= mcount:
                        break
                    nombre_m = f"Materia C{carrera.id}P{plan.id} - {cuatri}-{j+1}"
                    clave = unique_clave_materia(session= None) if False else unique_clave_materia  # placeholder; we'll use a set below
                    # actual unique clave using helper set maintained below
                    materias.append({"nombre": nombre_m, "cuatrimestre": cuatri})
            # we will create materias in a loop with global unique set below
            materias_all.append((plan, materias))

    # create materias with unique claves using a set
    used_claves = set()
    created_materia_objs = []
    for plan, materias in materias_all:
        for m in materias:
            clave = unique_clave_materia(used_claves)
            mat = Materia(
                nombre=m["nombre"],
                clave=clave,
                cuatrimestre=m["cuatrimestre"],
                creditos=random.randint(4,8),
                horas_teoricas=random.choice([2,3]),
                horas_practicas=random.choice([1,2]),
                es_optativa=False,
                plan_estudio_id=plan.id,
                activo=True
            )
            session.add(mat)
            created_materia_objs.append(mat)
    session.commit()

    # create prerequisitos (random, avoid self and duplicates)
    materia_objs = session.query(Materia).all()
    materia_ids = [m.id for m in materia_objs]
    created_pairs = set()
    for m in materia_objs:
        # randomly add 0-2 prereqs from earlier cuatrimestres
        possible = [x for x in materia_objs if x.cuatrimestre < m.cuatrimestre and x.plan_estudio_id == m.plan_estudio_id]
        k = random.randint(0, min(2, len(possible)))
        prereq_samples = random.sample(possible, k) if k>0 else []
        for p in prereq_samples:
            key = (m.id, p.id)
            if key not in created_pairs and m.id != p.id:
                pr = Prerequisito(materia_id=m.id, materia_prerequisito_id=p.id, es_requisito_estricto=True)
                try:
                    session.add(pr)
                    session.commit()
                    created_pairs.add(key)
                except Exception:
                    session.rollback()

    print("Carreras, planes, materias & prerequisitos seeded.\n")

# ---------------------------
# SEED PERIODOS & GRUPOS
# ---------------------------

def seed_periodos_grupos(session: Session):
    print("Seeding periodos and groups...")
    periodos = []
    current_year = date.today().year
    for i in range(CONFIG["PERIODOS"]):
        anio = current_year - (CONFIG["PERIODOS"] - 1 - i)
        nombre = f"{anio}-P{i+1}"
        per = get_or_create(session, Periodo,
                            nombre=nombre,
                            defaults={"anio":anio, "periodo": f"P{i+1}", "fecha_inicio": date(anio,1,1), "fecha_fin": date(anio,12,31), "activo": True})
        periodos.append(per)

    carreras = session.query(Carrera).all()
    plans = session.query(PlanEstudio).all()
    grupos_created = []
    for carrera in carreras:
        for period in periodos:
            for cuatri in range(1, 10):
                for g in range(CONFIG["GROUPS_PER_CUATRIMESTRE"]):
                    nombre_gr = f"G{carrera.id}-{cuatri}-{g+1}"
                    # Unique constraint on carrera_id, periodo_id, cuatrimestre, nombre
                    exists = session.query(Grupo).filter_by(carrera_id=carrera.id, periodo_id=period.id, cuatrimestre=cuatri, nombre=nombre_gr).first()
                    if exists:
                        grupos_created.append(exists)
                        continue
                    plan_id = plans[0].id if plans else None
                    gr = Grupo(
                        nombre=nombre_gr,
                        carrera_id=carrera.id,
                        cuatrimestre=cuatri,
                        plan_estudio_id=plan_id,
                        periodo_id=period.id,
                        cupo_maximo=random.randint(20,40),
                        cupo_actual=0,
                        activo=True
                    )
                    session.add(gr)
                    grupos_created.append(gr)
    session.commit()
    print(f"Created {len(grupos_created)} groups.\n")
    return periodos

# ---------------------------
# SEED DOCENTES
# ---------------------------

def seed_docentes(session: Session):
    print("Seeding docentes...")
    used_emails = set([r.email for r in session.query(Docente).all()])  # if prepopulated
    used_cedulas = set([r.cedula_profesional for r in session.query(Docente).all() if r.cedula_profesional])

    docentes = []
    for _ in range(CONFIG["DOCENTES"]):
        email = unique_email_generator(used_emails)
        cedula = unique_cedula_generator(used_cedulas)
        d = Docente(
            nombre=fake.first_name(),
            apellido_paterno=fake.last_name(),
            apellido_materno=fake.last_name(),
            email=email,
            telefono=fake.phone_number(),
            celular=fake.phone_number(),
            especialidad=fake.job(),
            grado_academico=random.choice(["Licenciatura", "Maestría", "Doctorado"]),
            cedula_profesional=cedula,
            activo=True
        )
        session.add(d)
        docentes.append(d)
    session.commit()
    print(f"{len(docentes)} docentes created.\n")
    return docentes

# ---------------------------
# DOCENTE_MATERIA & HORARIOS
# ---------------------------

def seed_docente_materia_horarios(session: Session):
    print("Seeding docente_materia and horarios...")
    docentes = session.query(Docente).all()
    materias = session.query(Materia).all()
    grupos = session.query(Grupo).all()
    periodos = session.query(Periodo).all()

    docente_materia_objs = []
    # assign each materia to some docentes and groups in periods
    for periodo in periodos:
        for materia in materias:
            # pick 1-2 docentes for this materia in this periodo
            k = random.choice([1,1,2])
            chosen_docentes = random.sample(docentes, min(k, len(docentes)))
            for docente in chosen_docentes:
                # pick 1-2 groups matching the materia's plan and some cuatrimestre
                candidate_groups = [g for g in grupos if g.plan_estudio_id == materia.plan_estudio_id and g.cuatrimestre == materia.cuatrimestre and g.periodo_id == periodo.id]
                if not candidate_groups:
                    candidate_groups = random.sample(grupos, min(2, len(grupos)))
                chosen_groups = random.sample(candidate_groups, 1)
                for grp in chosen_groups:
                    exists = session.query(DocenteMateria).filter_by(docente_id=docente.id, materia_id=materia.id, grupo_id=grp.id, periodo_id=periodo.id).first()
                    if exists:
                        docente_materia_objs.append(exists)
                        continue
                    dm = DocenteMateria(
                        docente_id=docente.id,
                        materia_id=materia.id,
                        grupo_id=grp.id,
                        periodo_id=periodo.id,
                        cupo_maximo=random.randint(20,40),
                        cupo_actual=0,
                        activo=True
                    )
                    session.add(dm)
                    docente_materia_objs.append(dm)
    session.commit()

    # horarios: create 1-3 horarios per docente_materia
    dm_list = session.query(DocenteMateria).all()
    for dm in dm_list:
        slots = random.randint(1,2)
        used_slots = set()
        for _ in range(slots):
            dia = random.randint(1,5)  # Mon-Fri
            start_hour = random.randint(8,17)
            start = time(start_hour, 0, 0)
            end = (datetime.combine(date.today(), start) + timedelta(hours=1, minutes=30)).time()
            # ensure uniqueness per constraint: (docente_materia_id,dia,horario_inicio)
            if (dm.id, dia, start) in used_slots:
                continue
            used_slots.add((dm.id, dia, start))
            hd = HorarioDetalle(
                docente_materia_id=dm.id,
                dia_semana=dia,
                horario_inicio=start,
                horario_fin=end,
                aula=f"A{random.randint(1,30)}",
                edificio=random.choice(["A","B","C","D"])
            )
            try:
                session.add(hd)
                session.commit()
            except Exception:
                session.rollback()
    print("DocenteMateria and horarios seeded.\n")

# ---------------------------
# SEED ALUMNOS & USUARIOS
# ---------------------------

def seed_alumnos_usuarios(session: Session):
    print("Seeding alumnos and usuarios...")
    used_emails = set([u.email for u in session.query(Usuario).all()])
    used_matriculas = set([a.matricula for a in session.query(Alumno).all()])
    used_curps = set([a.curp for a in session.query(Alumno).all() if a.curp])

    plan = session.query(PlanEstudio).first()
    estatus = session.query(CatEstatusAlumnos).filter_by(nombre="Activo").first()
    role_alumno = session.query(CatRoles).filter_by(nombre="alumno").first()
    users_created = 0
    alumnos_created = []

    default_password_hash = get_password_hash("password123")
    default_verification_key_hash = get_password_hash("123456")

    for _ in range(CONFIG["ALUMNOS"]):
        email = unique_email_generator(used_emails)
        matricula = unique_matricula_generator(used_matriculas)
        curp = unique_curp_generator(used_curps)
        fn = fake.date_of_birth(minimum_age=17, maximum_age=30)
        alumno = Alumno(
            matricula=matricula,
            nombre=fake.first_name(),
            apellido_paterno=fake.last_name(),
            apellido_materno=fake.last_name(),
            fecha_nacimiento=fn,
            email=email,
            email_institucional=f"{matricula.lower()}@instituto.edu.mx",
            telefono=fake.phone_number(),
            celular=fake.phone_number(),
            curp=curp,
            plan_estudio_id=plan.id if plan else None,
            cuatrimestre_actual=random.randint(1,9),
            estatus_id=estatus.id if estatus else None,
            fecha_ingreso=date(random.randint(2017,2023), random.randint(1,12), random.randint(1,28)),
            porcentaje_beca=random.choice([0,10,25,50]),
            promedio_general=round(random.uniform(6,10),2),
            creditos_cursados=random.randint(0,200),
            creditos_aprobados=random.randint(0,180),
        )
        session.add(alumno)
        session.commit()  # commit to get id
        alumnos_created.append(alumno)

        # create Usuario
        # ensure unique email for usuario
        user_email = unique_email_generator(used_emails)
        usuario = Usuario(
            email=user_email,
            password_hash=default_password_hash,
            rol_id=role_alumno.id if role_alumno else None,
            alumno_id=alumno.id,
            activo=True,
            debe_cambiar_password=True,
            verification_key_hash=default_verification_key_hash,
            debe_cambiar_clave_verificacion=True
        )
        session.add(usuario)
        try:
            session.commit()
            users_created += 1
        except Exception:
            session.rollback()

    print(f"Created {len(alumnos_created)} alumnos and {users_created} usuarios for alumnos.\n")
    return alumnos_created

# ---------------------------
# SEED USUARIOS FOR DOCENTES (if missing)
# ---------------------------

def seed_usuarios_docentes(session: Session):
    print("Seeding usuarios for docentes...")
    role_docente = session.query(CatRoles).filter_by(nombre="docente").first()
    docentes = session.query(Docente).all()
    created = 0
    used_emails = set([u.email for u in session.query(Usuario).all()])
    
    default_password_hash = get_password_hash("password123")
    default_verification_key_hash = get_password_hash("123456")

    for d in docentes:
        # if docente already has usuario (via relationship), skip
        existing = session.query(Usuario).filter_by(docente_id=d.id).first()
        if existing:
            continue
        email = d.email if d.email and d.email not in used_emails else unique_email_generator(used_emails)
        user = Usuario(
            email=email,
            password_hash=default_password_hash,
            rol_id=role_docente.id if role_docente else None,
            docente_id=d.id,
            activo=True,
            debe_cambiar_password=True,
            verification_key_hash=default_verification_key_hash,
            debe_cambiar_clave_verificacion=True
        )
        session.add(user)
        try:
            session.commit()
            created += 1
        except Exception:
            session.rollback()
    print(f"Created {created} usuarios for docentes.\n")

# ---------------------------
# SEED INSCRIPCIONES, KARDEX, CALIFICACIONES, ASISTENCIAS
# ---------------------------

def seed_inscripciones_and_grades(session: Session):
    print("Seeding inscripciones, kardex, calificaciones parciales and asistencias...")
    alumnos = session.query(Alumno).all()
    docente_materias = session.query(DocenteMateria).all()
    estatus_insc = session.query(CatEstatusInscripcion).first()
    estatus_kardex = session.query(CatEstatusKardex).first()

    inscripciones_created = []
    kardex_created = []
    calificaciones_created = 0
    asistencias_created = 0

    # For each alumno, enroll them in 6-10 random docente_materia sections
    for alumno in random.sample(alumnos, min(len(alumnos), CONFIG["ALUMNOS"])):
        k = random.randint(6, 10)
        chosen = random.sample(docente_materias, min(k, len(docente_materias)))
        for dm in chosen:
            # check unique inscripcion (alumno_id, docente_materia_id)
            if session.query(Inscripcion).filter_by(alumno_id=alumno.id, docente_materia_id=dm.id).first():
                continue
            ins = Inscripcion(
                alumno_id=alumno.id,
                docente_materia_id=dm.id,
                estatus_id=estatus_insc.id if estatus_insc else None
            )
            session.add(ins)
            try:
                session.commit()
            except Exception:
                session.rollback()
                continue
            inscripciones_created.append(ins)
            # create kardex for this inscripcion
            if session.query(Kardex).filter_by(inscripcion_id=ins.id).first():
                continue
            kard = Kardex(
                inscripcion_id=ins.id,
                intento=1,
                calificacion_final=None,
                aprobado=None,
                estatus_id=estatus_kardex.id if estatus_kardex else None,
                publicado_visible_alumno=False
            )
            session.add(kard)
            try:
                session.commit()
                kardex_created.append(kard)
            except Exception:
                session.rollback()
                continue
            # create partial calificaciones (3 units)
            for unidad in range(1,4):
                if session.query(CalificacionParcial).filter_by(kardex_id=kard.id, unidad=unidad).first():
                    continue
                cal = CalificacionParcial(
                    kardex_id=kard.id,
                    unidad=unidad,
                    calificacion=round(random.uniform(5,10),2),
                    porcentaje_peso=round(100/3,2),
                    publicado=random.choice([True, False])
                )
                session.add(cal)
                try:
                    session.commit()
                    calificaciones_created += 1
                except Exception:
                    session.rollback()
            # create some asistencias for random horario_detalle entries for this dm
            horarios = session.query(HorarioDetalle).filter_by(docente_materia_id=dm.id).all()
            if horarios:
                # create attendance for 4 random dates
                for _ in range(4):
                    hd = random.choice(horarios)
                    fecha = date.today() - timedelta(days=random.randint(1,100))
                    if session.query(Asistencia).filter_by(inscripcion_id=ins.id, fecha=fecha, horario_detalle_id=hd.id).first():
                        continue
                    a = Asistencia(
                        inscripcion_id=ins.id,
                        horario_detalle_id=hd.id,
                        fecha=fecha,
                        presente=random.choice([True, False]),
                        retardo=random.choice([False, False, True]),
                        justificada=random.choice([False, True]),
                        observaciones=None
                    )
                    session.add(a)
                    try:
                        session.commit()
                        asistencias_created += 1
                    except Exception:
                        session.rollback()

    print(f"Inscripciones: {len(inscripciones_created)}, Kardex: {len(kardex_created)}, Calificaciones: {calificaciones_created}, Asistencias: {asistencias_created}\n")

# ---------------------------
# SEED PAGOS
# ---------------------------

def seed_pagos(session: Session):
    print("Seeding pagos...")
    alumnos = session.query(Alumno).all()
    periodos = session.query(Periodo).all()
    conceptos = session.query(CatConceptosPago).all()
    estatus_pago = session.query(CatEstatusPago).all()
    metodos = session.query(CatMetodosPago).all()

    pagos_created = 0
    for alumno in random.sample(alumnos, min(len(alumnos), 120)):
        periodo = random.choice(periodos)
        concepto = random.choice(conceptos)
        monto = concepto.monto_default if concepto.monto_default else round(random.uniform(500,2000),2)
        descuento = random.choice([0, 0, 0.1, 0.25]) * monto
        total = round(monto - descuento,2)
        estatus = random.choice(estatus_pago)
        metodo = random.choice(metodos)
        pago = Pago(
            alumno_id=alumno.id,
            periodo_id=periodo.id,
            concepto_id=concepto.id,
            monto=monto,
            descuento_beca=round(descuento,2),
            otros_descuentos=0,
            monto_total=total,
            monto_pagado=0 if estatus.nombre=="Pendiente" else total,
            fecha_vencimiento=date.today() + timedelta(days=random.randint(-30,60)),
            fecha_pago=(datetime.now() - timedelta(days=random.randint(0,60))) if estatus.nombre=="Pagado" else None,
            estatus_id=estatus.id,
            metodo_pago_id=metodo.id,
            referencia=f"REF{random.randint(100000,999999)}",
            comprobante_url=None,
            notas=None
        )
        session.add(pago)
        try:
            session.commit()
            pagos_created += 1
        except Exception:
            session.rollback()
    print(f"Pagos created: {pagos_created}\n")

# ---------------------------
# SEED DOCUMENTOS
# ---------------------------

def seed_documentos(session: Session):
    print("Seeding documentos...")
    alumnos = session.query(Alumno).all()
    tipos = session.query(CatTiposDocumento).all()
    estatus_doc = session.query(CatEstatusDocumento).all()
    doc_count = 0
    for alumno in random.sample(alumnos, min(len(alumnos), 150)):
        tipo = random.choice(tipos)
        est = random.choice(estatus_doc)
        nombre_archivo = f"{alumno.matricula}_{tipo.nombre}.pdf" if alumno.matricula else f"{alumno.id}_{tipo.nombre}.pdf"
        doc = Documento(
            alumno_id=alumno.id,
            tipo_id=tipo.id,
            nombre_archivo=nombre_archivo,
            ruta_archivo=f"/files/{nombre_archivo}",
            tamano_bytes=random.randint(1000,2000000),
            mime_type="application/pdf",
            estatus_id=est.id,
            comentarios=None,
            revisado_por_id=None
        )
        session.add(doc)
        try:
            session.commit()
            doc_count += 1
        except Exception:
            session.rollback()
    print(f"Documentos created: {doc_count}\n")

# ---------------------------
# EXTRACURRICULARES
# ---------------------------

def seed_extracurriculars(session: Session):
    print("Seeding extracurriculares and alumno_extracurricular...")
    docentes = session.query(Docente).all()
    alumnos = session.query(Alumno).all()
    created_ex = []
    for i in range(CONFIG["EXTRACURRICULARES"]):
        nombre = f"Extracurricular {i+1}"
        responsable = random.choice(docentes) if docentes else None
        start = date.today() - timedelta(days=random.randint(0,365))
        end = start + timedelta(days=random.randint(30,180))
        ex = Extracurricular(
            nombre=nombre,
            descripcion=fake.text(max_nb_chars=200),
            tipo=random.choice(["Cultural","Deportivo","Académico"]),
            fecha_inicio=start,
            fecha_fin=end,
            cupo_maximo=random.randint(10,100),
            cupo_actual=0,
            responsable_id=responsable.id if responsable else None,
            activo=True
        )
        session.add(ex)
        try:
            session.commit()
            created_ex.append(ex)
        except Exception:
            session.rollback()
    # enroll random alumnos
    ae_count = 0
    for ex in created_ex:
        # enroll 10-30 students
        students = random.sample(alumnos, min(len(alumnos), random.randint(10, min(30, len(alumnos)))))
        for s in students:
            if session.query(AlumnoExtracurricular).filter_by(alumno_id=s.id, extracurricular_id=ex.id).first():
                continue
            ae = AlumnoExtracurricular(
                alumno_id=s.id,
                extracurricular_id=ex.id,
                calificacion=None,
                horas_cumplidas=random.randint(0, ex.cupo_maximo if ex.cupo_maximo else 50),
                completado=random.choice([False, False, True]),
            )
            session.add(ae)
            try:
                session.commit()
                ae_count += 1
            except Exception:
                session.rollback()
    print(f"Extracurriculars: {len(created_ex)}, alumno_extracurricular entries: {ae_count}\n")

# ---------------------------
# SERVICIO SOCIAL & PRACTICAS
# ---------------------------

def seed_servicio_practicas(session: Session):
    print("Seeding servicio social and practicas profesionales...")
    alumnos = session.query(Alumno).all()
    estatus_serv = session.query(CatEstatusServicio).all()
    ss_count = 0
    pp_count = 0
    for s in random.sample(alumnos, min(len(alumnos), 80)):
        est = random.choice(estatus_serv)
        ss = ServicioSocial(
            alumno_id=s.id,
            institucion=fake.company(),
            dependencia=fake.bs(),
            programa=fake.catch_phrase(),
            descripcion=fake.text(max_nb_chars=200),
            horas_requeridas=480,
            horas_cumplidas=random.randint(0,480),
            fecha_inicio=date.today() - timedelta(days=random.randint(100,1000)),
            estatus_id=est.id
        )
        session.add(ss)
        try:
            session.commit()
            ss_count += 1
        except Exception:
            session.rollback()
    for s in random.sample(alumnos, min(len(alumnos), 60)):
        est = random.choice(estatus_serv)
        pp = PracticasProfesionales(
            alumno_id=s.id,
            empresa=fake.company(),
            puesto=fake.job(),
            area=random.choice(["TI","Marketing","Administración"]),
            descripcion=fake.text(max_nb_chars=200),
            horas_requeridas=300,
            horas_cumplidas=random.randint(0,300),
            fecha_inicio=date.today() - timedelta(days=random.randint(30,800)),
            estatus_id=est.id
        )
        session.add(pp)
        try:
            session.commit()
            pp_count += 1
        except Exception:
            session.rollback()
    print(f"ServicioSocial: {ss_count}, PracticasProfesionales: {pp_count}\n")

# ---------------------------
# TITULACION REQUISITOS & ALUMNO TITULACION
# ---------------------------

def seed_titulacion(session: Session):
    print("Seeding titulacion requisitos and alumno_titulacion...")
    plans = session.query(PlanEstudio).all()
    alumnos = session.query(Alumno).all()
    requisitos = []
    for plan in plans:
        # create 5 requisitos per plan
        for i in range(1,6):
            req = TitulacionRequisito(
                plan_estudio_id=plan.id,
                carrera_id=plan.carrera_id,
                requisito=f"Requisito {i} Plan {plan.id}",
                descripcion=fake.text(max_nb_chars=120),
                obligatorio=True,
                orden=i,
                activo=True
            )
            session.add(req)
            requisitos.append(req)
    try:
        session.commit()
    except Exception:
        session.rollback()
    # assign some requisitos as fulfilled to random alumnos
    at_count = 0
    for alumno in random.sample(alumnos, min(len(alumnos), 120)):
        for req in random.sample(requisitos, min(3, len(requisitos))):
            if session.query(AlumnoTitulacion).filter_by(alumno_id=alumno.id, requisito_id=req.id).first():
                continue
            at = AlumnoTitulacion(
                alumno_id=alumno.id,
                requisito_id=req.id,
                cumplido=random.choice([False, True, False]),
                fecha_cumplimiento=(date.today() - timedelta(days=random.randint(0,1000))) if random.choice([True, False]) else None
            )
            session.add(at)
            try:
                session.commit()
                at_count += 1
            except Exception:
                session.rollback()
    print(f"Titulacion requisitos created: {len(requisitos)}, alumno_titulacion entries: {at_count}\n")

# ---------------------------
# ALUMNI & EVENTS
# ---------------------------

def seed_alumni_events(session: Session):
    print("Seeding alumni, eventos_alumni and inscripciones_eventos...")
    alumnos = session.query(Alumno).all()
    alumni_count = 0
    for alumno in random.sample(alumnos, min(len(alumnos), 60)):
        if session.query(Alumni).filter_by(alumno_id=alumno.id).first():
            continue
        al = Alumni(
            alumno_id=alumno.id,
            empresa_actual=random.choice([fake.company(), None]),
            puesto_actual=random.choice([fake.job(), None]),
            sector_industria=random.choice(["TI","Educación","Salud","Servicios"]),
            salario_rango=random.choice(["<20k","20-40k","40-60k",">60k"]),
            linkedin=f"https://linkedin.com/in/{fake.user_name()}",
            email_personal=fake.email(),
            telefono_personal=fake.phone_number(),
            direccion_actual=fake.address(),
            acepta_contacto=random.choice([True, False]),
            disponible_mentoria=random.choice([True, False]),
            biografia=fake.text(max_nb_chars=200)
        )
        session.add(al)
        try:
            session.commit()
            alumni_count += 1
        except Exception:
            session.rollback()
    eventos = []
    for i in range(CONFIG["EVENTOS_ALUMNI"]):
        fecha_ev = datetime.now() + timedelta(days=random.randint(-30,90))
        ev = EventoAlumni(
            titulo=f"Evento Alumni {i+1}",
            descripcion=fake.text(max_nb_chars=200),
            fecha_evento=fecha_ev,
            ubicacion=random.choice(["Auditorio A","Sala B","Plataforma Zoom"]),
            modalidad=random.choice(["Presencial","Virtual"]),
            url_virtual=(f"https://meet.example.com/{random.randint(1000,9999)}" if random.choice([True, False]) else None),
            cupo_maximo=random.randint(20,200),
            cupo_actual=0,
            costo=random.choice([0.0, 50.0, 100.0]),
            requiere_registro=True,
            activo=True
        )
        session.add(ev)
        try:
            session.commit()
            eventos.append(ev)
        except Exception:
            session.rollback()
    # inscripciones_eventos
    ie_count = 0
    for ev in eventos:
        to_register = random.sample(alumnos, min(len(alumnos), random.randint(5, 40)))
        for s in to_register:
            if session.query(InscripcionEvento).filter_by(evento_id=ev.id, alumno_id=s.id).first():
                continue
            ie = InscripcionEvento(evento_id=ev.id, alumno_id=s.id, asistio=random.choice([True, False, None]))
            session.add(ie)
            try:
                session.commit()
                ie_count += 1
            except Exception:
                session.rollback()
    print(f"Alumni created: {alumni_count}, eventos: {len(eventos)}, inscripciones_eventos: {ie_count}\n")

# ---------------------------
# NOTIFICATIONS, AUDIT LOG, CALENDARIO ACADEMICO
# ---------------------------

def seed_notifications_audit_calendar(session: Session):
    print("Seeding notifications, audit_log and calendario_academico...")
    usuarios = session.query(Usuario).all()
    tipos_not = session.query(CatTiposNotificacion).all()
    tipos_evento = session.query(CatTiposEventoCalendario).all()
    periodos = session.query(Periodo).all()

    notif_count = 0
    for u in random.sample(usuarios, min(len(usuarios), 150)):
        titulo = f"Notificación para {u.email}"
        tipo = random.choice(tipos_not)
        n = Notificacion(
            usuario_id=u.id,
            tipo_id=tipo.id,
            titulo=titulo,
            mensaje=fake.text(max_nb_chars=200),
            prioridad=random.choice(["baja","normal","alta"]),
            leida=random.choice([False, True]),
            fecha_expiracion=(datetime.now() + timedelta(days=random.randint(1,60))) if random.choice([True, False]) else None
        )
        session.add(n)
        try:
            session.commit()
            notif_count += 1
        except Exception:
            session.rollback()

    # audit_log sample entries
    audit_count = 0
    for _ in range(60):
        u = random.choice(usuarios)
        al = AuditLog(
            tabla=random.choice(["alumnos","usuarios","pagos","inscripciones"]),
            registro_id=random.randint(1,500),
            accion=random.choice(["create","update","delete"]),
            usuario_id=u.id,
            datos_anteriores=None,
            datos_nuevos=None,
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent()
        )
        session.add(al)
        try:
            session.commit()
            audit_count += 1
        except Exception:
            session.rollback()

    # calendario académico entries
    cal_count = 0
    for periodo in periodos:
        for i in range(4):
            inicio = periodo.fecha_inicio + timedelta(days=random.randint(0,60))
            fin = inicio + timedelta(days=random.randint(1,20))
            ca = CalendarioAcademico(
                periodo_id=periodo.id,
                tipo_id=random.choice(tipos_evento).id,
                titulo=f"Evento {i+1} Periodo {periodo.nombre}",
                descripcion=fake.text(max_nb_chars=200),
                fecha_inicio=inicio,
                fecha_fin=fin,
                aplica_carreras=None,
                todo_el_dia=random.choice([True, False])
            )
            session.add(ca)
            try:
                session.commit()
                cal_count += 1
            except Exception:
                session.rollback()

    print(f"Notificaciones: {notif_count}, audit_log: {audit_count}, calendario entries: {cal_count}\n")

# ---------------------------
# ORCHESTRATOR
# ---------------------------

def run_full_seed():
    print("Creating tables if not exists...")
    Base.metadata.create_all(engine)
    session = Session(bind=engine)

    print("\n=== START SEED ===\n")
    try:
        seed_catalogs(session)
        seed_carreras_planes_materias(session)
        seed_periodos_grupos(session)
        seed_docentes(session)
        seed_docente_materia_horarios(session)
        seed_alumnos_usuarios(session)
        seed_usuarios_docentes(session)
        seed_inscripciones_and_grades(session)
        seed_pagos(session)
        seed_documentos(session)
        seed_extracurriculars(session)
        seed_servicio_practicas(session)
        seed_titulacion(session)
        seed_alumni_events(session)
        seed_notifications_audit_calendar(session)
        print("=== SEED FINISHED ===")
    finally:
        session.close()


# ---------------------------
# MENU
# ---------------------------

def main_menu():
    
    try:
        while True:
            print("\n======= SEEDER MENU =======")
            print("1. Run seed (safe, no clearing)")
            print("2. Clear database ONLY")
            print("3. Clear database AND run seed (fresh install)")
            print("4. Exit")
            print("===========================\n")
            choice = input("Select an option: ").strip()

            if choice == "1":
                run_full_seed()
            elif choice == "2":
                session = Session(bind=engine)
                try:
                    clear_database(session)
                finally:
                    session.close()
            elif choice == "3":
                session = Session(bind=engine)
                try:
                    clear_database(session)
                finally:
                    session.close()
                run_full_seed()
            elif choice == "4":
                print("Exiting.")
                break
            else:
                print("Invalid option.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main_menu()
