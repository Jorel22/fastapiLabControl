# API Reference: LabControl Mecánica ESPOCH (FastAPI)

Este documento contiene la especificación completa y detallada de la API REST de **LabControl Mecánica ESPOCH**, optimizada para el consumo y comprensión por Modelos de Lenguaje (LLMs) y desarrolladores.

---

## 1. Información General

- **Nombre de la API**: LabControl Mecánica ESPOCH API
- **Versión**: 1.0.0
- **Base URL**: `http://localhost:5000` o `http://<host>:5000`
- **Prefijo global**: `/api`
- **Formato de datos**: `application/json` (excepto exportaciones CSV/PDF)

---

## 2. Autenticación y Autorización

### Mecanismo de Autenticación
La API utiliza JSON Web Tokens (**JWT**) con algoritmo **HS256**. El token puede enviarse mediante:
1. **Cookie HttpOnly**: `access_token_cookie=<token>` (automáticamente enviada por navegadores tras el login).
2. **Cabecera HTTP**: `Authorization: Bearer <token>`

### Roles y Perfiles de Usuario
- **`administrador`**: Técnico de laboratorios. Acceso total de lectura y escritura (alta, edición, baja, reactivación de bienes, registro de mantenimientos, software y gestión de cuentas).
- **`consulta`**: Decano, DTIC, auditoría. Acceso de solo lectura (consultar bienes, histórico técnico, software y reportes).

---

## 3. Códigos de Estado y Manejo de Errores

| Código | Significado | Descripción |
|---|---|---|
| `200 OK` | Éxito | Solicitud procesada correctamente. |
| `201 Created` | Creado | Recurso creado exitosamente. |
| `400 Bad Request` | Petición Inválida | Operación no permitida (ej. un admin intentando desactivar su propia cuenta). |
| `401 Unauthorized` | No Autenticado | Token ausente, expirado o credenciales inválidas. |
| `403 Forbidden` | Prohibido | Usuario autenticado pero sin rol suficiente (ej. rol `consulta` intentando escribir). |
| `404 Not Found` | No Encontrado | El recurso solicitado no existe. |
| `409 Conflict` | Conflicto | Registro duplicado (ej. código de bien o nombre de usuario ya existente). |
| `422 Unprocessable Entity` | Error de Validación | Campos obligatorios faltantes o valores fuera de rango/formato. |

### Formato Estándar de Error
```json
{
  "error": "Mensaje descriptivo del error."
}
```

---

## 4. Catálogos y Constantes

- **Tipos de Equipo (`tipo`)**:
  `"computadora"`, `"switch"`, `"access_point"`, `"proyector"`, `"pantalla_interactiva"`, `"aire_acondicionado"`, `"otro"`
- **Estados de Bien (`estado`)**:
  `"activo"`, `"dado_de_baja"`
- **Tipos de Mantenimiento (`tipo`)**:
  `"preventivo"`, `"correctivo"`
- **Estados de Licencia Software (`licencia`)**:
  `"activa"`, `"vencida"`
- **Perfiles de Usuario (`perfil`)**:
  `"administrador"`, `"consulta"`

---

## 5. Especificación de Endpoints

---

### Módulo: General & Verificación

#### `GET /api/`
- **Descripción**: Página inicial de bienvenida de la API.
- **Acceso**: Público.
- **Respuesta 200**:
  ```json
  {
    "status": "ok",
    "app": "LabControl Mecánica ESPOCH API",
    "version": "1.0.0"
  }
  ```

#### `GET /api/health`
- **Descripción**: Endpoint de monitoreo de salud del servicio (Health Check).
- **Acceso**: Público.
- **Respuesta 200**:
  ```json
  {
    "status": "ok",
    "app": "LabControl Mecánica ESPOCH API"
  }
  ```

---

### Módulo: Autenticación (`/api/auth`)

