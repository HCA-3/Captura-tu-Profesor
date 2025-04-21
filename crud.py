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
from utilidades import obtener_siguiente_id

# --- Almacenamiento en Memoria (Caché) ---
# Cargamos los datos al iniciar el módulo
try:
    # Usamos listas de diccionarios internamente para la manipulación
    _db_juegos: List[Dict[str, Any]] = cargar_juegos()
    _db_desarrolladores: List[Dict[str, Any]] = cargar_desarrolladores()
except HTTPException as e:
    print(f"Error crítico al cargar datos iniciales: {e.detail}. Iniciando con datos vacíos.")
    _db_juegos = []
    _db_desarrolladores = []
