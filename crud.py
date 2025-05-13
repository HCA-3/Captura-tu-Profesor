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
import uuid
from pathlib import Path

# Directorio para imágenes
IMAGENES_DIR = "imagenes"
os.makedirs(IMAGENES_DIR, exist_ok=True)

# Bases de datos en memoria
try:
    _db_juegos = cargar_juegos()
    _db_consolas = cargar_consolas()
    _db_accesorios = cargar_accesorios()
except HTTPException:
    _db_juegos = []
    _db_consolas = []
    _db_accesorios = []

# Funciones para manejo de imágenes
async def guardar_imagen(imagen: UploadFile) -> Optional[Dict[str, str]]:
    if not imagen:
        return None
    
    try:
        # Validar tipo de imagen
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if imagen.content_type not in allowed_types:
            raise ValueError("Solo se permiten imágenes JPEG, PNG o WEBP")

        # Generar nombre único
        file_ext = Path(imagen.filename).suffix.lower()
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(IMAGENES_DIR, file_name)

        # Guardar archivo
        contents = await imagen.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        return {
            "nombre_archivo": file_name,
            "url": f"/imagenes/{file_name}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar imagen: {str(e)}"
        )

async def eliminar_imagen(nombre_archivo: str):
    if nombre_archivo:
        try:
            file_path = os.path.join(IMAGENES_DIR, nombre_archivo)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

# Operaciones CRUD para Juegos
async def crear_juego(datos_juego: JuegoCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    # Validar título único
    titulo_lower = datos_juego.titulo.lower()
    if any(j['titulo'].lower() == titulo_lower and not j.get('esta_eliminado') for j in _db_juegos):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un juego con este título"
        )

    try:
        imagen_data = await guardar_imagen(imagen)
        nuevo_juego = {
            "id": obtener_siguiente_id(),
            **datos_juego.model_dump(),
            "imagen": imagen_data,
            "esta_eliminado": False
        }
        
        _db_juegos.append(nuevo_juego)
        guardar_juegos(_db_juegos)
        return nuevo_juego
    except Exception as e:
        if imagen_data and 'nombre_archivo' in imagen_data:
            await eliminar_imagen(imagen_data['nombre_archivo'])
        raise e

async def actualizar_juego(id_juego: int, datos_actualizacion: JuegoCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    juego = next((j for j in _db_juegos if j['id'] == id_juego), None)
    if not juego:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    
    try:
        # Validar título único si se cambia
        if 'titulo' in datos_actualizacion.model_dump(exclude_unset=True):
            titulo_lower = datos_actualizacion.titulo.lower()
            if any(j['id'] != id_juego and j['titulo'].lower() == titulo_lower and not j.get('esta_eliminado') 
                   for j in _db_juegos):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otro juego con este título"
                )

        # Procesar imagen
        imagen_data = await guardar_imagen(imagen) if imagen else None
        if imagen_data and juego.get('imagen'):
            await eliminar_imagen(juego['imagen']['nombre_archivo'])

        # Actualizar campos
        for field, value in datos_actualizacion.model_dump(exclude_unset=True).items():
            juego[field] = value
        
        if imagen_data:
            juego['imagen'] = imagen_data
        
        guardar_juegos(_db_juegos)
        return juego
    except Exception as e:
        if imagen_data and 'nombre_archivo' in imagen_data:
            await eliminar_imagen(imagen_data['nombre_archivo'])
        raise e

# Implementar funciones similares para Consolas y Accesorios
# (crear_consola, actualizar_consola, crear_accesorio, actualizar_accesorio)

def obtener_juego_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    return next((j for j in _db_juegos if j['id'] == id_juego), None)

def obtener_juego_activo_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    juego = obtener_juego_por_id(id_juego)
    return juego if juego and not juego.get('esta_eliminado') else None

# Implementar funciones similares para consolas y accesorios
# (obtener_consola_por_id, obtener_consola_activa_por_id, etc.)

def eliminar_logico_juego(id_juego: int) -> Dict[str, Any]:
    juego = obtener_juego_por_id(id_juego)
    if not juego:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    
    juego['esta_eliminado'] = True
    guardar_juegos(_db_juegos)
    return juego

# Implementar funciones similares para consolas y accesorios
# (eliminar_logico_consola, eliminar_logico_accesorio)

def obtener_compatibilidad_juego(id_juego: int) -> Dict[str, Any]:
    juego = obtener_juego_activo_por_id(id_juego)
    if not juego:
        raise HTTPException(status_code=404, detail="Juego no encontrado o inactivo")

    plataformas = [p.lower() for p in juego.get('plataformas', [])]
    consolas_compatibles = []

    for consola in _db_consolas:
        if not consola.get('esta_eliminado') and consola['nombre'].lower() in plataformas:
            accesorios = [a for a in _db_accesorios 
                         if a['id_consola'] == consola['id'] and not a.get('esta_eliminado')]
            consolas_compatibles.append({**consola, 'accesorios': accesorios})

    return {
        "juego": juego,
        "consolas_compatibles": consolas_compatibles
    }