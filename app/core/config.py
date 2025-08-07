import os
from typing import Optional
from pydantic_settings import BaseSettings  # ✅ correct for Pydantic v2



class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Steves0705@localhost:5432/chatscribe2")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "chatscribe2")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "localhost")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt"}

    class Config:
        env_file = ".env"


settings = Settings()
