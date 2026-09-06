"""Pruebas automatizadas de API — Jairo Jácome.

Técnica asignada: ANÁLISIS DE VALORES LÍMITE.
Regla de negocio: R03 (RF-002, integridad referencial) — todo bien debe
asignarse a un laboratorio existente; la Facultad de Mecánica cuenta con
seis laboratorios de cómputo, de modo que el rango válido es [1, 6].
Endpoint: POST /api/bienes

JUSTIFICACIÓN DE LA TÉCNICA
---------------------------
Se seleccionó la regla R03 porque el identificador de laboratorio tiene un
mínimo y un máximo definidos explícitamente por el dominio, y los errores
de programación del tipo off-by-one —escribir «mayor que» en lugar de
«mayor o igual que», o contar desde cero— se concentran justo en los
bordes del rango.

Se evalúan seis valores: 0, 1, 2, 5, 6 y 7. Los dos exteriores (0 y 7)
verifican que el rechazo se produzca de forma controlada; los límites
exactos (1 y 6) verifican que estén incluidos en la clase válida; y los
adyacentes interiores (2 y 5) confirman que el interior del rango se
comporta como se espera. Probar valores del centro del intervalo no
aportaría información: si 2 y 5 se aceptan, 3 y 4 también.

MATRIZ DE CASOS
---------------
    Caso   laboratorio_id   Frontera             Esperado
    -----  ---------------  -------------------  --------
    CP04   0                debajo del mínimo    422
    CP05   1                límite mínimo        201
    CP06   2                cerca del mínimo     201
    CP07   5                cerca del máximo     201
    CP08   6                límite máximo        201
    CP09   7                sobre el máximo      422

DEFECTOS
--------
Los dos casos exteriores resultaron NO CUMPLIDOS, y por causas distintas:

  CP04  el valor 0 se convierte silenciosamente en NULL y el alta se
        acepta con 201; el bien queda registrado sin laboratorio.
  CP09  el valor 7 no se valida contra el rango ni contra el catálogo,
        de modo que la violación de integridad referencial aflora como
        error no controlado (500) en lugar de un 422 descriptivo.

NOTA SOBRE EL ENTORNO DE PRUEBAS
--------------------------------
CP09 solo reproduce el 500 observado en Render si la base de datos aplica
claves foráneas. SQLite las tiene DESACTIVADAS por defecto, así que sin
intervención el caso devolvería 201 en local y el entorno de pruebas no
sería representativo de producción. La fixture `catalogo` de
tests/conftest.py ejecuta `PRAGMA foreign_keys=ON` precisamente para
cerrar esa brecha.

Ejecución:
    pytest tests/jairo_jacome/test_api_valores_limite.py -v
"""
import pytest

PREFIJO = "TEST-CN"

# Marca de técnica: permite ejecutar solo esta suite con `-m limite`.
pytestmark = pytest.mark.limite


def cuerpo_alta(codigo, laboratorio_id):
    """Cuerpo de alta con el único campo variable: el laboratorio."""
    return {
        "codigo_bien": codigo,
        "nombre": f"Equipo de pruebas {codigo}",
        "numero_serie": f"SN-{codigo}",
        "tipo": "computadora",
        "laboratorio_id": laboratorio_id,
        "custodio_id": 1,
    }


# ==========================================================================
# INTERIOR DEL RANGO — los cuatro valores válidos
# ==========================================================================
# Comparten estructura y resultado esperado, así que se parametrizan: una
# sola función genera cuatro casos identificados por su CPxx.


@pytest.mark.parametrize(
    "caso, laboratorio_id, frontera",
    [
        ("CP05", 1, "límite mínimo"),
        ("CP06", 2, "cerca del mínimo"),
        ("CP07", 5, "cerca del máximo"),
        ("CP08", 6, "límite máximo"),
    ],
)
def test_laboratorio_dentro_del_rango(cliente_admin, caso, laboratorio_id, frontera):
    """CP05-CP08 · Los cuatro valores del interior del intervalo se aceptan."""
    codigo = f"{PREFIJO}-{caso[-2:]}"
    r = cliente_admin.post("/api/bienes", json=cuerpo_alta(codigo, laboratorio_id))

    assert r.status_code == 201, f"{caso} ({frontera}) debería aceptarse"
    assert r.json()["bien"]["laboratorio_id"] == laboratorio_id

    # Verificación posterior: el laboratorio quedó realmente asignado.
    persistido = cliente_admin.get(f"/api/bienes/{codigo}").json()["bien"]
    assert persistido["laboratorio_id"] == laboratorio_id