#### `POST /api/auth/login`
- **Descripción**: Inicia sesión. Retorna información del usuario y setea la cookie HttpOnly `access_token_cookie`.
- **Acceso**: Público.
- **Cuerpo de la Petición (JSON)**:
  ```json
  {
    "usuario": "admin",
    "password": "admin123"
  }
  ```
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "mensaje": "Bienvenido, admin.",
      "usuario": {
        "id": 1,
        "usuario": "admin",
        "perfil": "administrador",
        "activo": true
      }
    }
    ```
    *Set-Cookie: access_token_cookie=<jwt>; HttpOnly; Path=/; Max-Age=1800; SameSite=Lax*
  - `401 Unauthorized`:
    ```json
    {
      "error": "Usuario o contraseña incorrectos."
    }
    ```

#### `POST /api/auth/logout`
- **Descripción**: Cierra la sesión activa eliminando la cookie JWT.
- **Acceso**: Público / Autenticado.
- **Respuesta 200**:
  ```json
  {
    "mensaje": "Sesión cerrada."
  }
  ```

#### `GET /api/auth/perfil`
- **Descripción**: Obtiene los datos del usuario actualmente autenticado.
- **Acceso**: Requiere autenticación (`administrador` o `consulta`).
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "usuario": {
        "id": 1,
        "usuario": "admin",
        "perfil": "administrador",
        "activo": true
      }
    }
    ```
  - `401 Unauthorized`: `{"error": "Falta el token de autenticación."}`

---

### Módulo: Inventario de Bienes (`/api/bienes`)

#### `GET /api/bienes`
- **Descripción**: Lista todos los bienes institucionales con filtros opcionales y retorna los catálogos para filtros en UI.
- **Acceso**: Requiere autenticación (`administrador` o `consulta`).
- **Parámetros Query (opcionales)**:
  - `laboratorio_id` *(int)*: Filtrar por ID de laboratorio.
  - `tipo` *(string)*: Filtrar por tipo (`computadora`, `switch`, etc.).
  - `estado` *(string)*: Filtrar por estado (`activo`, `dado_de_baja`).
- **Respuesta 200**:
  ```json
  {
    "bienes": [
      {
        "codigo_bien": "ESPOCH-PC-001",
        "numero_serie": "SN123456",
        "nombre": "PC Dell OptiPlex 7090",
        "descripcion": "Core i7 16GB RAM SSD 512GB",
        "tipo": "computadora",
        "laboratorio_id": 1,
        "custodio_id": 1,
        "estado": "activo",
        "laboratorio": "Laboratorio 1",
        "custodio": "Ing. Carlos Pérez"
      }
    ],
    "catalogos": {
      "laboratorios": [
        {"id": 1, "nombre": "Laboratorio 1", "ubicacion": "Facultad de Mecánica - ESPOCH"}
      ],
      "custodios": [
        {"id": 1, "nombre": "Ing. Carlos Pérez", "cargo": "Técnico de Laboratorios"}
      ],
      "tipos": ["computadora", "switch", "access_point", "proyector", "pantalla_interactiva", "aire_acondicionado", "otro"],
      "estados": ["activo", "dado_de_baja"]
    }
  }
  ```

#### `GET /api/bienes/{codigo}`
- **Descripción**: Obtiene el detalle de un bien específico mediante su código único.
- **Acceso**: Requiere autenticación (`administrador` o `consulta`).
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "bien": {
        "codigo_bien": "ESPOCH-PC-001",
        "numero_serie": "SN123456",
        "nombre": "PC Dell OptiPlex 7090",
        "descripcion": "Descripción del equipo",
        "tipo": "computadora",
        "laboratorio_id": 1,
        "custodio_id": 1,
        "estado": "activo",
        "laboratorio": "Laboratorio 1",
        "custodio": "Ing. Carlos Pérez"
      }
    }
    ```
  - `404 Not Found`: `{"error": "No existe el bien 'ESPOCH-PC-999'"}`

#### `POST /api/bienes`
- **Descripción**: Registra un nuevo bien en el inventario. Genera traza de auditoría de alta.
- **Acceso**: Requiere rol `administrador`.
- **Cuerpo de la Petición (JSON)**:
  ```json
  {
    "codigo_bien": "ESPOCH-PC-010",
    "nombre": "PC Lenovo ThinkCentre M70",
    "numero_serie": "LN987654",
    "descripcion": "Equipo asignado a prácticas",
    "tipo": "computadora",
    "laboratorio_id": 1,
    "custodio_id": 1
  }
  ```
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "mensaje": "Bien 'ESPOCH-PC-010' registrado.",
      "bien": {
        "codigo_bien": "ESPOCH-PC-010",
        "numero_serie": "LN987654",
        "nombre": "PC Lenovo ThinkCentre M70",
        "descripcion": "Equipo asignado a prácticas",
        "tipo": "computadora",
        "laboratorio_id": 1,
        "custodio_id": 1,
        "estado": "activo",
        "laboratorio": "Laboratorio 1",
        "custodio": "Ing. Carlos Pérez"
      }
    }
    ```
  - `409 Conflict`: `{"error": "Ya existe un bien con el código 'ESPOCH-PC-010'."}`
  - `422 Unprocessable Entity`: `{"error": "El código del bien es obligatorio."}`
  - `403 Forbidden`: `{"error": "Acceso restringido a administradores."}`

