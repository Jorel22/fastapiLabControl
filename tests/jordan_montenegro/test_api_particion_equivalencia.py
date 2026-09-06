"""Pruebas automatizadas de API — Jordan Montenegro.

Técnica asignada: PARTICIÓN DE EQUIVALENCIA.
Regla de negocio: R02 (RF-002) — el tipo de equipo registrado debe
pertenecer al catálogo institucional cerrado de siete valores.
Endpoint: POST /api/bienes

JUSTIFICACIÓN DE LA TÉCNICA
---------------------------
El campo `tipo` no admite un rango numérico sino un dominio enumerado y
cerrado de siete valores, frente a un universo prácticamente infinito de
cadenas inválidas. La partición de equivalencia es la técnica adecuada
para dominios de este tipo: divide ese universo en clases cuyo
comportamiento esperado es homogéneo, de modo que probar un representante
de cada clase equivale a probar la clase completa.

Se definieron una clase válida y CINCO clases inválidas de naturaleza
distinta, en lugar de una sola. Agruparlas sería un error de diseño: cada
una incumple una regla diferente y recorre una ruta de código diferente
—pertenencia al catálogo, obligatoriedad del campo, normalización de la
cadena—, de manera que un sistema puede rechazar correctamente una y
aceptar otra. La evidencia lo confirma: CP03 y CP20 acaban ambos con el
tipo en NULL, pero por caminos distintos.

MATRIZ DE CASOS
---------------
    Caso    Clase                            Valor                 Esperado
    ------  -------------------------------  --------------------  --------
    CP01    Válida · representante 1         "computadora"         201
    CP19    Válida · representante 2         "aire_acondicionado"  201
    CP02    Inválida · fuera del catálogo    "impresora_laser"     422
    CP03    Inválida · campo ausente         (omitido)             422
    CP20    Inválida · cadena vacía          ""                    422
    CP21    Inválida · mayúsculas            "COMPUTADORA"         422
    CP22    Inválida · espacios sin recortar "  computadora  "     422

CP01, CP02 y CP03 proceden de la matriz consolidada de la Unidad 2.
CP19 a CP22 se diseñaron para esta tarea: amplían la partición con un
segundo representante de la clase válida y tres clases inválidas que la
matriz original no cubría.

DEFECTOS
--------
Cinco de los siete casos resultan NO CUMPLIDOS: la API no valida el campo
`tipo` contra el catálogo en ningún punto. Se automatizan afirmando el
resultado ESPERADO y se marcan con `xfail(strict=True)`, de modo que la
suite queda en verde, el defecto queda documentado en el código, y si
alguien corrige la API el xfail pasa a XPASS y la suite falla avisando de
que hay que retirar la marca.

Ejecución:
    pytest tests/jordan_montenegro/test_api_particion_equivalencia.py -v
"""
import pytest

# Prefijo acordado en la Tarea 4 para los registros generados por pruebas.
PREFIJO = "TEST-CN"

# Marca de técnica: permite ejecutar solo esta partición con `-m particion`.
pytestmark = pytest.mark.particion


def cuerpo_alta(codigo, **sobrescribir):
    """Cuerpo válido de alta de un bien.

    Los kwargs sustituyen campos; pasar un campo con valor `...` (Ellipsis)
    lo omite de la solicitud, que es como se construye CP03.
    """
    datos = {
        "codigo_bien": codigo,
        "nombre": f"Equipo de pruebas {codigo}",
        "numero_serie": f"SN-{codigo}",
        "tipo": "computadora",
        "laboratorio_id": 1,
        "custodio_id": 1,
    }
    datos.update(sobrescribir)
    return {clave: valor for clave, valor in datos.items() if valor is not ...}


# ==========================================================================
# CLASE VÁLIDA — el valor pertenece al catálogo institucional
# ==========================================================================


def test_CP01_tipo_computadora(cliente_admin):
    """CP01 · Clase válida, primer representante: tipo = "computadora"."""
    r = cliente_admin.post("/api/bienes", json=cuerpo_alta(f"{PREFIJO}-01"))

    assert r.status_code == 201
    assert r.json()["bien"]["tipo"] == "computadora"
    assert r.json()["bien"]["estado"] == "activo"


def test_CP19_tipo_aire_acondicionado(cliente_admin):
    """CP19 · Clase válida, segundo representante: tipo = "aire_acondicionado".

    Un único representante no bastaría para dar por probada la clase: si la
    API reconociera solo el primer valor del catálogo, un caso aislado no lo
    detectaría. Este caso confirma que la clase válida no se reduce a un
    valor privilegiado.
    """
    r = cliente_admin.post(
        "/api/bienes", json=cuerpo_alta(f"{PREFIJO}-19", tipo="aire_acondicionado")
    )

    assert r.status_code == 201
    assert r.json()["bien"]["tipo"] == "aire_acondicionado"


# ==========================================================================
# CLASES INVÁLIDAS
# ==========================================================================


