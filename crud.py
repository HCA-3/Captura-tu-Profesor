from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
import modelos
from modelos import Juego, JuegoCrear, JuegoBase 
from persistencia import cargar_juegos, guardar_juegos
from utilidades import obtener_siguiente_id

try:
    _db_juegos: List[Dict[str, Any]] = cargar_juegos()
except HTTPException as e:
    print(f"Error crítico al cargar datos iniciales de juegos: {e.detail}. Iniciando con datos vacíos.")
    _db_juegos = []


def obtener_juego_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    """Busca un juego por ID (incluyendo borrados lógicamente)."""
    for juego in _db_juegos:
        if juego.get("id") == id_juego:
            return juego
    return None

def obtener_juego_activo_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    """Busca un juego activo por ID."""
    juego = obtener_juego_por_id(id_juego)
    # Simplificado: solo verifica que exista y no esté eliminado
    if juego and not juego.get("esta_eliminado", False):
        return juego
    return None

def obtener_juegos(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene una lista de juegos."""
    if incluir_eliminados:
        resultados = _db_juegos
    else:
        # Simplificado: filtra solo por el estado del juego
        resultados = [juego for juego in _db_juegos if not juego.get("esta_eliminado", False)]
    return resultados[saltar : saltar + limite]

def crear_juego(datos_juego: JuegoCrear) -> Dict[str, Any]:
    """Crea un nuevo juego."""
    # Simplificado: Ya no se valida el desarrollador_id
    nuevo_id = obtener_siguiente_id()
    nuevo_juego_dict = Juego(
        id=nuevo_id,
        esta_eliminado=False,
        **datos_juego.dict()
    ).dict()

    _db_juegos.append(nuevo_juego_dict)
    guardar_juegos(_db_juegos)
    return nuevo_juego_dict

def actualizar_juego(id_juego: int, datos_actualizacion: JuegoCrear) -> Optional[Dict[str, Any]]:
    """Actualiza un juego existente."""
    indice_juego = -1
    for i, juego in enumerate(_db_juegos):
        if juego.get("id") == id_juego:
            indice_juego = i
            break

    if indice_juego == -1:
        return None

    juego_a_actualizar = _db_juegos[indice_juego]

    datos_nuevos = datos_actualizacion.dict(exclude_unset=True)
    for clave, valor in datos_nuevos.items():
         if clave in JuegoBase.__fields__:
              juego_a_actualizar[clave] = valor

    _db_juegos[indice_juego] = juego_a_actualizar
    guardar_juegos(_db_juegos)
    return juego_a_actualizar

def eliminar_logico_juego(id_juego: int) -> Optional[Dict[str, Any]]:
    """Marca un juego como eliminado (borrado lógico). (Sin cambios)"""
    juego = obtener_juego_por_id(id_juego)
    if juego is None or juego.get("esta_eliminado"):
        return None

    juego['esta_eliminado'] = True
    guardar_juegos(_db_juegos)
    return juego

def filtrar_juegos_por_genero(genero: str) -> List[Dict[str, Any]]:
    """Filtra juegos activos por género. (Sin cambios funcionales directos, pero usa la nueva lógica de obtener_juegos)"""
    consulta_genero = genero.strip().lower()
    if not consulta_genero:
        return []
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False)
    resultados = [
        juego for juego in juegos_activos
        if consulta_genero in juego.get("genero", "").lower()
    ]
    return resultados

# Añadimos una función de búsqueda por nombre de desarrollador (ahora un campo del juego)
def buscar_juegos_por_desarrollador(nombre_dev: str) -> List[Dict[str, Any]]:
    """Busca juegos activos por nombre de desarrollador (campo del juego)."""
    consulta_dev = nombre_dev.strip().lower()
    if not consulta_dev:
        return []
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False)
    resultados = [
        juego for juego in juegos_activos
        if consulta_dev in juego.get("nombre_desarrollador", "").lower()
    ]
    return resultados