#### `PUT /api/bienes/{codigo}`
- **Descripción**: Edita los datos de un bien existente. Registra traza de auditoría con los campos modificados.
- **Acceso**: Requiere rol `administrador`.
- **Cuerpo de la Petición (JSON)**:
  ```json
  {
    "nombre": "PC Lenovo ThinkCentre Actualizada",
    "numero_serie": "LN987654-B",
    "descripcion": "Memoria ampliada a 32GB",
    "tipo": "computadora",
    "laboratorio_id": 2,
    "custodio_id": 1
  }
  ```
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "mensaje": "Bien 'ESPOCH-PC-010' actualizado.",
      "bien": { ... }
    }
    ```
  - `404 Not Found`: `{"error": "No existe el bien 'ESPOCH-PC-010'"}`

#### `POST /api/bienes/{codigo}/baja`
- **Descripción**: Da de baja lógica a un equipo (`estado: dado_de_baja`), conservando todo su historial y registrando auditoría.
- **Acceso**: Requiere rol `administrador`.
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "mensaje": "Bien 'ESPOCH-PC-010' dado de baja."
    }
    ```
  - `404 Not Found`: `{"error": "No existe el bien 'ESPOCH-PC-010'"}`

#### `POST /api/bienes/{codigo}/reactivar`
- **Descripción**: Reactiva un bien que estaba dado de baja (`estado: activo`) y registra auditoría.
- **Acceso**: Requiere rol `administrador`.
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "mensaje": "Bien 'ESPOCH-PC-010' reactivado."
    }
    ```
  - `404 Not Found`: `{"error": "No existe el bien 'ESPOCH-PC-010'"}`

---

### Módulo: Software y Licencias

#### `GET /api/bienes/{codigo}/software`
- **Descripción**: Lista todos los programas y licencias instalados en un equipo específico.
- **Acceso**: Requiere autenticación (`administrador` o `consulta`).
- **Respuesta 200**:
  ```json
  {
    "bien": { "codigo_bien": "ESPOCH-PC-001", "nombre": "PC Dell" },
    "softwares": [
      {
        "id": 1,
        "codigo_bien": "ESPOCH-PC-001",
        "nombre": "Kaspersky Endpoint Security",
        "licencia": "activa",
        "fecha_instalacion": "2026-01-15",
        "vencimiento": "2026-09-20",
        "num_escaneos": 45,
        "estado_licencia": "por_vencer",
        "dias_para_vencer": 20
      }
    ]
  }
  ```

#### `POST /api/bienes/{codigo}/software`
- **Descripción**: Asocia un software o licencia a un equipo tecnológico.
- **Acceso**: Requiere rol `administrador`.
- **Cuerpo de la Petición (JSON)**:
  ```json
  {
    "nombre": "AutoCAD 2025",
    "licencia": "activa",
    "fecha_instalacion": "2026-03-01",
    "vencimiento": "2027-03-01",
    "num_escaneos": 0
  }
  ```
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "mensaje": "Software registrado.",
      "software": {
        "id": 2,
        "codigo_bien": "ESPOCH-PC-001",
        "nombre": "AutoCAD 2025",
        "licencia": "activa",
        "fecha_instalacion": "2026-03-01",
        "vencimiento": "2027-03-01",
        "num_escaneos": 0,
        "estado_licencia": "vigente",
        "dias_para_vencer": 182
      }
    }
    ```
  - `422 Unprocessable Entity`: `{"error": "El nombre del software es obligatorio."}`
  - `404 Not Found`: `{"error": "No existe el bien 'ESPOCH-PC-001'"}`

