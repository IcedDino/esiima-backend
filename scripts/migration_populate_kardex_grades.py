import sys
import os
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import func

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from app.models import Kardex, CalificacionParcial

def populate_kardex_grades():
    """
    Populates or re-populates the calificacion_final and aprobado fields in the Kardex table
    for ALL entries, by averaging partial grades.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Starting migration to populate/re-populate Kardex final grades for all entries...")

        # Fetch ALL Kardex entries
        kardex_entries_to_update = db.query(Kardex).all()

        if not kardex_entries_to_update:
            print("No Kardex entries found. Skipping population.")
            return

        for kardex_entry in kardex_entries_to_update:
            final_grade = None # Initialize final_grade for each entry
            
            # Get associated partial grades
            partial_grades = db.query(CalificacionParcial).filter(
                CalificacionParcial.kardex_id == kardex_entry.id
            ).all()

            if partial_grades:
                # Calculate average of partial grades
                valid_grades = [p.calificacion for p in partial_grades if p.calificacion is not None]

                if valid_grades:
                    final_grade = round(sum(valid_grades) / len(valid_grades), 2)
                    print(f"Kardex ID {kardex_entry.id}: Calculated final_grade={final_grade} from partials.")
                else:
                    # Partial grades exist but are all None
                    print(f"Kardex ID {kardex_entry.id}: Partial grades exist but are all NULL. Defaulting final_grade to 0.0.")
                    final_grade = 0.0
            else:
                # If no partial grades, default final_grade to 0.0
                print(f"Kardex ID {kardex_entry.id}: No partial grades found. Defaulting final_grade to 0.0.")
                final_grade = 0.0

            kardex_entry.calificacion_final = final_grade
            kardex_entry.aprobado = final_grade is not None and final_grade >= 7.0  # Corrected passing grade to 7.0

            print(f"Updated Kardex ID {kardex_entry.id}: calificacion_final={kardex_entry.calificacion_final}, aprobado={kardex_entry.aprobado}")

        db.commit()
        print("\nKardex final grades population script finished successfully.")

    except Exception as e:
        db.rollback()
        print(f"\nAn error occurred during Kardex grades population: {e}")
        print("Kardex grades population failed and changes were rolled back.")
    finally:
        db.close()

if __name__ == "__main__":
    populate_kardex_grades()
