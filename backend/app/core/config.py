import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    # Database
    DATABASE_URL: str = "postgresql://legal_user:legal_password_123@localhost:5432/legal_doc_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # ChromaDB
    CHROMADB_URL: str = "http://localhost:8000"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760
    UPLOAD_DIRECTORY: str = "./uploads"
    
    # Development
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()

os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)