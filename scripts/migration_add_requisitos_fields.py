import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine

def add_requisitos_columns():
    """
    Adds the following columns if they don't exist:
    - unidades_requeridas and tipo_unidad to titulacion_requisitos
    - unidades_cubiertas to alumno_titulacion
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        print("Starting migration to add requisitos fields...")

        # 1. Add 'unidades_requeridas' to 'titulacion_requisitos' table
        try:
            db.execute(text('ALTER TABLE titulacion_requisitos ADD COLUMN unidades_requeridas INTEGER'))
            print("Column 'unidades_requeridas' added to 'titulacion_requisitos' table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'unidades_requeridas' already exists in 'titulacion_requisitos'.")
            else:
                raise

        # 2. Add 'tipo_unidad' to 'titulacion_requisitos' table
        try:
            db.execute(text('ALTER TABLE titulacion_requisitos ADD COLUMN tipo_unidad VARCHAR(255)'))
            print("Column 'tipo_unidad' added to 'titulacion_requisitos' table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'tipo_unidad' already exists in 'titulacion_requisitos'.")
            else:
                raise

        # 3. Add 'unidades_cubiertas' to 'alumno_titulacion' table
        try:
            db.execute(text('ALTER TABLE alumno_titulacion ADD COLUMN unidades_cubiertas INTEGER'))
            print("Column 'unidades_cubiertas' added to 'alumno_titulacion' table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'unidades_cubiertas' already exists in 'alumno_titulacion'.")
            else:
                raise
        
        db.commit()
        print("\nMigration script finished successfully.")

    except Exception as e:
        db.rollback()
        print(f"\nAn error occurred: {e}")
        print("Migration failed and changes were rolled back.")
    finally:
        db.close()

if __name__ == "__main__":
    add_requisitos_columns()
