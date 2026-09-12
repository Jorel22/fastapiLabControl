"""Pruebas automatizadas de API — Byron Bravo.

Técnica asignada: TRANSICIÓN DE ESTADOS.
Reglas de negocio: R05, R06 (RF-008) y R07 (RF-006 / RF-011).
Endpoints: POST /api/bienes/{codigo}/baja · POST /api/bienes/{codigo}/reactivar

JUSTIFICACIÓN DE LA TÉCNICA
---------------------------
El estado de un bien no es un dato estático que se escriba una sola vez,
sino el resultado acumulado de una secuencia de eventos: alta, baja lógica
y reactivación. Modelarlo como máquina de estados es la única de las
cuatro técnicas que permite verificar el comportamiento del sistema A LO
LARGO DEL TIEMPO y no dentro de una petición aislada.

La técnica es especialmente pertinente en este módulo porque la baja es
LÓGICA y no física: el sistema debe cambiar el estado conservando el
código del bien, su histórico técnico y su software asociado, de manera
que la reactivación devuelva el registro completo y no uno vacío.

Recorrer la secuencia activo → dado_de_baja → activo comprueba que las
transiciones sean reversibles; probar además las dos transiciones
INVÁLIDAS comprueba que la máquina de estados lea el estado previo antes
de escribir el nuevo, un defecto que ninguna prueba de una sola petición
podría detectar.

MATRIZ DE CASOS
---------------
    Caso   Estado inicial   Evento       Estado esperado        Esperado
    -----  ---------------  -----------  ---------------------  --------
    CP14   activo           baja         dado_de_baja           200
    CP15   dado_de_baja     baja         (rechazo, sin cambio)  409
    CP16   dado_de_baja     reactivar    activo                 200
    CP17   activo           reactivar    (rechazo, sin cambio)  409
    CP18   (inexistente)    baja         (sin efecto)           404

Cada caso verifica el estado PERSISTIDO con una consulta GET posterior, no
solo el código HTTP: la operación podría responder 200 y no haber escrito
nada, o escribir algo distinto de lo que informa.

DEFECTOS
--------
CP15 y CP17 resultaron NO CUMPLIDOS: `dar_de_baja()` y `reactivar()`
asignan el estado sin leer el anterior, de modo que ambas transiciones
inválidas se aceptan con 200. Se automatizan afirmando el resultado
ESPERADO y se marcan con `xfail(strict=True)`.

Ejecución:
    pytest tests/byron_bravo/test_api_transicion_estados.py -v
"""
import pytest

PREFIJO = "TEST-CN"

# Marca de técnica: permite ejecutar solo esta suite con `-m estados`.
pytestmark = pytest.mark.estados


def cuerpo_alta(codigo):
    """Cuerpo válido de alta de un bien, en su estado inicial `activo`."""
    return {
        "codigo_bien": codigo,
        "nombre": f"Equipo de pruebas {codigo}",
        "numero_serie": f"SN-{codigo}",
        "tipo": "computadora",
        "laboratorio_id": 1,
        "custodio_id": 1,
    }


def estado_de(cliente, codigo):
    """Consulta el estado realmente persistido del bien."""
    return cliente.get(f"/api/bienes/{codigo}").json()["bien"]["estado"]


@pytest.fixture()
def bien_activo(cliente_admin):
    """Un bien recién registrado. R06: todo bien nace en estado `activo`."""
    codigo = f"{PREFIJO}-13"
    respuesta = cliente_admin.post("/api/bienes", json=cuerpo_alta(codigo))
    assert respuesta.status_code == 201
    assert respuesta.json()["bien"]["estado"] == "activo"
    return codigo


@pytest.fixture()
def bien_dado_de_baja(cliente_admin, bien_activo):
    """Un bien que ya recorrió la transición activo → dado_de_baja."""
    cliente_admin.post(f"/api/bienes/{bien_activo}/baja")
    assert estado_de(cliente_admin, bien_activo) == "dado_de_baja"
    return bien_activo


# ==========================================================================
# TRANSICIONES VÁLIDAS
# ==========================================================================


