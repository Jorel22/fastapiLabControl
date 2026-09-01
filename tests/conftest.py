"""Fixtures compartidas de pruebas (pytest + TestClient de FastAPI + SQLite en memoria)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app

# SQLite en memoria con StaticPool para compartir el estado entre hilos/conexiones de test
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea una base de datos limpia para cada prueba."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def app(db_session):
    """Instancia de la aplicación FastAPI con la sesión de prueba inyectada."""
    application = create_app("testing")

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    application.dependency_overrides[get_db] = override_get_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP de pruebas para FastAPI."""
    with TestClient(app, cookies={}) as c:
        yield c
