from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()

# Construct the database URL from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_SSL_CERT_PATH = os.getenv("DB_SSL_CERT_PATH")

# If the DB_SSL_CERT_PATH is not provided via environment variable,
# we construct a default path for local development.
if not DB_SSL_CERT_PATH:
    # This assumes the script is in a subdirectory of the project root.
    # The certificate is expected to be in the project root.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cert_path = os.path.join(project_root, "DigiCertGlobalRootG2.crt.pem")
    if os.path.exists(cert_path):
        DB_SSL_CERT_PATH = cert_path

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Set up connection arguments, including SSL if a certificate path is provided
connect_args = {}
if DB_SSL_CERT_PATH:
    connect_args["ssl"] = {"ca": DB_SSL_CERT_PATH}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
