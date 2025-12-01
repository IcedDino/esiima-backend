#!/usr/bin/env python3
"""
migration_add_fields_to_alumnos.py

This script adds the following fields to the 'alumnos' table:
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

To run this migration, execute the following command from your project's root directory:
python scripts/migration_add_fields_to_alumnos.py
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import engine

def run_migration():
    """
    Adds the new columns to the 'alumnos' table.
    """
    print("Starting migration: Adding new fields to 'alumnos' table...")

    try:
        with engine.connect() as connection:
            # Use a transaction to ensure all or no changes are applied
            with connection.begin():
                print("Adding column: calle")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN calle VARCHAR(255)"))
                
                print("Adding column: num_ext")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN num_ext VARCHAR(255)"))

                print("Adding column: num_int")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN num_int VARCHAR(255)"))

                print("Adding column: colonia")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN colonia VARCHAR(255)"))

                print("Adding column: codigo_postal")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN codigo_postal VARCHAR(255)"))

                print("Adding column: municipio")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN municipio VARCHAR(255)"))

                print("Adding column: estado")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN estado VARCHAR(255)"))

                print("Adding column: ciclo_escolar")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN ciclo_escolar VARCHAR(255)"))

                print("Adding column: nivel_estudios")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN nivel_estudios VARCHAR(255)"))

                print("Adding column: semestre_grupo")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN semestre_grupo VARCHAR(255)"))

                print("Adding column: cursa_actualmente")
                connection.execute(text("ALTER TABLE alumnos ADD COLUMN cursa_actualmente VARCHAR(255)"))

            print("✔ Migration completed successfully.")

    except Exception as e:
        print(f"An error occurred during the migration: {e}")
        print("Migration failed. Please check the error and try again.")
        # It's good practice to log the full error for debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