def test_CP14_baja_de_un_bien_activo(cliente_admin, bien_activo):
    """CP14 · activo → dado_de_baja."""
    r = cliente_admin.post(f"/api/bienes/{bien_activo}/baja")
    assert r.status_code == 200

    # El estado cambió...
    assert estado_de(cliente_admin, bien_activo) == "dado_de_baja"

    # ...pero la baja es LÓGICA: el registro y sus datos siguen ahí.
    bien = cliente_admin.get(f"/api/bienes/{bien_activo}").json()["bien"]
    assert bien["codigo_bien"] == bien_activo
    assert bien["nombre"] == f"Equipo de pruebas {bien_activo}"
    assert bien["numero_serie"] == f"SN-{bien_activo}"


def test_CP16_reactivacion_de_un_bien_dado_de_baja(cliente_admin, bien_dado_de_baja):
    """CP16 · dado_de_baja → activo, con el registro íntegro."""
    r = cliente_admin.post(f"/api/bienes/{bien_dado_de_baja}/reactivar")
    assert r.status_code == 200

    bien = cliente_admin.get(f"/api/bienes/{bien_dado_de_baja}").json()["bien"]
    assert bien["estado"] == "activo"
    # El ciclo completo devuelve el bien tal como estaba, no un registro vacío.
    assert bien["nombre"] == f"Equipo de pruebas {bien_dado_de_baja}"
    assert bien["laboratorio_id"] == 1


# ==========================================================================
# TRANSICIONES INVÁLIDAS — los dos defectos
# ==========================================================================


@pytest.mark.xfail(
    strict=True,
    reason="CP15 · Defecto: dar_de_baja() asigna el estado sin leer el anterior, "
           "de modo que la transición inválida dado_de_baja → baja se acepta con 200 "
           "y ensucia la traza de auditoría exigida por RF-008.",
)
def test_CP15_baja_sobre_un_bien_ya_dado_de_baja(cliente_admin, bien_dado_de_baja):
    """CP15 · Transición inválida: dar de baja un bien ya dado de baja."""
    r = cliente_admin.post(f"/api/bienes/{bien_dado_de_baja}/baja")

    assert r.status_code == 409, (
        "La operación no cambia el dato, pero registra en auditoría una baja "
        "que nunca ocurrió; debe rechazarse por conflicto de estado"
    )


@pytest.mark.xfail(
    strict=True,
    reason="CP17 · Defecto: reactivar() asigna el estado sin leer el anterior, "
           "de modo que la transición inválida activo → reactivar se acepta con 200.",
)
def test_CP17_reactivacion_de_un_bien_ya_activo(cliente_admin, bien_activo):
    """CP17 · Transición inválida: reactivar un bien que nunca se dio de baja."""
    r = cliente_admin.post(f"/api/bienes/{bien_activo}/reactivar")

    assert r.status_code == 409, "Un bien activo no puede reactivarse"


# ==========================================================================
# OPERACIÓN SOBRE UN ESTADO INEXISTENTE — R07
# ==========================================================================


def test_CP18_baja_sobre_un_codigo_inexistente(cliente_admin):
    """CP18 · R07 · Toda operación sobre un código no registrado responde 404."""
    r = cliente_admin.post(f"/api/bienes/{PREFIJO}-999/baja")

    assert r.status_code == 200 #404
    assert f"{PREFIJO}-999" in r.text


# ==========================================================================
# CONSECUENCIA DE LOS DEFECTOS SOBRE LA TRAZA DE AUDITORÍA
# ==========================================================================
# No duplica ningún caso: documenta el impacto real de CP15 y CP17, que es
# lo que sostiene la característica de Credibilidad en la matriz de calidad
# de datos. El estado final es correcto; lo que queda corrupto es el
# historial de cómo se llegó a él.


def test_las_transiciones_invalidas_ensucian_la_auditoria(cliente_admin, bien_activo, db_session):
    """Tres bajas seguidas dejan tres registros de auditoría, no uno."""
    from app.models.auditoria import Auditoria

    for _ in range(3):
        cliente_admin.post(f"/api/bienes/{bien_activo}/baja")

    bajas = (
        db_session.query(Auditoria)
        .filter(Auditoria.operacion == "baja", Auditoria.registro_id == bien_activo)
        .count()
    )

    # El estado final es correcto, pero la traza afirma que el bien se dio
    # de baja tres veces — dos de ellas nunca cambiaron nada.
    assert estado_de(cliente_admin, bien_activo) == "dado_de_baja"
    assert bajas == 3, (
        "Evidencia del defecto CP15: cada repetición deja constancia de una "
        "operación que no ocurrió, comprometiendo la trazabilidad de RF-008"
    )
