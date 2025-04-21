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