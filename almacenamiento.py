import os
import uuid
from fastapi import UploadFile, HTTPException, status
from typing import Optional
from pathlib import Path
import magic

# Configuración
DIRECTORIO_IMAGENES = "imagenes"
TAMANO_MAXIMO_MB = 5  # Tamaño máximo de archivo permitido
TIPOS_PERMITIDOS = ["image/jpeg", "image/png", "image/webp"]

os.makedirs(DIRECTORIO_IMAGENES, exist_ok=True)

async def validar_imagen(archivo: UploadFile):
    """Valida el tipo y tamaño del archivo de imagen."""
    # Validar tamaño del archivo
    contenido = await archivo.read()
    await archivo.seek(0)  # Rebobinar para lectura posterior
    
    if len(contenido) > TAMANO_MAXIMO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo de {TAMANO_MAXIMO_MB}MB"
        )
    
    # Validar tipo de archivo usando magic
    tipo_real = magic.from_buffer(contenido, mime=True)
    if tipo_real not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Tipos permitidos: {', '.join(TIPOS_PERMITIDOS)}"
        )

async def guardar_imagen(archivo: UploadFile) -> dict:
    """Guarda un archivo de imagen y devuelve información sobre él."""
    await validar_imagen(archivo)
    
    # Generar nombre único para el archivo
    extension = Path(archivo.filename).suffix.lower()
    nombre_archivo = f"{uuid.uuid4()}{extension}"

    # Guardar el archivo
    ruta_archivo = os.path.join(DIRECTORIO_IMAGENES, nombre_archivo)
    
    try:
        with open(ruta_archivo, "wb") as buffer:
            contenido = await archivo.read()
            buffer.write(contenido)
    except Exception as e:
        # Si falla, intentar eliminar el archivo parcialmente escrito
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la imagen: {str(e)}"
        )

    return {
        "nombre_archivo": nombre_archivo,
        "url": f"/{DIRECTORIO_IMAGENES}/{nombre_archivo}"  # URL relativa para desarrollo
    }

def eliminar_imagen(nombre_archivo: str):
    """Elimina un archivo de imagen si existe."""
    if not nombre_archivo:
        return
        
    ruta_archivo = os.path.join(DIRECTORIO_IMAGENES, nombre_archivo)
    try:
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
    except Exception as e:
        print(f"Error al eliminar imagen {nombre_archivo}: {e}")