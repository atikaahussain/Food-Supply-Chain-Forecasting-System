import os
from dotenv import load_dotenv
from pathlib import Path

# This tells Python: "Find my current location, go up one folder, and look for .env"
base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # We use a default of None to catch if the loading fails
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Critical Check: This stops the app and tells you WHY it failed
    if not SQLALCHEMY_DATABASE_URI:
        print(f"DEBUG: Looking for .env at: {env_path}")
        raise RuntimeError("DATABASE_URL not found! Ensure your .env file is in the root folder.")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-atika')