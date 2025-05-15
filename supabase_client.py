# supabase_client.py
import os
from supabase import create_client, Client
from fastapi import UploadFile, HTTPException, status
import uuid

# Estas variables deberían ser configuradas de forma segura, por ejemplo, usando variables de entorno
SUPABASE_URL = "https://jifxqeqwntzweakavfiz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImppZnhxZXF3bnR6d2Vha2F2Zml6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzI3NDExMiwiZXhwIjoyMDYyODUwMTEyfQ.nNP-Q5PWEaiw1vgLx-9-IFP6DLCWpA1N1uVjemJ66Qc"
SUPABASE_BUCKET_NAME = "hca-3-project-images" # Nombre del bucket acordado

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def upload_to_supabase(file: UploadFile) -> dict:
    """Sube un archivo a Supabase Storage y devuelve la URL pública."""
    try:
        file_content = await file.read()
        await file.seek(0) # Rebobinar para que el archivo pueda ser leído de nuevo si es necesario
        
        # Generar un nombre de archivo único para Supabase
        file_ext = os.path.splitext(file.filename)[1].lower()
        if not file_ext:
            file_ext = ".png" # Extensión por defecto si no se puede determinar
        
        file_name_in_bucket = f"images/{uuid.uuid4()}{file_ext}"

        # Subir el archivo
        # La documentación de supabase-py v2 indica que upload() devuelve un dict en éxito
        # o lanza StorageException en error.
        res = supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            path=file_name_in_bucket, 
            file=file_content,
            file_options={"content-type": file.content_type}
        )

        # Si la llamada anterior no lanzó una excepción y res es un dict (como se espera en éxito),
        # entonces la subida fue exitosa.
        # El contenido exacto de 'res' puede variar, pero la ausencia de excepción es clave.
        # Ejemplo de 'res' en éxito podría ser: {"path": file_name_in_bucket}
        # Por ahora, asumimos éxito si no hay excepción y construimos la URL.
        
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET_NAME}/{file_name_in_bucket}"
        return {"url": public_url, "path_in_bucket": file_name_in_bucket}

    except HTTPException as http_exc: # Re-lanzar excepciones HTTP existentes
        raise http_exc
    except Exception as e: # Capturar otras excepciones, incluyendo StorageException de Supabase
        # Aquí podrías verificar si 'e' es una StorageException y extraer más detalles
        # from supabase.lib.errors import StorageException
        # if isinstance(e, StorageException):
        #     detail = f"Error de Supabase Storage: {e.message} (Status: {e.status_code})"
        # else:
        #     detail = f"Error inesperado durante la subida a Supabase: {str(e)}"
        
        # Para simplificar, usamos un mensaje genérico pero informativo
        error_message = str(e)
        status_code_to_raise = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Intentar extraer un código de estado HTTP si la excepción lo tiene (como en StorageException)
        if hasattr(e, "status_code") and isinstance(e.status_code, int):
            status_code_to_raise = e.status_code
        elif hasattr(e, "status") and isinstance(e.status, int): # Algunas excepciones usan 'status'
            status_code_to_raise = e.status

        raise HTTPException(
            status_code=status_code_to_raise,
            detail=f"Error al subir imagen a Supabase: {error_message}"
        )

    except HTTPException as http_exc: # Re-lanzar excepciones HTTP existentes
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante la subida a Supabase: {str(e)}"
        )

async def delete_from_supabase(file_path_in_bucket: str):
    """Elimina un archivo de Supabase Storage."""
    if not file_path_in_bucket:
        return
    try:
        response = supabase.storage.from_(SUPABASE_BUCKET_NAME).remove([file_path_in_bucket])
        if response.status_code != 200:
            # Loggear el error pero no necesariamente lanzar una excepción crítica
            # ya que la entidad principal podría haberse eliminado correctamente
            error_detail = "Error desconocido."
            try:
                error_content = response.json()
                error_detail = error_content.get("message", error_detail)
            except Exception:
                pass
            print(f"Advertencia: No se pudo eliminar el archivo {file_path_in_bucket} de Supabase: {error_detail}")
    except Exception as e:
        print(f"Advertencia: Excepción al intentar eliminar el archivo {file_path_in_bucket} de Supabase: {str(e)}")


