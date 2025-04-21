from fastapi import FastAPI, HTTPException, Depends, status, Query
from typing import List, Optional

# Importar módulos con nombres en español
import crud
import modelos # Importa los modelos Pydantic en español
from modelos import Juego, JuegoCrear, Desarrollador, DesarrolladorCrear

# --- Creación de la Aplicación FastAPI ---
app = FastAPI(
    title="API CapturaTuProfesor - Videojuegos",
    description="Una API para gestionar información de videojuegos y desarrolladores.",
    version="1.0.0"
)

# --- Manejo de Excepciones Global ---
@app.exception_handler(Exception)
async def manejador_excepciones_generico(request, exc: Exception):
    # Aquí podrías añadir logging del error 'exc'
    print(f"Error no manejado detectado: {exc}") # Log simple a consola
    # Devuelve una respuesta HTTP 500 estándar
    # Nota: No uses HTTPException directamente aquí, retorna una Response o usa la utilidad de FastAPI
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )