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

# --- Operaciones CRUD para Desarrolladores ---

def obtener_desarrollador_por_id(id_desarrollador: int) -> Optional[Dict[str, Any]]:
    """Busca un desarrollador por ID (incluyendo borrados lógicamente)."""
    for dev in _db_desarrolladores:
        # Usamos .get() para evitar KeyError si el campo falta por alguna razón
        if dev.get("id") == id_desarrollador:
            return dev
    return None

def obtener_desarrollador_activo_por_id(id_desarrollador: int) -> Optional[Dict[str, Any]]:
    """Busca un desarrollador activo (no eliminado) por ID."""
    dev = obtener_desarrollador_por_id(id_desarrollador)
    # Comprueba que exista y que 'esta_eliminado' sea False o None (consideramos None como no eliminado)
    if dev and not dev.get("esta_eliminado", False):
        return dev
    return None