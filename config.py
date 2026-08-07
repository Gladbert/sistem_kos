import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sistem-kos-secret-key-2024")
    
    # Supabase/Postgres: fix postgres:// to postgresql://
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
