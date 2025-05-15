from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status, UploadFile
import modelos
from modelos import (
    Juego, JuegoCrear, JuegoBase,
    Consola, ConsolaCrear, ConsolaBase,
    Accesorio, AccesorioCrear, AccesorioBase,
    ConsolaConAccesorios, JuegoCompatibilidad, ImagenBase
)
from persistencia import (
    cargar_juegos, guardar_juegos,
    cargar_consolas, guardar_consolas,
    cargar_accesorios, guardar_accesorios
)
from utilidades import obtener_siguiente_id
import os
# import uuid # No se usa directamente aquí si se elimina guardar_imagen local
# from pathlib import Path # No se usa directamente aquí si se elimina guardar_imagen local
import almacenamiento # Importar el módulo almacenamiento

# Directorio para imágenes (ya definido en almacenamiento.py, pero main.py lo usa también)
# IMAGENES_DIR = "imagenes" # Esta línea puede ser redundante si almacenamiento.py lo maneja todo
# os.makedirs(IMAGENES_DIR, exist_ok=True) # almacenamiento.py ya crea el directorio

# Bases de datos en memoria
try:
    _db_juegos = cargar_juegos()
    _db_consolas = cargar_consolas()
    _db_accesorios = cargar_accesorios()
except HTTPException:
    _db_juegos = []
    _db_consolas = []
    _db_accesorios = []

# Las funciones guardar_imagen y eliminar_imagen se eliminan de aquí
# y se usarán las de almacenamiento.py

# Operaciones CRUD para Juegos
async def crear_juego(datos_juego: JuegoCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    titulo_lower = datos_juego.titulo.lower()
    if any(j["titulo"].lower() == titulo_lower and not j.get("esta_eliminado") for j in _db_juegos):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un juego con este título"
        )

    imagen_data: Optional[Dict[str, str]] = None
    try:
        if imagen:
            imagen_data = await almacenamiento.guardar_imagen(imagen) # Usar almacenamiento.guardar_imagen
        
        nuevo_juego = {
            "id": obtener_siguiente_id(_db_juegos),
            **datos_juego.model_dump(),
            "imagen": imagen_data,
            "esta_eliminado": False
        }
        
        _db_juegos.append(nuevo_juego)
        guardar_juegos(_db_juegos)
        return nuevo_juego
    except Exception as e:
        if imagen_data and "nombre_archivo" in imagen_data:
            almacenamiento.eliminar_imagen(imagen_data["nombre_archivo"]) # Usar almacenamiento.eliminar_imagen
        # Re-raise la excepción original para que FastAPI la maneje o el manejador de excepciones en main.py
        if isinstance(e, HTTPException):
            raise e
        else:
            # Podrías loggear el error original aquí si es necesario
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al crear juego: {str(e)}")

