import sys
import os

# --- Start of the fix ---
# Calculate the project root directory, which is one level up from 'scripts'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Change the current working directory to the project root.
# This ensures that relative paths for .env files or SSL certs are found correctly
# by the code in app/database.py.
os.chdir(project_root)

# Add the project root to the Python path to allow importing from 'app'
sys.path.insert(0, project_root)
# --- End of the fix ---

# Now that the environment is set up correctly, we can import our app modules.
# The load_dotenv() inside app/database.py will now work as expected.
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Usuario
from app.auth import get_password_hash

def hash_existing_passwords():
    """
    Connects to the database and updates plaintext passwords with their bcrypt hash.
    """
    print("Attempting to connect to the database...")
    db: Session = SessionLocal()
    if not db:
        print("Failed to create a database session. Please check your .env file and database credentials.")
        return
        
    try:
        print("Database session created. Fetching users...")
        # Fetch all users that might have the placeholder password
        users_to_update = db.query(Usuario).filter(Usuario.password_hash == "notarealhash").all()

        if not users_to_update:
            print("No users with the password 'notarealhash' found. Passwords may already be hashed.")
            return

        password_to_hash = "notarealhash"
        new_hash = get_password_hash(password_to_hash)
        
        print(f"Found {len(users_to_update)} user(s) with the placeholder password.")
        print(f"Hashing '{password_to_hash}' to: {new_hash}")

        for user in users_to_update:
            user.password_hash = new_hash
            print(f"Updating password for user: {user.email}")

        db.commit()
        print("\nSuccessfully updated all passwords.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Rolling back changes.")
        db.rollback()
    finally:
        print("Closing database session.")
        db.close()

if __name__ == "__main__":
    print("--- Starting Password Hashing Script ---")
    hash_existing_passwords()
    print("--- Script Finished ---")
