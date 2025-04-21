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

def obtener_desarrolladores(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene una lista de desarrolladores (opcionalmente incluye borrados)."""
    if incluir_eliminados:
        resultados = _db_desarrolladores
    else:
        # Filtra para obtener solo los activos
        resultados = [dev for dev in _db_desarrolladores if not dev.get("esta_eliminado", False)]
    # Aplica paginación
    return resultados[saltar : saltar + limite]

def crear_desarrollador(datos_desarrollador: DesarrolladorCrear) -> Dict[str, Any]:
    """Crea un nuevo desarrollador."""
    nuevo_id = obtener_siguiente_id()

    # Verificar si ya existe un desarrollador activo con el mismo nombre (insensible a mayúsculas)
    nombre_nuevo = datos_desarrollador.nombre.strip().lower()
    existente = next((d for d in _db_desarrolladores if d.get("nombre", "").strip().lower() == nombre_nuevo and not d.get("esta_eliminado")), None)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un desarrollador activo con el nombre '{datos_desarrollador.nombre}'."
        )
        
         # Crea el diccionario de datos para el nuevo desarrollador
    nuevo_desarrollador_dict = Desarrollador(
        id=nuevo_id,
        esta_eliminado=False,
        **datos_desarrollador.dict() # Convierte el modelo Pydantic a dict
    ).dict() # Asegura que el resultado final sea un dict

    _db_desarrolladores.append(nuevo_desarrollador_dict)
    guardar_desarrolladores(_db_desarrolladores) # Persistir cambio
    return nuevo_desarrollador_dict # Retornar el dict creado

def actualizar_desarrollador(id_desarrollador: int, datos_actualizacion: DesarrolladorCrear) -> Optional[Dict[str, Any]]:
    """Actualiza un desarrollador existente."""
    indice_desarrollador = -1
    for i, dev in enumerate(_db_desarrolladores):
        if dev.get("id") == id_desarrollador:
            indice_desarrollador = i
            break
        
if indice_desarrollador == -1:
        return None # O podríamos lanzar 404 aquí directamente

    desarrollador_a_actualizar = _db_desarrolladores[indice_desarrollador]

    # Prevenir la actualización de un desarrollador eliminado (opcional, depende de la lógica de negocio)
    # if desarrollador_a_actualizar.get("esta_eliminado"):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede actualizar un desarrollador eliminado.")

    # Obtener datos a actualizar (solo los proporcionados)
    datos_nuevos = datos_actualizacion.dict(exclude_unset=True)

    # Opcional: Validar conflicto de nombre si se está cambiando
    if "nombre" in datos_nuevos:
        nombre_nuevo = datos_nuevos["nombre"].strip().lower()
        nombre_actual = desarrollador_a_actualizar.get("nombre", "").strip().lower()
        if nombre_nuevo != nombre_actual: # Solo validar si el nombre realmente cambia
             existente = next((d for i, d in enumerate(_db_desarrolladores) if i != indice_desarrollador and d.get("nombre", "").strip().lower() == nombre_nuevo and not d.get("esta_eliminado")), None)
             if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro desarrollador activo con el nombre '{datos_nuevos['nombre']}'."
                )

# Aplicar actualizaciones
    for clave, valor in datos_nuevos.items():
        # Solo actualiza campos que existen en el modelo base/original
        # y evita actualizar 'id' o 'esta_eliminado' directamente aquí
        if clave in DesarrolladorBase.__fields__:
             desarrollador_a_actualizar[clave] = valor

    # Actualizar en la lista "en memoria"
    _db_desarrolladores[indice_desarrollador] = desarrollador_a_actualizar
    guardar_desarrolladores(_db_desarrolladores) # Persistir cambio
    return desarrollador_a_actualizar

def eliminar_logico_desarrollador(id_desarrollador: int) -> Optional[Dict[str, Any]]:
    """Marca un desarrollador como eliminado (borrado lógico)."""
    desarrollador = obtener_desarrollador_por_id(id_desarrollador)

    # Si no existe o ya está borrado, no hacer nada (o devolver error si se prefiere)
    if desarrollador is None or desarrollador.get("esta_eliminado"):
        return None # El endpoint manejará el 404

    # Marcar como eliminado
    desarrollador['esta_eliminado'] = True

    # Consideración: ¿Qué pasa con los juegos de este desarrollador?
    # Podrían marcarse como "huérfanos", eliminarse también, o dejarse tal cual.
    # Por simplicidad, aquí solo marcamos el desarrollador. Los endpoints GET de juegos
    # ya filtran por desarrollador activo por defecto.
    
     guardar_desarrolladores(_db_desarrolladores) # Persistir el cambio
    return desarrollador # Devolvemos el desarrollador marcado como borrado

def buscar_desarrolladores_por_nombre(consulta_nombre: str) -> List[Dict[str, Any]]:
    """Busca desarrolladores activos por nombre (búsqueda parcial, insensible a mayúsculas)."""
    consulta = consulta_nombre.strip().lower()
    if not consulta: # Evitar búsqueda vacía
        return []
    resultados = [
        dev for dev in _db_desarrolladores
        if not dev.get("esta_eliminado", False) and consulta in dev.get("nombre", "").lower()
    ]
    return resultados

# --- Operaciones CRUD para Juegos ---

def obtener_juego_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    """Busca un juego por ID (incluyendo borrados lógicamente)."""
    for juego in _db_juegos:
        if juego.get("id") == id_juego:
            return juego
    return None

def obtener_juego_activo_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    """Busca un juego activo por ID, asegurando que su desarrollador también esté activo."""
    juego = obtener_juego_por_id(id_juego)
    if juego and not juego.get("esta_eliminado"):
        # Validar que el desarrollador asociado exista y esté activo
        desarrollador = obtener_desarrollador_activo_por_id(juego.get("desarrollador_id"))
        if desarrollador:
            return juego
        else:
             # El juego existe y no está eliminado, pero su desarrollador sí lo está (o no existe)
             # Decidimos no retornarlo como "activo" en este caso.
             return None
    return None # No encontrado o está eliminado

def obtener_juegos(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene una lista de juegos. Por defecto, solo activos con desarrollador activo."""

    juegos_filtrados = []
    # Optimización: obtener lista de IDs de desarrolladores activos una sola vez
    ids_desarrolladores_activos = {dev['id'] for dev in obtener_desarrolladores(incluir_eliminados=False, limite=len(_db_desarrolladores))} # Obtener todos los activos

    for juego in _db_juegos:
        esta_eliminado_juego = juego.get("esta_eliminado", False)
        id_desarrollador_juego = juego.get("desarrollador_id")

        # Condición para incluir el juego:
        # 1. Si se piden incluir eliminados: incluir todos.
        # 2. Si NO se piden incluir eliminados: incluir solo si el juego NO está eliminado Y su desarrollador está en la lista de activos.
        if incluir_eliminados:
            juegos_filtrados.append(juego)
        elif not esta_eliminado_juego and id_desarrollador_juego in ids_desarrolladores_activos:
            juegos_filtrados.append(juego)

    # Aplicar paginación a los resultados filtrados
    return juegos_filtrados[saltar : saltar + limite]