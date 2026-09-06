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


# ==========================================================================
# Fixtures compartidas por las carpetas de los tres integrantes
# (U3 · Tarea 1 — automatización de la Matriz de Casos de Prueba).
#
# Se añaden aquí, y no en cada carpeta, para que las tres suites de caja
# negra partan del mismo catálogo institucional y de la misma sesión
# autenticada: cualquier diferencia entre los datos de partida haría que
# los resultados de un integrante no fueran comparables con los de otro.
# Las 62 pruebas de RF anteriores no las usan y no se ven afectadas.
# ==========================================================================
from sqlalchemy import text  # noqa: E402

from app.models.custodio import Custodio  # noqa: E402
from app.models.laboratorio import Laboratorio  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

# Prefijo acordado en la Tarea 4: hace identificables y auditables los
# registros generados por las pruebas.
PREFIJO_QA = "TEST-CN"

USUARIO_ADMIN = "qa_admin"
CLAVE_ADMIN = "QaAdmin2026"
USUARIO_CONSULTA = "qa_consulta"
CLAVE_CONSULTA = "QaConsulta2026"


@pytest.fixture(scope="function")
def catalogo(db_session):
    """Siembra el catálogo institucional y las dos cuentas de prueba.

    Activa además la comprobación de claves foráneas, desactivada por
    defecto en SQLite. Sin este PRAGMA el entorno de pruebas no reproduce
    el fallo de integridad referencial que CP09 provocó en Render sobre
    PostgreSQL: la fila se insertaría con un laboratorio inexistente.
    """
    db_session.execute(text("PRAGMA foreign_keys=ON"))

    for i in range(1, 7):  # R03 — seis laboratorios de cómputo
        db_session.add(
            Laboratorio(id=i, nombre=f"Laboratorio {i}", ubicacion="Facultad de Mecánica")
        )
    db_session.add(Custodio(id=1, nombre="Custodio de pruebas", cargo="Técnico"))

    admin = Usuario(usuario=USUARIO_ADMIN, perfil="administrador", activo=True)
    admin.set_password(CLAVE_ADMIN)
    db_session.add(admin)

    consulta = Usuario(usuario=USUARIO_CONSULTA, perfil="consulta", activo=True)
    consulta.set_password(CLAVE_CONSULTA)
    db_session.add(consulta)

    db_session.commit()

    yield db_session

    # CP09 deja la transacción abortada por la violación de integridad
    # referencial: hay que revertirla antes de tocar la conexión, o el
    # desmontaje falla y pytest reporta el caso dos veces.
    db_session.rollback()
    db_session.execute(text("PRAGMA foreign_keys=OFF"))
    db_session.commit()


def _sesion_iniciada(app, usuario, clave):
    """Devuelve un TestClient con la cookie de sesión ya establecida.

    `raise_server_exceptions=False` hace que un error no controlado se
    devuelva como 500 en lugar de propagarse como excepción, que es lo que
    necesita CP09 para observar el mismo código que devolvió Render.
    """
    cliente = TestClient(app, cookies={}, raise_server_exceptions=False)
    respuesta = cliente.post("/api/auth/login", json={"usuario": usuario, "password": clave})
    assert respuesta.status_code == 200, f"Falló el login previo: {respuesta.text}"
    return cliente


@pytest.fixture(scope="function")
def cliente_admin(app, catalogo):
    """Cliente con sesión de perfil administrador (escritura sobre el inventario).

    El login se hace una sola vez; TestClient conserva la cookie HttpOnly
    `access_token_cookie` y la reenvía en las peticiones siguientes, igual
    que hace Postman.
    """
    with _sesion_iniciada(app, USUARIO_ADMIN, CLAVE_ADMIN) as c:
        yield c


@pytest.fixture(scope="function")
def cliente_consulta(app, catalogo):
    """Cliente con sesión de perfil consulta (solo lectura — RF-001 / RNF-003)."""
    with _sesion_iniciada(app, USUARIO_CONSULTA, CLAVE_CONSULTA) as c:
        yield c


@pytest.fixture(scope="function")
def cliente_anonimo(app, catalogo):
    """Cliente sin autenticar."""
    with TestClient(app, cookies={}, raise_server_exceptions=False) as c:
        yield c
