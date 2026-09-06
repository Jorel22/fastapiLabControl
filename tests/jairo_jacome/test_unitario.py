"""Pruebas unitarias — Jairo Jácome.

Técnica asignada: ANÁLISIS DE VALORES LÍMITE.
Función bajo prueba: `app.services.validaciones.laboratorio_en_rango()`.
Regla de negocio: R03 (RF-002, integridad) — todo bien debe asignarse a un
laboratorio existente. La Facultad de Mecánica cuenta con seis laboratorios
de cómputo, por lo que el identificador válido es el intervalo cerrado [1, 6].

Los errores de programación se concentran en los bordes de un rango: se
producen al escribir «mayor que» en lugar de «mayor o igual que», o al
contar desde cero. Por eso se evalúan los seis valores del borde —0, 1, 2,
5, 6 y 7— en vez de valores del interior: verifican a la vez que los
límites estén INCLUIDOS y que los adyacentes queden EXCLUIDOS.

Ejecución:
    pytest tests/jairo_jacome/test_unitario.py -v
"""
import pytest

from app.services.validaciones import (
    LABORATORIO_MAXIMO,
    LABORATORIO_MINIMO,
    laboratorio_en_rango,
)


# ==========================================================================
# LOS SEIS VALORES DEL BORDE — respaldan CP04 a CP09
# ==========================================================================


@pytest.mark.parametrize(
    "caso, laboratorio_id, esperado, frontera",
    [
        ("CP04", 0, False, "debajo del mínimo"),
        ("CP05", 1, True, "límite mínimo"),
        ("CP06", 2, True, "cerca del mínimo"),
        ("CP07", 5, True, "cerca del máximo"),
        ("CP08", 6, True, "límite máximo"),
        ("CP09", 7, False, "sobre el máximo"),
    ],
)
def test_rango_de_laboratorio(caso, laboratorio_id, esperado, frontera):
    """Recorre el borde completo del intervalo [1, 6]."""
    assert laboratorio_en_rango(laboratorio_id) is esperado, (
        f"{caso} · {frontera}: el valor {laboratorio_id} debería "
        f"{'aceptarse' if esperado else 'rechazarse'}"
    )


def test_los_limites_estan_incluidos_en_el_intervalo():
    """El intervalo es CERRADO: 1 y 6 son valores válidos, no exclusivos.

    Es la comprobación que distingue `<=` de `<`, el error off-by-one que
    la técnica busca detectar.
    """
    assert laboratorio_en_rango(LABORATORIO_MINIMO) is True
    assert laboratorio_en_rango(LABORATORIO_MAXIMO) is True
    assert laboratorio_en_rango(LABORATORIO_MINIMO - 1) is False
    assert laboratorio_en_rango(LABORATORIO_MAXIMO + 1) is False


# ==========================================================================
# VALORES EXTREMOS
# ==========================================================================


@pytest.mark.parametrize("valor", [-1, -100, 999, 2**31])
def test_los_valores_muy_alejados_del_rango_se_rechazan(valor):
    """Ningún entero fuera del intervalo se acepta, por lejos que esté."""
    assert laboratorio_en_rango(valor) is False


# ==========================================================================
# ROBUSTEZ DE TIPO
# ==========================================================================
# Solo comprobable a nivel unitario: a través de HTTP, Pydantic convertiría
# algunos de estos valores antes de que la regla llegara a evaluarlos.


def test_un_booleano_no_es_un_identificador_de_laboratorio():
    """En Python `True == 1` y `False == 0`.

    Sin una comprobación explícita de tipo, `laboratorio_en_rango(True)`
    devolvería True y se aceptaría un booleano como identificador de
    laboratorio. Es un defecto que solo aparece al pensar la función por
    separado del endpoint: a través de la API nunca se habría probado.
    """
    assert laboratorio_en_rango(True) is False
    assert laboratorio_en_rango(False) is False


@pytest.mark.parametrize("valor", [None, "", "1", "uno", 1.0, 1.5, [], {}, [1]])
def test_los_valores_que_no_son_enteros_se_rechazan(valor):
    """La cadena "1" tampoco vale: el identificador es un entero, no texto.

    Incluye 1.0: un flotante que coincide numéricamente con un laboratorio
    válido sigue siendo un tipo incorrecto para una clave foránea.
    """
    assert laboratorio_en_rango(valor) is False
