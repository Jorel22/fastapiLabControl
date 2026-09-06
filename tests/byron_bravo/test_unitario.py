"""Pruebas unitarias — Byron Bravo.

Técnica asignada: TRANSICIÓN DE ESTADOS.
Funciones bajo prueba: `transicion_permitida()` y `siguiente_estado()`
de `app.services.validaciones`.
Reglas de negocio: R05 y R06 (RF-008) — un bien activo puede darse de
baja de forma lógica conservando su histórico, y un bien dado de baja
puede reactivarse.

Estas pruebas no levantan la aplicación ni abren la base de datos:
ejercitan la máquina de estados como estructura de datos pura. Eso
permite verificar propiedades de la SECUENCIA —reversibilidad, ausencia
de estados intermedios, cierre del conjunto— que a través de HTTP
exigirían varias peticiones encadenadas.

Ejecución:
    pytest tests/byron_bravo/test_unitario.py -v
"""
import pytest

from app.models.bien import ESTADOS
from app.services.validaciones import (
    TRANSICIONES_VALIDAS,
    siguiente_estado,
    transicion_permitida,
)

EVENTOS = ("baja", "reactivar")


# ==========================================================================
# TRANSICIONES VÁLIDAS
# ==========================================================================


def test_baja_desde_activo_es_valida():
    """R05 · activo --baja--> dado_de_baja."""
    assert transicion_permitida("activo", "baja") is True
    assert siguiente_estado("activo", "baja") == "dado_de_baja"


def test_reactivacion_desde_dado_de_baja_es_valida():
    """R06 · dado_de_baja --reactivar--> activo."""
    assert transicion_permitida("dado_de_baja", "reactivar") is True
    assert siguiente_estado("dado_de_baja", "reactivar") == "activo"


# ==========================================================================
# TRANSICIONES INVÁLIDAS — respaldan CP15 y CP17
# ==========================================================================
# No alteran el dato, pero sí la traza de auditoría exigida por RF-008:
# cada repetición deja una operación registrada que nunca ocurrió.


def test_baja_sobre_un_bien_ya_dado_de_baja_es_invalida():
    """Respalda CP15 · dar de baja dos veces el mismo bien."""
    assert transicion_permitida("dado_de_baja", "baja") is False
    assert siguiente_estado("dado_de_baja", "baja") is None


def test_reactivar_un_bien_ya_activo_es_invalida():
    """Respalda CP17 · reactivar un bien que nunca se dio de baja."""
    assert transicion_permitida("activo", "reactivar") is False
    assert siguiente_estado("activo", "reactivar") is None


# ==========================================================================
# PROPIEDADES DE LA SECUENCIA
# ==========================================================================
# Lo que distingue a esta técnica de las otras tres: verificar el
# comportamiento a lo largo del tiempo, no dentro de una operación aislada.


def test_el_ciclo_completo_regresa_al_estado_de_origen():
    """La baja lógica es reversible: activo → dado_de_baja → activo.

    Es la propiedad central de R05/R06: la baja no es física, así que el
    bien debe poder volver exactamente al estado del que partió.
    """
    intermedio = siguiente_estado("activo", "baja")
    assert intermedio == "dado_de_baja"
    assert siguiente_estado(intermedio, "reactivar") == "activo"


def test_no_existe_ningun_estado_fuera_del_catalogo():
    """Ninguna transición puede producir un estado ajeno a ESTADOS.

    Protege la restricción CHECK del modelo: si alguien añadiera una
    transición hacia un estado nuevo sin declararlo, la inserción fallaría
    en la base de datos en tiempo de ejecución en lugar de aquí.
    """
    for destino in TRANSICIONES_VALIDAS.values():
        assert destino in ESTADOS


@pytest.mark.parametrize("estado", list(ESTADOS))
@pytest.mark.parametrize("evento", list(EVENTOS))
def test_cada_estado_admite_exactamente_un_evento(estado, evento):
    """Recorrido exhaustivo de la matriz 2x2 estado x evento.

    Cuatro combinaciones, dos válidas y dos inválidas. La máquina de
    estados es lo bastante pequeña como para recorrerla entera, lo que
    elimina cualquier duda sobre casos no contemplados.
    """
    esperado = (estado, evento) in {("activo", "baja"), ("dado_de_baja", "reactivar")}
    assert transicion_permitida(estado, evento) is esperado


# ==========================================================================
# ROBUSTEZ
# ==========================================================================


@pytest.mark.parametrize(
    "estado, evento",
    [
        ("ACTIVO", "baja"),          # el catálogo de estados es en minúsculas
        ("activo", "BAJA"),          # el evento también
        ("eliminado", "baja"),       # estado inexistente
        ("activo", "eliminar"),      # evento inexistente
        (None, "baja"),              # estado ausente
        ("activo", None),            # evento ausente
    ],
)
def test_los_valores_desconocidos_no_producen_transicion(estado, evento):
    """Cualquier par no declarado se rechaza, en vez de fallar por excepción."""
    assert transicion_permitida(estado, evento) is False
    assert siguiente_estado(estado, evento) is None
