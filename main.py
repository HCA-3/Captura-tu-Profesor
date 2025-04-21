from fastapi import FastAPI, HTTPException, Depends, status, Query
from typing import List, Optional

# Importar módulos con nombres en español
import crud
import modelos # Importa los modelos Pydantic en español
from modelos import Juego, JuegoCrear, Desarrollador, DesarrolladorCrear

# --- Creación de la Aplicación FastAPI ---
app = FastAPI(
    title="API CapturaTuProfesor - Videojuegos",
    description="Una API para gestionar información de videojuegos y desarrolladores.",
    version="1.0.0"
)

# --- Manejo de Excepciones Global ---
@app.exception_handler(Exception)
async def manejador_excepciones_generico(request, exc: Exception):
    # Aquí podrías añadir logging del error 'exc'
    print(f"Error no manejado detectado: {exc}") # Log simple a consola
    # Devuelve una respuesta HTTP 500 estándar
    # Nota: No uses HTTPException directamente aquí, retorna una Response o usa la utilidad de FastAPI
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )
    
# --- Endpoints para Desarrolladores ---

@app.post(
    "/desarrolladores/",
    response_model=Desarrollador, # Modelo de respuesta en español
    status_code=status.HTTP_201_CREATED,
    tags=["Desarrolladores"],
    summary="Crear un nuevo desarrollador" # Título corto para la UI de Docs
    )

def crear_nuevo_desarrollador(datos_desarrollador: DesarrolladorCrear): # Modelo de entrada en español
    """
    Crea un nuevo desarrollador en la base de datos (archivo CSV).

    - **datos_desarrollador**: JSON con los datos del desarrollador.
        - `nombre` (str): Requerido.
        - `pais` (str, opcional): País de origen.
        - `ano_fundacion` (int, opcional): Año de fundación.
    \f
    :param datos_desarrollador: Datos Pydantic validados.
    :return: El objeto Desarrollador creado.
    :raises HTTPException 409: Si ya existe un desarrollador activo con ese nombre.
    :raises HTTPException 500: Si ocurre un error interno al guardar.
    """
    try:
        # La función crud ya maneja la lógica y la excepción 409
        nuevo_dev = crud.crear_desarrollador(datos_desarrollador=datos_desarrollador)
        return nuevo_dev
    except HTTPException as http_exc:
        raise http_exc # Re-lanzar excepciones HTTP específicas (409, 400, etc.)
    except Exception as e:
        # Captura cualquier otro error inesperado durante la creación/guardado
        print(f"Error inesperado al crear desarrollador: {e}") # Loggear el error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar crear el desarrollador.")

def crear_nuevo_desarrollador(datos_desarrollador: DesarrolladorCrear): # Modelo de entrada en español
    """
    Crea un nuevo desarrollador en la base de datos (archivo CSV).

    - **datos_desarrollador**: JSON con los datos del desarrollador.
        - `nombre` (str): Requerido.
        - `pais` (str, opcional): País de origen.
        - `ano_fundacion` (int, opcional): Año de fundación.
    \f
    :param datos_desarrollador: Datos Pydantic validados.
    :return: El objeto Desarrollador creado.
    :raises HTTPException 409: Si ya existe un desarrollador activo con ese nombre.
    :raises HTTPException 500: Si ocurre un error interno al guardar.
    """
    try:
        # La función crud ya maneja la lógica y la excepción 409
        nuevo_dev = crud.crear_desarrollador(datos_desarrollador=datos_desarrollador)
        return nuevo_dev
    except HTTPException as http_exc:
        raise http_exc # Re-lanzar excepciones HTTP específicas (409, 400, etc.)
    except Exception as e:
        # Captura cualquier otro error inesperado durante la creación/guardado
        print(f"Error inesperado al crear desarrollador: {e}") # Loggear el error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar crear el desarrollador.")

@app.get(
    "/desarrolladores/",
    response_model=List[Desarrollador],
    tags=["Desarrolladores"],
    summary="Listar desarrolladores"
    )

def leer_desarrolladores(
    saltar: int = 0,
    limite: int = 10,
    incluir_eliminados: bool = Query(False, description="Incluir desarrolladores marcados como eliminados en la lista")
    ):
    """
    Obtiene una lista paginada de desarrolladores.

    Permite incluir opcionalmente los desarrolladores marcados como eliminados
    para propósitos de trazabilidad o administración.
    """
    try:
        desarrolladores = crud.obtener_desarrolladores(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return desarrolladores
    except Exception as e:
        print(f"Error inesperado al obtener desarrolladores: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener la lista de desarrolladores.")

@app.get(
    "/desarrolladores/{id_desarrollador}",
    response_model=Desarrollador,
    tags=["Desarrolladores"],
    summary="Obtener un desarrollador por ID"
    )

def leer_desarrollador_por_id(id_desarrollador: int):
    """
    Obtiene los detalles de un desarrollador específico usando su ID.

    Solo devuelve desarrolladores que **no** estén marcados como eliminados.
    """
    db_desarrollador = crud.obtener_desarrollador_activo_por_id(id_desarrollador=id_desarrollador)
    if db_desarrollador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El desarrollador con ID {id_desarrollador} no fue encontrado o está inactivo."
        )
    return db_desarrollador