@pytest.mark.xfail(
    strict=True,
    reason="CP02 · Defecto: la API acepta tipos ajenos al catálogo institucional. "
           "El esquema declara `tipo: Optional[str]` sin restringirlo a TIPOS_EQUIPO, "
           "pese a que esa tupla ya está definida en app/models/bien.py.",
)
def test_CP02_tipo_fuera_del_catalogo(cliente_admin):
    """CP02 · Clase inválida 1: valor correcto en forma, ajeno al catálogo."""
    r = cliente_admin.post(
        "/api/bienes", json=cuerpo_alta(f"{PREFIJO}-02", tipo="impresora_laser")
    )

    assert r.status_code == 422, (
        "Un tipo que no pertenece al catálogo institucional debe rechazarse; "
        "aceptarlo incumple el RF-002 y rompe el filtro por tipo del inventario"
    )


@pytest.mark.xfail(
    strict=True,
    reason="CP03 · Defecto: el campo obligatorio ausente se convierte en NULL en vez "
           "de rechazarse (bien_service: `if not tipo_val: tipo_val = None`).",
)
def test_CP03_campo_tipo_ausente(cliente_admin):
    """CP03 · Clase inválida 2: el campo obligatorio no se envía."""
    r = cliente_admin.post("/api/bienes", json=cuerpo_alta(f"{PREFIJO}-03", tipo=...))

    assert r.status_code == 422, "El tipo es obligatorio y su ausencia debe rechazarse"


@pytest.mark.xfail(
    strict=True,
    reason="CP20 · Defecto: la cadena vacía se normaliza a NULL y el alta se acepta. "
           "El bien queda registrado sin tipo, igual que en CP03 pero por otra ruta.",
)
def test_CP20_tipo_cadena_vacia(cliente_admin):
    """CP20 · Clase inválida 3: el campo llega, pero vacío.

    Clase distinta de CP03: allí el campo no se envía y aquí sí. Que ambos
    terminen con el tipo en NULL es precisamente el hallazgo — desde fuera
    las dos violaciones son indistinguibles, así que el consumidor de la API
    no puede saber cuál de las dos reglas incumplió.
    """
    r = cliente_admin.post("/api/bienes", json=cuerpo_alta(f"{PREFIJO}-20", tipo=""))

    assert r.status_code == 422, "Una cadena vacía no pertenece al catálogo"


@pytest.mark.xfail(
    strict=True,
    reason="CP21 · Defecto: el catálogo no distingue mayúsculas y 'COMPUTADORA' se "
           "almacena literalmente, generando un valor que ningún filtro encontrará.",
)
def test_CP21_tipo_en_mayusculas(cliente_admin):
    """CP21 · Clase inválida 4: variante de capitalización.

    `tipo` es un identificador de catálogo, no texto libre. Almacenar
    "COMPUTADORA" crea una fila que el filtro `?tipo=computadora` del
    listado de inventario nunca devolverá.
    """
    r = cliente_admin.post(
        "/api/bienes", json=cuerpo_alta(f"{PREFIJO}-21", tipo="COMPUTADORA")
    )

    assert r.status_code == 422, "El catálogo está definido en minúsculas"


@pytest.mark.xfail(
    strict=True,
    reason="CP22 · Defecto: el valor no se recorta antes de validarse ni de guardarse; "
           "'  computadora  ' se almacena con los espacios incluidos.",
)
def test_CP22_tipo_con_espacios_sin_recortar(cliente_admin):
    """CP22 · Clase inválida 5: el valor correcto rodeado de espacios.

    Es el caso más silencioso de la partición: en pantalla el dato parece
    correcto, pero para la base de datos es un valor distinto del catálogo.
    Se detecta comprobando el valor efectivamente persistido, no solo el
    código HTTP.
    """
    r = cliente_admin.post(
        "/api/bienes", json=cuerpo_alta(f"{PREFIJO}-22", tipo="  computadora  ")
    )

    assert r.status_code == 422, "El valor debe normalizarse antes de validarse"


# ==========================================================================
# VERIFICACIÓN DEL DATO PERSISTIDO
# ==========================================================================
# La partición se evalúa sobre el código HTTP, pero el impacto real de los
# defectos está en lo que queda almacenado. Esta prueba no duplica ningún
# caso: documenta la consecuencia de CP02, CP03, CP20, CP21 y CP22 sobre el
# inventario, y es la evidencia que sostiene la matriz de calidad de datos.


def test_consecuencia_de_los_defectos_sobre_el_inventario(cliente_admin):
    """Deja constancia de qué queda realmente guardado tras cada clase inválida."""
    persistido = {}
    for caso, tipo_enviado in [
        ("CP02", "impresora_laser"),
        ("CP20", ""),
        ("CP21", "COMPUTADORA"),
        ("CP22", "  computadora  "),
    ]:
        codigo = f"{PREFIJO}-V{caso[-2:]}"
        cliente_admin.post("/api/bienes", json=cuerpo_alta(codigo, tipo=tipo_enviado))
        respuesta = cliente_admin.get(f"/api/bienes/{codigo}")
        persistido[caso] = respuesta.json()["bien"]["tipo"]

    # Ninguno de los cuatro valores pertenece al catálogo institucional:
    # el inventario admitió cuatro registros con el tipo corrupto o vacío.
    assert persistido["CP02"] == "impresora_laser"
    assert persistido["CP20"] is None
    assert persistido["CP21"] == "COMPUTADORA"
    assert persistido["CP22"] == "  computadora  "
