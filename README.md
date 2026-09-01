# LabControl Mecánica ESPOCH (FastAPI)

API REST de control de inventario y mantenimientos de laboratorios para la Facultad de Mecánica de la Escuela Superior Politécnica de Chimborazo (ESPOCH).

Desarrollada con **FastAPI**, **SQLAlchemy**, **Pydantic** y **SQLite**.

---

## Características

- **Autenticación y Seguridad**: JWT con cookies HttpOnly y soporte de Bearer Token en headers HTTP. Roles: `administrador` (técnico) y `consulta` (decano, DTIC).
- **Inventario de Bienes**: Control de equipos, números de serie, laboratorios, custodios y estados (activo / dado de baja).
- **Mantenimientos e Histórico**: Registro de mantenimientos preventivos y correctivos con validación de fechas e histórico cronológico.
- **Software y Licencias**: Seguimiento de licencias activas, vencidas o próximas a vencer (alerta a 30 días) y número de escaneos.
- **Informes y Planes**: Generación y filtrado de reportes por semestre, laboratorio, tipo o bien, con exportación a **CSV** y **PDF** (ReportLab) conforme a las Normas de Control Interno (series 406 y 410).
- **Auditoría**: Traza completa de operaciones de escritura (alta, edición, baja, reactivación).
- **Documentación Interactiva Automática**: Swagger UI en `/docs` y ReDoc en `/redoc`.

---

## Requisitos y Configuración

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Variables de entorno (opcional en `.env`):
   ```env
   SECRET_KEY=cambia-esta-clave-en-produccion
   JWT_SECRET_KEY=cambia-esta-clave-jwt
   DATABASE_URL=sqlite:///labcontrol.db
   ```

3. Cargar datos iniciales (6 laboratorios y usuario administrador `admin` / `admin123`):
   ```bash
   python seed.py
   ```

4. (Opcional) Cargar datos de demostración completos:
   ```bash
   python seed_demo.py
   ```

---

## Ejecución del Servidor

```bash
python run.py
```

El servidor iniciará en: `http://localhost:5000`

- **Swagger UI**: [http://localhost:5000/docs](http://localhost:5000/docs)
- **ReDoc**: [http://localhost:5000/redoc](http://localhost:5000/redoc)
- **OpenAPI JSON**: [http://localhost:5000/openapi.json](http://localhost:5000/openapi.json)
- **Health Check**: [http://localhost:5000/api/health](http://localhost:5000/api/health)

---

## Ejecutar Pruebas

```bash
pytest tests/ -v
```
