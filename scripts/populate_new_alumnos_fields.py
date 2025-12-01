#!/usr/bin/env python3
"""
populate_new_alumnos_fields.py

This script populates the newly added fields for existing records in the 'alumnos' table
with fake data. It's designed to be run after the migration that adds these columns.

Fields to populate:
- calle
- num_ext
- num_int
- colonia
- codigo_postal
- municipio
- estado
- ciclo_escolar
- nivel_estudios
- semestre_grupo
- cursa_actualmente

To run this script, execute the following command from your project's root directory:
python scripts/populate_new_alumnos_fields.py
"""

import sys
import os
import random
from faker import Faker

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import engine
from app.models import Alumno

fake = Faker("es_MX")

def populate_new_fields():
    """
    Connects to the database, queries all students, and fills in the new
    empty fields with generated data.
    """
    print("Starting to populate new fields for existing students...")
    session = Session(bind=engine)
    
    try:
        # Get all students that have not been populated yet
        # A simple check for 'calle IS NULL' should be sufficient
        alumnos_to_update = session.query(Alumno).filter(Alumno.calle == None).all()

        if not alumnos_to_update:
            print("No students found that need updating. All fields seem to be populated.")
            return

        print(f"Found {len(alumnos_to_update)} students to update.")

        for i, alumno in enumerate(alumnos_to_update):
            # Populate address fields
            alumno.calle = fake.street_name()
            alumno.num_ext = fake.building_number()
            alumno.num_int = str(random.randint(1, 20)) if random.choice([True, False]) else None
            alumno.colonia = fake.street_name()
            alumno.codigo_postal = fake.postcode()
            alumno.municipio = fake.city()
            alumno.estado = fake.state()

            # Populate academic fields
            current_year = date.today().year
            alumno.ciclo_escolar = f"{current_year}-{current_year + 1}"
            alumno.nivel_estudios = "Licenciatura"
            alumno.semestre_grupo = f"{alumno.cuatrimestre_actual or random.randint(1,9)}{random.choice(['A', 'B'])}"
            alumno.cursa_actualmente = "Sí"
            
            # Print progress
            if (i + 1) % 50 == 0:
                print(f"Updated {i + 1}/{len(alumnos_to_update)} students...")

        # Commit all changes at once
        print("Committing changes to the database...")
        session.commit()
        print(f"✔ Successfully populated new fields for {len(alumnos_to_update)} students.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Rolling back changes.")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        print("Session closed.")

if __name__ == "__main__":
    from datetime import date
    populate_new_fields()
