import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine

def add_missing_columns():
    """
    Adds the following columns if they don't exist:
    - tipo_examen to kardex
    - faltas_permitidas to materias
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Starting migration to add missing fields...")

        # 1. Add 'tipo_examen' to 'kardex' table
        try:
            db.execute(text('ALTER TABLE kardex ADD COLUMN tipo_examen VARCHAR(255)'))
            print("Column 'tipo_examen' added to 'kardex' table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'tipo_examen' already exists in 'kardex'.")
            else:
                raise

        # 2. Add 'faltas_permitidas' to 'materias' table
        try:
            db.execute(text('ALTER TABLE materias ADD COLUMN faltas_permitidas INTEGER'))
            print("Column 'faltas_permitidas' added to 'materias' table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'faltas_permitidas' already exists in 'materias'.")
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
    add_missing_columns()
