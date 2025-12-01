import sys
import os

# Add the project root to the Python path to allow for package imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base
from scripts.migration_add_missing_fields import add_missing_columns
from scripts.migration_add_solicitudes import create_solicitudes_table
from scripts.migration_add_requisitos_fields import add_requisitos_columns

def run_migrations():
    """
    Runs all database migrations in the correct order.
    """
    print("--- Starting Master Database Migration ---")

    # Step 1: Create all tables from the models defined in Base
    try:
        print("\n[Step 1/4] Ensuring all tables are created...")
        # This will create tables for all models that inherit from Base
        # It will not fail if the tables already exist.
        Base.metadata.create_all(bind=engine)
        print("Table check complete.")
    except Exception as e:
        print(f"An error occurred during table creation: {e}")
        # We can choose to exit if this fails, as subsequent steps might depend on it
        return

    # Step 2: Run the script to add miscellaneous missing columns
    print("\n[Step 2/4] Running migration for missing fields (kardex, materias)...")
    try:
        add_missing_columns()
    except Exception as e:
        print(f"An error occurred during 'add_missing_columns': {e}")

    # Step 3: Run the script to create the 'solicitudes' table
    print("\n[Step 3/4] Running migration for 'solicitudes' table...")
    try:
        create_solicitudes_table()
    except Exception as e:
        print(f"An error occurred during 'create_solicitudes_table': {e}")

    # Step 4: Run the script to add fields to 'titulacion_requisitos'
    print("\n[Step 4/4] Running migration for 'requisitos' fields...")
    try:
        add_requisitos_columns()
    except Exception as e:
        print(f"An error occurred during 'add_requisitos_columns': {e}")

    print("\n--- Master Database Migration Finished ---")
    print("Your database schema should now be up-to-date.")

if __name__ == "__main__":
    run_migrations()
