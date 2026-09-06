"""Pruebas unitarias — Jordan Montenegro.

Técnica asignada: PARTICIÓN DE EQUIVALENCIA.
Función bajo prueba: `app.services.validaciones.tipo_es_valido()`.
Regla de negocio: R02 (RF-002) — el tipo de equipo registrado debe
pertenecer al catálogo institucional cerrado de siete valores.

Estas pruebas no levantan la aplicación, no abren la base de datos y no
hacen ninguna petición HTTP: ejercitan una función pura, por lo que la
suite completa corre en milisegundos y, cuando una falla, el defecto está
en esa función y en ninguna otra parte.

La misma partición de clases que se aplica aquí se aplica en
test_api_particion_equivalencia.py a nivel de API. La diferencia es el
nivel de prueba, no el diseño de los casos: aquí se comprueba la REGLA,
allí se comprueba que la API la APLIQUE.

Ejecución:
    pytest tests/jordan_montenegro/test_unitario.py -v
"""
import pytest

from app.models.bien import TIPOS_EQUIPO
from app.services.validaciones import tipo_es_valido


# ==========================================================================
# CLASE VÁLIDA — el valor pertenece al catálogo institucional
# ==========================================================================
# Se prueban los siete valores y no solo un representante porque el
# catálogo es finito y muy pequeño: cuando la clase válida es enumerable,
# recorrerla entera cuesta lo mismo que elegir un representante y elimina
# el riesgo de que la implementación reconozca unos valores y otros no.


@pytest.mark.parametrize("tipo", list(TIPOS_EQUIPO))
def test_los_siete_tipos_del_catalogo_son_validos(tipo):
    """Todo valor del catálogo institucional debe aceptarse."""
    assert tipo_es_valido(tipo) is True


def test_el_catalogo_tiene_exactamente_siete_valores():
    """El catálogo es cerrado: si alguien lo amplía, esta prueba lo avisa.

    Es una prueba de contrato, no de comportamiento: protege la partición
    frente a un cambio silencioso en la definición del dominio, que
    invalidaría las clases de equivalencia diseñadas en la Tarea 4.
    """
    assert len(TIPOS_EQUIPO) == 7


# ==========================================================================
# CLASES INVÁLIDAS — cuatro clases distintas, no una sola
# ==========================================================================
# Agruparlas en una única clase «valor inválido» dejaría validaciones sin
# verificar: un sistema puede rechazar correctamente el valor ajeno al
# catálogo y aceptar la cadena vacía, porque cada una recorre una ruta de
# código distinta (pertenencia, obligatoriedad, normalización).


def test_valor_ajeno_al_catalogo_se_rechaza():
    """Clase inválida 1 · sintácticamente correcto pero fuera del catálogo."""
    assert tipo_es_valido("impresora_laser") is False


def test_campo_ausente_se_rechaza():
    """Clase inválida 2 · el campo obligatorio no se envía (None)."""
    assert tipo_es_valido(None) is False


def test_cadena_vacia_se_rechaza():
    """Clase inválida 3 · cadena vacía.

    Distinta de «campo ausente»: el campo llega, pero sin contenido. Un
    sistema puede tratar `None` y `""` de forma diferente.
    """
    assert tipo_es_valido("") is False


@pytest.mark.parametrize("tipo", ["COMPUTADORA", "Computadora", "cOmPuTaDoRa"])
def test_el_catalogo_distingue_mayusculas(tipo):
    """Clase inválida 4 · variante de capitalización.

    El catálogo se define en minúsculas y es un identificador, no texto
    libre. Aceptar variantes de capitalización produciría filas que el
    filtro por tipo del inventario no encontraría nunca.
    """
    assert tipo_es_valido(tipo) is False


@pytest.mark.parametrize("tipo", ["  computadora", "computadora  ", "  computadora  "])
def test_los_espacios_sin_recortar_se_rechazan(tipo):
    """Clase inválida 5 · el valor correcto rodeado de espacios.

    Es el defecto más silencioso de la partición: a la vista humana el
    dato es correcto, pero para la base de datos es un valor distinto.
    """
    assert tipo_es_valido(tipo) is False


# ==========================================================================
# ROBUSTEZ DE TIPO — valores que no son cadenas
# ==========================================================================
# Solo comprobable a este nivel: la API recibe JSON y Pydantic convertiría
# algunos de estos valores antes de que la regla llegara a evaluarlos.


@pytest.mark.parametrize("valor", [1, 0, True, False, [], {}, ["computadora"]])
def test_los_valores_que_no_son_cadenas_se_rechazan(valor):
    """Ningún valor no textual puede pasar por un tipo de equipo."""
    assert tipo_es_valido(valor) is False
