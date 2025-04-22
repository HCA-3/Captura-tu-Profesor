from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
import modelos
from modelos import Juego, JuegoCrear, JuegoBase, Consola, ConsolaCrear, ConsolaBase 
from persistencia import ( 
    cargar_juegos, guardar_juegos,
    cargar_consolas, guardar_consolas
)
from utilidades import obtener_siguiente_id

try:
    _db_juegos: List[Dict[str, Any]] = cargar_juegos()
except HTTPException as e:
    print(f"Error crítico al cargar datos iniciales de juegos: {e.detail}. Iniciando con datos vacíos.")
    _db_juegos = []

try: 
    _db_consolas: List[Dict[str, Any]] = cargar_consolas()
except HTTPException as e:
    print(f"Error crítico al cargar datos iniciales de consolas: {e.detail}. Iniciando con datos vacíos.")
    _db_consolas = []

def obtener_juego_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    for juego in _db_juegos:
        if juego.get("id") == id_juego: return juego
    return None

def obtener_juego_activo_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    juego = obtener_juego_por_id(id_juego)
    if juego and not juego.get("esta_eliminado", False): return juego
    return None

def obtener_juegos(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    resultados = [j for j in _db_juegos if incluir_eliminados or not j.get("esta_eliminado", False)]
    return resultados[saltar : saltar + limite]

def crear_juego(datos_juego: JuegoCrear) -> Dict[str, Any]:
    nuevo_id = obtener_siguiente_id()
    nuevo_juego_dict = Juego(id=nuevo_id, esta_eliminado=False, **datos_juego.dict()).dict()
    _db_juegos.append(nuevo_juego_dict)
    guardar_juegos(_db_juegos)
    return nuevo_juego_dict

def actualizar_juego(id_juego: int, datos_actualizacion: JuegoCrear) -> Optional[Dict[str, Any]]:
    indice_juego = -1
    for i, juego in enumerate(_db_juegos):
        if juego.get("id") == id_juego: indice_juego = i; break
    if indice_juego == -1: return None
    juego_a_actualizar = _db_juegos[indice_juego]
    datos_nuevos = datos_actualizacion.dict(exclude_unset=True)
    for clave, valor in datos_nuevos.items():
         if clave in JuegoBase.__fields__: juego_a_actualizar[clave] = valor
    _db_juegos[indice_juego] = juego_a_actualizar
    guardar_juegos(_db_juegos)
    return juego_a_actualizar

def eliminar_logico_juego(id_juego: int) -> Optional[Dict[str, Any]]:
    juego = obtener_juego_por_id(id_juego)
    if juego is None or juego.get("esta_eliminado"): return None
    juego['esta_eliminado'] = True
    guardar_juegos(_db_juegos)
    return juego

def filtrar_juegos_por_genero(genero: str) -> List[Dict[str, Any]]:
    consulta_genero = genero.strip().lower()
    if not consulta_genero: return []
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False)
    return [j for j in juegos_activos if consulta_genero in j.get("genero", "").lower()]

def buscar_juegos_por_desarrollador(nombre_dev: str) -> List[Dict[str, Any]]:
    consulta_dev = nombre_dev.strip().lower()
    if not consulta_dev: return []
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False)
    return [j for j in juegos_activos if consulta_dev in j.get("nombre_desarrollador", "").lower()]


# --- Operaciones CRUD para Consolas (Nuevo) ---

def obtener_consola_por_id(id_consola: int) -> Optional[Dict[str, Any]]:
    """Busca una consola por ID (incluyendo borradas lógicamente)."""
    for consola in _db_consolas:
        if consola.get("id") == id_consola:
            return consola
    return None

def obtener_consola_activa_por_id(id_consola: int) -> Optional[Dict[str, Any]]:
    """Busca una consola activa por ID."""
    consola = obtener_consola_por_id(id_consola)
    if consola and not consola.get("esta_eliminado", False):
        return consola
    return None

def obtener_consolas(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene una lista de consolas."""
    if incluir_eliminados:
        resultados = _db_consolas
    else:
        resultados = [c for c in _db_consolas if not c.get("esta_eliminado", False)]
    return resultados[saltar : saltar + limite]

def crear_consola(datos_consola: ConsolaCrear) -> Dict[str, Any]:
    """Crea una nueva consola."""
    nuevo_id = obtener_siguiente_id()
    # Validación opcional: Evitar nombres duplicados activos
    nombre_nuevo = datos_consola.nombre.strip().lower()
    existente = next((c for c in _db_consolas if c.get("nombre", "").strip().lower() == nombre_nuevo and not c.get("esta_eliminado")), None)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una consola activa con el nombre '{datos_consola.nombre}'."
        )

    nueva_consola_dict = Consola(
        id=nuevo_id,
        esta_eliminado=False,
        **datos_consola.dict()
    ).dict()

    _db_consolas.append(nueva_consola_dict)
    guardar_consolas(_db_consolas) # Guardar en consolas.csv
    return nueva_consola_dict

def actualizar_consola(id_consola: int, datos_actualizacion: ConsolaCrear) -> Optional[Dict[str, Any]]:
    """Actualiza una consola existente."""
    indice_consola = -1
    for i, consola in enumerate(_db_consolas):
        if consola.get("id") == id_consola:
            indice_consola = i
            break

    if indice_consola == -1:
        return None

    consola_a_actualizar = _db_consolas[indice_consola]
    datos_nuevos = datos_actualizacion.dict(exclude_unset=True)

    if "nombre" in datos_nuevos:
        nombre_nuevo = datos_nuevos["nombre"].strip().lower()
        nombre_actual = consola_a_actualizar.get("nombre", "").strip().lower()
        if nombre_nuevo != nombre_actual:
             existente = next((c for i, c in enumerate(_db_consolas) if i != indice_consola and c.get("nombre", "").strip().lower() == nombre_nuevo and not c.get("esta_eliminado")), None)
             if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otra consola activa con el nombre '{datos_nuevos['nombre']}'."
                )

    for clave, valor in datos_nuevos.items():
         if clave in ConsolaBase.__fields__: 
              consola_a_actualizar[clave] = valor

    _db_consolas[indice_consola] = consola_a_actualizar
    guardar_consolas(_db_consolas)
    return consola_a_actualizar

def eliminar_logico_consola(id_consola: int) -> Optional[Dict[str, Any]]:
    """Marca una consola como eliminada (borrado lógico)."""
    consola = obtener_consola_por_id(id_consola)
    if consola is None or consola.get("esta_eliminado"):
        return None

    consola['esta_eliminado'] = True
    guardar_consolas(_db_consolas)
    return consola

def buscar_consolas_por_fabricante(fabricante: str) -> List[Dict[str, Any]]:
    """Busca consolas activas por fabricante (búsqueda parcial, insensible a mayúsculas)."""
    consulta = fabricante.strip().lower()
    if not consulta:
        return []
    consolas_activas = obtener_consolas(limite=len(_db_consolas), incluir_eliminados=False)
    resultados = [
        c for c in consolas_activas
        if consulta in c.get("fabricante", "").lower()
    ]
    return resultados