---

### Módulo: Mantenimientos e Histórico Técnico

#### `POST /api/bienes/{codigo}/mantenimientos`
- **Descripción**: Registra una intervención técnica (`preventivo` o `correctivo`) sobre un equipo.
- **Acceso**: Requiere rol `administrador`.
- **Cuerpo de la Petición (JSON)**:
  ```json
  {
    "tipo": "correctivo",
    "fecha": "2026-08-30",
    "observaciones": "Reemplazo de fuente de poder 500W y limpieza de disipador."
  }
  ```
- **Validaciones de Negocio**:
  - `tipo` es obligatorio y debe ser `"preventivo"` o `"correctivo"`.
  - `fecha` es obligatoria en formato `AAAA-MM-DD` y **no puede ser una fecha futura**.
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "mensaje": "Mantenimiento registrado y agregado al histórico."
    }
    ```
  - `422 Unprocessable Entity`: `{"error": "La fecha no puede ser posterior a la actual."}`
  - `404 Not Found`: `{"error": "No existe el bien 'ESPOCH-PC-001'."}`

#### `GET /api/bienes/{codigo}/historico`
- **Descripción**: Obtiene el histórico cronológico (ascendente por fecha) de todas las intervenciones de un equipo.
- **Acceso**: Requiere autenticación (`administrador` o `consulta`).
- **Respuesta 200**:
  ```json
  {
    "bien": {
      "codigo_bien": "ESPOCH-PC-001",
      "nombre": "PC Dell OptiPlex 7090",
      "laboratorio": "Laboratorio 1",
      "custodio": "Ing. Carlos Pérez"
    },
    "registros": [
      {
        "id": 1,
        "codigo_bien": "ESPOCH-PC-001",
        "tipo": "preventivo",
        "fecha": "2026-05-10",
        "observaciones": "Limpieza general y lubricación de ventiladores.",
        "usuario_id": 1,
        "usuario": "admin"
      },
      {
        "id": 2,
        "codigo_bien": "ESPOCH-PC-001",
        "tipo": "correctivo",
        "fecha": "2026-08-30",
        "observaciones": "Reemplazo de fuente de poder 500W.",
        "usuario_id": 1,
        "usuario": "admin"
      }
    ]
  }
  ```

---

### Módulo: Informes y Reportes (`/api/reportes`)

#### `GET /api/reportes`
- **Descripción**: Genera informes consolidados de mantenimientos con filtros combinables y opción de exportación a archivo.
- **Acceso**: Requiere autenticación (`administrador` o `consulta`).
- **Parámetros Query (opcionales)**:
  - `semestre` *(string)*: Formato `"YYYY-A"` (enero–junio) o `"YYYY-B"` (julio–diciembre). Ej: `"2026-A"`.
  - `laboratorio_id` *(int)*: ID del laboratorio.
  - `tipo` *(string)*: `"preventivo"` o `"correctivo"`.
  - `codigo_bien` *(string)*: Código específico de bien.
  - `formato` *(string)*: Si se omite retorna JSON. Valores permitidos: `"csv"`, `"pdf"`.

- **Respuestas según `formato`**:
  1. **Sin formato (JSON estándar)**:
     ```json
     {
       "reporte": [
         {
           "id": 1,
           "codigo_bien": "ESPOCH-PC-001",
           "tipo": "preventivo",
           "fecha": "2026-05-10",
           "observaciones": "Limpieza general",
           "usuario_id": 1,
           "usuario": "admin"
         }
       ],
       "catalogos": {
         "laboratorios": [ ... ],
         "tipos": ["preventivo", "correctivo"],
         "semestres": ["2026-B", "2026-A", "2025-B"]
       }
     }
     ```
  2. **`formato=csv`**:
     - `Content-Type`: `text/csv; charset=utf-8`
     - `Content-Disposition`: `attachment; filename=reporte_mantenimientos.csv`
     - Incluye texto legal de conformidad con Normas de Control Interno (series 406/410) y tabla CSV.
  3. **`formato=pdf`**:
     - `Content-Type`: `application/pdf`
     - `Content-Disposition`: `attachment; filename=reporte_mantenimientos.pdf`
     - Documento PDF generado con ReportLab en formato horizontal (A4 landscape) con estilos y pie normativo.

---

### Módulo: Gestión de Usuarios (`/api/usuarios`)

#### `GET /api/usuarios`
- **Descripción**: Lista todas las cuentas registradas en el sistema.
- **Acceso**: Requiere rol `administrador`.
- **Respuesta 200**:
  ```json
  {
    "usuarios": [
      {"id": 1, "usuario": "admin", "perfil": "administrador", "activo": true},
      {"id": 2, "usuario": "decano", "perfil": "consulta", "activo": true},
      {"id": 3, "usuario": "dtic", "perfil": "consulta", "activo": true}
    ]
  }
  ```

#### `POST /api/usuarios`
- **Descripción**: Crea una nueva cuenta de usuario (generalmente de perfil `consulta`).
- **Acceso**: Requiere rol `administrador`.
- **Cuerpo de la Petición (JSON)**:
  ```json
  {
    "usuario": "auditor_externo",
    "password": "PasswordSeguro123",
    "perfil": "consulta"
  }
  ```
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "mensaje": "Cuenta 'auditor_externo' creada con éxito.",
      "usuario": {
        "id": 4,
        "usuario": "auditor_externo",
        "perfil": "consulta",
        "activo": true
      }
    }
    ```
  - `409 Conflict`: `{"error": "Ya existe el usuario 'auditor_externo'."}`
  - `422 Unprocessable Entity`: `{"error": "Todos los campos son obligatorios."}`

