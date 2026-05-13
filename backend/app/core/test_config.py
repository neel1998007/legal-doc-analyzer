"""
Test configuration for Legal Document Analyzer
"""
import os
from app.core.config import Settings

class TestSettings(Settings):
    """Test-specific settings"""
    
    # Test Database (SQLite for tests)
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Test environment
    DEBUG: bool = True
    
    # Test file upload
    UPLOAD_DIRECTORY: str = "./test_uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB for tests
    
    # Test JWT
    SECRET_KEY: str = "test-secret-key-for-testing-only"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5  # Short expiry for tests
    
    class Config:
        env_file = ".env.test"

# Create test settings instance
test_settings = TestSettings()

# Ensure test upload directory exists
os.makedirs(test_settings.UPLOAD_DIRECTORY, exist_ok=True)