async def actualizar_juego(id_juego: int, datos_actualizacion: JuegoCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    juego_existente = next((j for j in _db_juegos if j["id"] == id_juego and not j.get("esta_eliminado")), None)
    if not juego_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Juego no encontrado o inactivo")

    # Validar título único si se cambia y es diferente al actual
    if datos_actualizacion.titulo:
        nuevo_titulo_lower = datos_actualizacion.titulo.lower()
        if nuevo_titulo_lower != juego_existente["titulo"].lower():
            if any(j["id"] != id_juego and j["titulo"].lower() == nuevo_titulo_lower and not j.get("esta_eliminado") for j in _db_juegos):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otro juego con este título"
                )

    imagen_data_nueva: Optional[Dict[str, str]] = None
    try:
        if imagen:
            imagen_data_nueva = await almacenamiento.guardar_imagen(imagen) # Usar almacenamiento.guardar_imagen
            # Si hay nueva imagen y existía una antigua, eliminar la antigua
            if imagen_data_nueva and juego_existente.get("imagen") and juego_existente["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(juego_existente["imagen"]["nombre_archivo"]) # Usar almacenamiento.eliminar_imagen
        
        # Actualizar campos del juego
        update_data = datos_actualizacion.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None: # Asegurarse de no actualizar con None si no es la intención
                 juego_existente[field] = value
        
        if imagen_data_nueva:
            juego_existente["imagen"] = imagen_data_nueva
        elif imagen is None and "imagen" in datos_actualizacion.model_fields_set: # Si se pasa imagen=None explícitamente para borrarla
            if juego_existente.get("imagen") and juego_existente["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(juego_existente["imagen"]["nombre_archivo"])
            juego_existente["imagen"] = None
            
        guardar_juegos(_db_juegos)
        return juego_existente
    except Exception as e:
        # Si se guardó una nueva imagen pero falla otra cosa, eliminar la nueva imagen
        if imagen_data_nueva and "nombre_archivo" in imagen_data_nueva:
            almacenamiento.eliminar_imagen(imagen_data_nueva["nombre_archivo"]) # Usar almacenamiento.eliminar_imagen
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al actualizar juego: {str(e)}")

def obtener_juegos(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    juegos_filtrados = _db_juegos if incluir_eliminados else [j for j in _db_juegos if not j.get("esta_eliminado")]
    return juegos_filtrados[saltar : saltar + limite]

def obtener_juego_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    return next((j for j in _db_juegos if j["id"] == id_juego), None)

def obtener_juego_activo_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    juego = obtener_juego_por_id(id_juego)
    return juego if juego and not juego.get("esta_eliminado") else None

def eliminar_logico_juego(id_juego: int) -> Dict[str, Any]:
    juego = obtener_juego_por_id(id_juego)
    if not juego or juego.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Juego no encontrado o ya eliminado")
    
    # Eliminar imagen asociada si existe
    if juego.get("imagen") and juego["imagen"].get("nombre_archivo"):
        almacenamiento.eliminar_imagen(juego["imagen"]["nombre_archivo"]) # Usar almacenamiento.eliminar_imagen
        juego["imagen"] = None # Opcional: limpiar referencia de imagen

    juego["esta_eliminado"] = True
    guardar_juegos(_db_juegos)
    return juego

def filtrar_juegos_por_genero(genero: str) -> List[Dict[str, Any]]:
    genero_lower = genero.lower()
    return [j for j in _db_juegos if not j.get("esta_eliminado") and genero_lower in j["genero"].lower()]

def buscar_juegos_por_desarrollador(nombre_dev: str) -> List[Dict[str, Any]]:
    nombre_dev_lower = nombre_dev.lower()
    return [j for j in _db_juegos if not j.get("esta_eliminado") and j.get("nombre_desarrollador") and nombre_dev_lower in j["nombre_desarrollador"].lower()]

# --- Operaciones CRUD para Consolas ---
async def crear_consola(datos_consola: ConsolaCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    nombre_lower = datos_consola.nombre.lower()
    if any(c["nombre"].lower() == nombre_lower and not c.get("esta_eliminado") for c in _db_consolas):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una consola con este nombre"
        )
    imagen_data: Optional[Dict[str, str]] = None
    try:
        if imagen:
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        nueva_consola = {
            "id": obtener_siguiente_id(_db_consolas),
            **datos_consola.model_dump(),
            "imagen": imagen_data,
            "esta_eliminado": False
        }
        _db_consolas.append(nueva_consola)
        guardar_consolas(_db_consolas)
        return nueva_consola
    except Exception as e:
        if imagen_data and "nombre_archivo" in imagen_data:
            almacenamiento.eliminar_imagen(imagen_data["nombre_archivo"])
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al crear consola: {str(e)}")

async def actualizar_consola(id_consola: int, datos_actualizacion: ConsolaCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    consola_existente = next((c for c in _db_consolas if c["id"] == id_consola and not c.get("esta_eliminado")), None)
    if not consola_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consola no encontrada o inactiva")

    if datos_actualizacion.nombre:
        nuevo_nombre_lower = datos_actualizacion.nombre.lower()
        if nuevo_nombre_lower != consola_existente["nombre"].lower():
            if any(c["id"] != id_consola and c["nombre"].lower() == nuevo_nombre_lower and not c.get("esta_eliminado") for c in _db_consolas):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otra consola con este nombre"
                )
    imagen_data_nueva: Optional[Dict[str, str]] = None
    try:
        if imagen:
            imagen_data_nueva = await almacenamiento.guardar_imagen(imagen)
            if imagen_data_nueva and consola_existente.get("imagen") and consola_existente["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(consola_existente["imagen"]["nombre_archivo"])
        
        update_data = datos_actualizacion.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                consola_existente[field] = value
        
        if imagen_data_nueva:
            consola_existente["imagen"] = imagen_data_nueva
        elif imagen is None and "imagen" in datos_actualizacion.model_fields_set:
            if consola_existente.get("imagen") and consola_existente["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(consola_existente["imagen"]["nombre_archivo"])
            consola_existente["imagen"] = None
            
        guardar_consolas(_db_consolas)
        return consola_existente
    except Exception as e:
        if imagen_data_nueva and "nombre_archivo" in imagen_data_nueva:
            almacenamiento.eliminar_imagen(imagen_data_nueva["nombre_archivo"])
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al actualizar consola: {str(e)}")

def obtener_consolas(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    consolas_filtradas = _db_consolas if incluir_eliminados else [c for c in _db_consolas if not c.get("esta_eliminado")]
    return consolas_filtradas[saltar : saltar + limite]

def obtener_consola_por_id(id_consola: int) -> Optional[Dict[str, Any]]:
    return next((c for c in _db_consolas if c["id"] == id_consola), None)

def obtener_consola_activa_por_id(id_consola: int) -> Optional[Dict[str, Any]]:
    consola = obtener_consola_por_id(id_consola)
    return consola if consola and not consola.get("esta_eliminado") else None

def eliminar_logico_consola(id_consola: int) -> Dict[str, Any]:
    consola = obtener_consola_por_id(id_consola)
    if not consola or consola.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consola no encontrada o ya eliminada")

    if consola.get("imagen") and consola["imagen"].get("nombre_archivo"):
        almacenamiento.eliminar_imagen(consola["imagen"]["nombre_archivo"])
        consola["imagen"] = None

    consola["esta_eliminado"] = True
    # También eliminar lógicamente los accesorios asociados
    for acc in _db_accesorios:
        if acc["id_consola"] == id_consola and not acc.get("esta_eliminado"):
            if acc.get("imagen") and acc["imagen"].get("nombre_archivo"):
                 almacenamiento.eliminar_imagen(acc["imagen"]["nombre_archivo"])
                 acc["imagen"] = None
            acc["esta_eliminado"] = True
            
    guardar_consolas(_db_consolas)
    guardar_accesorios(_db_accesorios) # Guardar cambios en accesorios también
    return consola

def buscar_consolas_por_fabricante(fabricante: str) -> List[Dict[str, Any]]:
    fabricante_lower = fabricante.lower()
    return [c for c in _db_consolas if not c.get("esta_eliminado") and c.get("fabricante") and fabricante_lower in c["fabricante"].lower()]

# --- Operaciones CRUD para Accesorios ---
async def crear_accesorio(datos_accesorio: AccesorioCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    # Validar que la consola asociada exista y esté activa
    consola_madre = obtener_consola_activa_por_id(datos_accesorio.id_consola)
    if not consola_madre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La consola con ID {datos_accesorio.id_consola} no existe o no está activa."
        )
    
    # Validar nombre único para el accesorio DENTRO de la misma consola
    nombre_lower = datos_accesorio.nombre.lower()
    if any(a["nombre"].lower() == nombre_lower and a["id_consola"] == datos_accesorio.id_consola and not a.get("esta_eliminado") for a in _db_accesorios):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un accesorio con este nombre para la consola ID {datos_accesorio.id_consola}"
        )

    imagen_data: Optional[Dict[str, str]] = None
    try:
        if imagen:
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        nuevo_accesorio = {
            "id": obtener_siguiente_id(_db_accesorios),
            **datos_accesorio.model_dump(),
            "imagen": imagen_data,
            "esta_eliminado": False
        }
        _db_accesorios.append(nuevo_accesorio)
        guardar_accesorios(_db_accesorios)
        return nuevo_accesorio
    except Exception as e:
        if imagen_data and "nombre_archivo" in imagen_data:
            almacenamiento.eliminar_imagen(imagen_data["nombre_archivo"])
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al crear accesorio: {str(e)}")

async def actualizar_accesorio(id_accesorio: int, datos_actualizacion: AccesorioCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    accesorio_existente = next((a for a in _db_accesorios if a["id"] == id_accesorio and not a.get("esta_eliminado")), None)
    if not accesorio_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accesorio no encontrado o inactivo")

    # Validar que la consola asociada (si se cambia) exista y esté activa
    if datos_actualizacion.id_consola and datos_actualizacion.id_consola != accesorio_existente["id_consola"]:
        consola_madre_nueva = obtener_consola_activa_por_id(datos_actualizacion.id_consola)
        if not consola_madre_nueva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La nueva consola con ID {datos_actualizacion.id_consola} no existe o no está activa."
            )
    
    # Validar nombre único si se cambia, dentro de la misma (nueva o actual) consola
    id_consola_actual = datos_actualizacion.id_consola if datos_actualizacion.id_consola else accesorio_existente["id_consola"]
    if datos_actualizacion.nombre:
        nuevo_nombre_lower = datos_actualizacion.nombre.lower()
        # Comprobar si el nombre ha cambiado o si la consola ha cambiado
        nombre_cambiado = nuevo_nombre_lower != accesorio_existente["nombre"].lower()
        consola_cambiada = datos_actualizacion.id_consola and datos_actualizacion.id_consola != accesorio_existente["id_consola"]
        
        if nombre_cambiado or consola_cambiada:
            if any(a["id"] != id_accesorio and \
                   a["nombre"].lower() == nuevo_nombre_lower and \
                   a["id_consola"] == id_consola_actual and \
                   not a.get("esta_eliminado") for a in _db_accesorios):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro accesorio con este nombre para la consola ID {id_consola_actual}"
                )

    imagen_data_nueva: Optional[Dict[str, str]] = None
    try:
        if imagen:
            imagen_data_nueva = await almacenamiento.guardar_imagen(imagen)
            if imagen_data_nueva and accesorio_existente.get("imagen") and accesorio_existente["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(accesorio_existente["imagen"]["nombre_archivo"])
        
        update_data = datos_actualizacion.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                accesorio_existente[field] = value
        
        if imagen_data_nueva:
            accesorio_existente["imagen"] = imagen_data_nueva
        elif imagen is None and "imagen" in datos_actualizacion.model_fields_set:
            if accesorio_existente.get("imagen") and accesorio_existente["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(accesorio_existente["imagen"]["nombre_archivo"])
            accesorio_existente["imagen"] = None
            
        guardar_accesorios(_db_accesorios)
        return accesorio_existente
    except Exception as e:
        if imagen_data_nueva and "nombre_archivo" in imagen_data_nueva:
            almacenamiento.eliminar_imagen(imagen_data_nueva["nombre_archivo"])
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al actualizar accesorio: {str(e)}")

def obtener_accesorios(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    accesorios_filtrados = _db_accesorios if incluir_eliminados else [a for a in _db_accesorios if not a.get("esta_eliminado")]
    return accesorios_filtrados[saltar : saltar + limite]

def obtener_accesorio_por_id(id_accesorio: int) -> Optional[Dict[str, Any]]:
    return next((a for a in _db_accesorios if a["id"] == id_accesorio), None)

def obtener_accesorio_activo_por_id(id_accesorio: int) -> Optional[Dict[str, Any]]:
    accesorio = obtener_accesorio_por_id(id_accesorio)
    return accesorio if accesorio and not accesorio.get("esta_eliminado") else None

def eliminar_logico_accesorio(id_accesorio: int) -> Dict[str, Any]:
    accesorio = obtener_accesorio_por_id(id_accesorio)
    if not accesorio or accesorio.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accesorio no encontrado o ya eliminado")

    if accesorio.get("imagen") and accesorio["imagen"].get("nombre_archivo"):
        almacenamiento.eliminar_imagen(accesorio["imagen"]["nombre_archivo"])
        accesorio["imagen"] = None

    accesorio["esta_eliminado"] = True
    guardar_accesorios(_db_accesorios)
    return accesorio

def obtener_accesorios_por_consola(id_consola: int, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    # Primero verificar si la consola existe (activa o no, dependiendo de la lógica deseada)
    # Aquí asumimos que la consola debe existir, pero no necesariamente estar activa para listar sus accesorios (depende del requisito)
    consola = obtener_consola_por_id(id_consola)
    if not consola:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada.")

    accesorios_consola = [a for a in _db_accesorios if a["id_consola"] == id_consola]
    if not incluir_eliminados:
        accesorios_consola = [a for a in accesorios_consola if not a.get("esta_eliminado")]
    return accesorios_consola

# --- Funciones de Compatibilidad ---
def obtener_compatibilidad_juego(id_juego: int) -> Dict[str, Any]:
    juego = obtener_juego_activo_por_id(id_juego)
    if not juego:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Juego no encontrado o inactivo")

    plataformas_juego = [p.lower() for p in juego.get("plataformas", [])]
    consolas_compatibles_info = []

    for consola_db in _db_consolas:
        if not consola_db.get("esta_eliminado") and consola_db["nombre"].lower() in plataformas_juego:
            # Obtener accesorios activos para esta consola compatible
            accesorios_consola = obtener_accesorios_por_consola(id_consola=consola_db["id"], incluir_eliminados=False)
            
            # Crear una copia de la consola para añadirle los accesorios sin modificar _db_consolas
            consola_info = {**consola_db, "accesorios": accesorios_consola}
            consolas_compatibles_info.append(consola_info)

    return {
        "juego": juego,
        "consolas_compatibles": consolas_compatibles_info
    }

# Función para obtener el siguiente ID (modificada para tomar la lista como argumento)
def obtener_siguiente_id(db_list: List[Dict[str, Any]]) -> int:
    if not db_list:
        return 1
    return max(item["id"] for item in db_list) + 1