# ==========================================================================
# EXTERIOR DEL RANGO — los dos defectos
# ==========================================================================


@pytest.mark.xfail(
    strict=True,
    reason="CP04 · Defecto: laboratorio_id = 0 se convierte silenciosamente en NULL "
           "(bien_service: `if lab_id == 0: lab_id = None`) y el alta se acepta con "
           "201. El bien queda en el inventario sin laboratorio asignado, lo que "
           "incumple la integridad exigida por RF-002.",
)
def test_CP04_laboratorio_debajo_del_minimo(cliente_admin):
    """CP04 · Debajo del mínimo: laboratorio_id = 0."""
    r = cliente_admin.post("/api/bienes", json=cuerpo_alta(f"{PREFIJO}-04", 0))

    assert r.status_code == 422, (
        "El valor 0 está fuera del rango [1, 6] y debe rechazarse, no "
        "convertirse en nulo sin avisar"
    )


@pytest.mark.xfail(
    strict=True,
    reason="CP09 · Defecto: laboratorio_id = 7 no se valida contra el rango ni "
           "contra el catálogo. La violación de integridad referencial aflora como "
           "error no controlado (500, sin cuerpo JSON) en lugar de un 422 "
           "descriptivo, exponiendo detalles internos del servidor.",
)
def test_CP09_laboratorio_sobre_el_maximo(cliente_admin):
    """CP09 · Sobre el máximo: laboratorio_id = 7, inexistente en el catálogo."""
    r = cliente_admin.post("/api/bienes", json=cuerpo_alta(f"{PREFIJO}-09", 7))

    assert r.status_code == 422, (
        "Un laboratorio inexistente debe rechazarse con un mensaje que permita "
        "al usuario saber qué regla infringió, no con un error interno"
    )


# ==========================================================================
# ASIMETRÍA ENTRE LOS DOS BORDES
# ==========================================================================
# No duplica CP04 ni CP09: documenta que los dos extremos del MISMO rango
# fallan de forma distinta, que es el hallazgo más informativo de la
# técnica y la evidencia de la característica de Consistencia en la matriz
# de calidad de datos.


def test_los_dos_bordes_del_rango_fallan_de_forma_distinta(cliente_admin):
    """Un mismo rango, dos valores fuera, dos comportamientos incompatibles."""
    # Borde inferior: el alta se acepta y el bien queda sin laboratorio.
    respuesta_cero = cliente_admin.post("/api/bienes", json=cuerpo_alta(f"{PREFIJO}-B0", 0))
    assert respuesta_cero.status_code == 201

    persistido = cliente_admin.get(f"/api/bienes/{PREFIJO}-B0").json()["bien"]
    assert persistido["laboratorio_id"] is None

    # Borde superior: la petición revienta. Se ejecuta AL FINAL a propósito:
    # la violación de integridad deja la transacción abortada, de modo que
    # cualquier consulta posterior en la misma sesión fallaría también. Ese
    # efecto colateral es en sí mismo parte del hallazgo — un solo dato mal
    # validado inutiliza la sesión de base de datos completa.
    respuesta_siete = cliente_admin.post("/api/bienes", json=cuerpo_alta(f"{PREFIJO}-B7", 7))
    assert respuesta_siete.status_code == 500

    # El cuerpo es texto plano ("Internal Server Error"), no el JSON con la
    # clave "error" que devuelve el resto de la API. El consumidor no puede
    # saber qué regla infringió, que es lo que registró la matriz de la
    # Tarea 4 como «respuesta sin cuerpo JSON».
    assert respuesta_siete.headers["content-type"].startswith("text/plain")
    assert "laboratorio" not in respuesta_siete.text.lower(), (
        "La respuesta ni siquiera menciona el campo que causó el fallo"
    )

    # Ninguno de los dos devolvió el 422 que exige la regla, y además el
    # sistema trata los dos extremos del mismo rango de forma incoherente.
