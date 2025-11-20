from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import SessionLocal, engine, Base
from .models import Carrera as DBCarrera
from .schemas import Carrera as SchemaCarrera

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS - this way avoids the type warning
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rest of your code...
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the ESIIMA API"}

@app.get("/carreras/", response_model=List[SchemaCarrera])
def read_carreras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    carreras = db.query(DBCarrera).offset(skip).limit(limit).all()
    return carreras