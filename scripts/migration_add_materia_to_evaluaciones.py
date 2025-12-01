#!/usr/bin/env python3
"""
migration_add_materia_to_evaluaciones.py

This script adds the 'materia_id' column to the 'evaluaciones' table.

To run this migration, execute the following command from your project's root directory:
python scripts/migration_add_materia_to_evaluaciones.py
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import engine

def run_migration():
    """
    Adds the new column to the 'evaluaciones' table.
    """
    print("Starting migration: Adding 'materia_id' to 'evaluaciones' table...")

    try:
        with engine.connect() as connection:
            with connection.begin():
                print("Adding column: materia_id")
                connection.execute(text("ALTER TABLE evaluaciones ADD COLUMN materia_id INTEGER"))
                print("Adding foreign key constraint...")
                connection.execute(text("ALTER TABLE evaluaciones ADD CONSTRAINT fk_evaluaciones_materia FOREIGN KEY (materia_id) REFERENCES materias(id)"))

            print("✔ Migration completed successfully.")

    except Exception as e:
        print(f"An error occurred during the migration: {e}")
        print("Migration failed. Please check the error and try again.")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
