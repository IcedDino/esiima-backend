import sys
import os
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base
from app.models import Alumno, Materia

class Solicitud(Base):
    __tablename__ = 'solicitudes'
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey('alumnos.id'), nullable=False)
    materia_id = Column(Integer, ForeignKey('materias.id'), nullable=False)
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())
    estatus = Column(String(255), default='Pendiente')

    alumno = relationship("Alumno")
    materia = relationship("Materia")

def create_solicitudes_table():
    """
    Creates the 'solicitudes' table in the database.
    """
    try:
        print("Starting migration to create 'solicitudes' table...")
        Base.metadata.create_all(bind=engine, tables=[Solicitud.__table__])
        print("'solicitudes' table created successfully.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Migration failed.")

if __name__ == "__main__":
    create_solicitudes_table()
