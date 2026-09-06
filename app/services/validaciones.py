"""Validadores de reglas de negocio del módulo de Inventario de Bienes.

Funciones puras: reciben un valor, devuelven un booleano o un estado, y no
tocan la base de datos, la sesión HTTP ni el reloj del sistema. Esa pureza
es lo que permite probarlas unitariamente sin levantar la aplicación.

Trazabilidad con la Matriz de Casos de Prueba (U2 · Tarea 4):

    Función                    Regla   Casos de prueba
    ------------------------   -----   -----------------------------
    tipo_es_valido             R02     CP01-CP03, CP19-CP22
    laboratorio_en_rango       R03     CP04-CP09
    transicion_permitida       R05,R06 CP14-CP17
    siguiente_estado           R05,R06 CP14, CP16

NOTA DE DISEÑO
--------------
Estas validaciones no existían cuando se ejecutó la Tarea 4, y esa ausencia
es la causa directa de cuatro de los seis casos NO CUMPLIDOS: la API acepta
tipos ajenos al catálogo (CP02, CP03) y laboratorios fuera del rango
(CP04, CP09). El módulo se añade aquí como capa de validación reutilizable;
conectarlo a `bien_service.crear_bien()` corrige esos cuatro defectos.

El catálogo de tipos se importa de `app.models.bien` en lugar de repetirse:
la tupla TIPOS_EQUIPO ya estaba declarada allí desde el inicio del proyecto
—documentando el catálogo institucional— pero nunca se usaba para validar
nada. Reutilizarla mantiene una única fuente de verdad.
"""
from app.models.bien import ESTADOS, TIPOS_EQUIPO

# R03 — La Facultad de Mecánica cuenta con seis laboratorios de cómputo,
# de modo que el identificador válido es el intervalo cerrado [1, 6].
LABORATORIO_MINIMO = 1
LABORATORIO_MAXIMO = 6

# R05 / R06 — Ciclo de vida del bien. La baja es lógica, no física: el
# registro conserva su código y su histórico técnico, y la transición es
# reversible. Solo estas dos combinaciones (estado, evento) son válidas.
TRANSICIONES_VALIDAS = {
    ("activo", "baja"): "dado_de_baja",
    ("dado_de_baja", "reactivar"): "activo",
}


def tipo_es_valido(tipo) -> bool:
    """R02 · El tipo de equipo debe pertenecer al catálogo institucional.

    Rechaza, además del valor ajeno al catálogo, todo lo que no sea una
    cadena exactamente igual a uno de los siete valores: `None` (campo
    ausente), la cadena vacía, las variantes de mayúsculas y las cadenas
    con espacios sin recortar. Son clases de equivalencia distintas que un
    sistema podría tratar de forma distinta, así que se comprueban todas.

    >>> tipo_es_valido("computadora")
    True
    >>> tipo_es_valido("COMPUTADORA")
    False
    """
    return isinstance(tipo, str) and tipo in TIPOS_EQUIPO


def laboratorio_en_rango(laboratorio_id) -> bool:
    """R03 · El laboratorio de asignación debe estar en el intervalo [1, 6].

    Descarta explícitamente los booleanos: en Python `True == 1`, de modo
    que sin esta comprobación `laboratorio_en_rango(True)` devolvería True
    y se aceptaría un booleano como identificador de laboratorio.

    >>> laboratorio_en_rango(6)
    True
    >>> laboratorio_en_rango(True)
    False
    """
    if isinstance(laboratorio_id, bool) or not isinstance(laboratorio_id, int):
        return False
    return LABORATORIO_MINIMO <= laboratorio_id <= LABORATORIO_MAXIMO


def estado_es_valido(estado) -> bool:
    """El estado de un bien solo puede ser 'activo' o 'dado_de_baja'."""
    return isinstance(estado, str) and estado in ESTADOS


def transicion_permitida(estado_actual, evento) -> bool:
    """R05 / R06 · Indica si el evento es aplicable desde el estado actual.

    Dar de baja un bien ya dado de baja, o reactivar uno que ya está
    activo, son transiciones inválidas: no alteran el dato pero ensucian
    la traza de auditoría exigida por RF-008.

    >>> transicion_permitida("activo", "baja")
    True
    >>> transicion_permitida("dado_de_baja", "baja")
    False
    """
    return (estado_actual, evento) in TRANSICIONES_VALIDAS


def siguiente_estado(estado_actual, evento):
    """R05 / R06 · Estado resultante, o None si la transición no es válida.

    >>> siguiente_estado("activo", "baja")
    'dado_de_baja'
    >>> siguiente_estado("activo", "reactivar") is None
    True
    """
    return TRANSICIONES_VALIDAS.get((estado_actual, evento))