#### `POST /api/usuarios/{usuario_id}/estado`
- **Descripción**: Alterna el estado activo/inactivo de una cuenta (`activo: true <-> false`).
- **Acceso**: Requiere rol `administrador`.
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "mensaje": "Cuenta 'decano' actualizada.",
      "usuario": {
        "id": 2,
        "usuario": "decano",
        "perfil": "consulta",
        "activo": false
      }
    }
    ```
  - `400 Bad Request`: `{"error": "No puedes desactivar tu propia cuenta."}`
  - `404 Not Found`: `{"error": "La cuenta no existe."}`

#### `POST /api/usuarios/{usuario_id}/reset`
- **Descripción**: Restablece la contraseña de un usuario.
- **Acceso**: Requiere rol `administrador`.
- **Cuerpo de la Petición (JSON)**:
  ```json
  {
    "password": "NuevaPassword123"
  }
  ```
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "mensaje": "Contraseña restablecida con éxito."
    }
    ```
  - `422 Unprocessable Entity`: `{"error": "La nueva contraseña debe tener mínimo 6 caracteres."}`
  - `404 Not Found`: `{"error": "La cuenta no existe."}`

---

## 6. Ejemplos de Consumo con `curl`

### 1. Iniciar Sesión y Guardar Cookies
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "admin", "password": "admin123"}' \
  -c cookies.txt
```

### 2. Consultar Inventario con Filtros
```bash
curl -X GET "http://localhost:5000/api/bienes?tipo=computadora&estado=activo" \
  -b cookies.txt
```

### 3. Registrar un Nuevo Bien
```bash
curl -X POST http://localhost:5000/api/bienes \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "codigo_bien": "ESPOCH-PC-099",
    "nombre": "PC Core i9",
    "tipo": "computadora",
    "laboratorio_id": 1,
    "custodio_id": 1
  }'
```

### 4. Exportar Reporte en PDF
```bash
curl -X GET "http://localhost:5000/api/reportes?semestre=2026-A&formato=pdf" \
  -b cookies.txt \
  --output reporte_2026A.pdf
```
