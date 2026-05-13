"""
Pytest configuration and fixtures
"""
import pytest
import os
import tempfile
import uuid as uuid_pkg
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, TypeDecorator, CHAR, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.core.security import get_password_hash

# Custom UUID type that works with SQLite
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as string.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid_pkg.UUID):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid_pkg.UUID):
                return value
            else:
                return uuid_pkg.UUID(value)

# Monkey-patch UUID type in all models to use GUID for tests
@event.listens_for(Base.metadata, "before_create")
def receive_before_create(target, connection, **kw):
    """Replace PostgreSQL UUID with our custom GUID for SQLite compatibility"""
    for table in target.tables.values():
        for column in table.columns:
            if hasattr(column.type, '__visit_name__') and column.type.__visit_name__ == 'UUID':
                column.type = GUID()

# Test database setup (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    try:
        if os.path.exists("./test.db"):
            os.remove("./test.db")
    except PermissionError:
        pass  # File is locked on Windows

@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Clean database before each test"""
    connection = engine.connect()
    transaction = connection.begin()
    
    for table in reversed(Base.metadata.sorted_tables):
        connection.execute(table.delete())
    
    transaction.commit()
    connection.close()
    yield

@pytest.fixture(scope="function")
def db_session():
    """Create database session for tests"""
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }

@pytest.fixture
def test_user(test_user_data):
    """Create test user in database"""
    session = TestingSessionLocal()
    user = User(
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"]
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    user_id = user.id
    session.close()
    
    # Return a dict with user info instead of the object
    return {
        "id": user_id,
        "email": test_user_data["email"],
        "full_name": test_user_data["full_name"]
    }

@pytest.fixture
def auth_headers(client, test_user_data, test_user):
    """Get authentication headers for test requests"""
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200, f"Login failed: {response.json() if response.status_code != 200 else ''}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_file():
    """Create a temporary test file"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(b"Test PDF content for testing file upload")
        tmp_file_path = tmp_file.name
    
    yield tmp_file_path
    
    # Cleanup
    if os.path.exists(tmp_file_path):
        os.remove(tmp_file_path)

# Configure pytest for async support
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"