# crud.py
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

# Importar modelos, persistencia y utilidades con nombres en español
import modelos
from modelos import Juego, JuegoCrear, Desarrollador, DesarrolladorCrear
from persistencia import (
    cargar_juegos, guardar_juegos,
    cargar_desarrolladores, guardar_desarrolladores
)