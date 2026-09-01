"""Punto de entrada de la aplicación LabControl Mecánica ESPOCH (FastAPI).

Uso:
    python run.py
    # o bien:
    uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=settings.DEBUG,
    )
