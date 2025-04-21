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

@app.put(
    "/desarrolladores/{id_desarrollador}",
    response_model=Desarrollador,
    tags=["Desarrolladores"],
    summary="Actualizar un desarrollador"
    )

def actualizar_desarrollador_existente(id_desarrollador: int, datos_desarrollador: DesarrolladorCrear):
    """
    Actualiza la información de un desarrollador existente.

    Permite modificar nombre, país y año de fundación.
    Verifica conflictos si se cambia el nombre.
    """
    try:
        desarrollador_actualizado = crud.actualizar_desarrollador(
            id_desarrollador=id_desarrollador,
            datos_actualizacion=datos_desarrollador
        )
        if desarrollador_actualizado is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el desarrollador con ID {id_desarrollador} para actualizar."
            )
        return desarrollador_actualizado
    except HTTPException as http_exc:
        raise http_exc # Re-lanzar 409 (conflicto nombre) u otros errores HTTP
    except Exception as e:
        print(f"Error inesperado al actualizar desarrollador {id_desarrollador}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar actualizar el desarrollador.")

@app.delete(
    "/desarrolladores/{id_desarrollador}",
    response_model=Desarrollador, # Devuelve el objeto marcado como eliminado
    tags=["Desarrolladores"],
    summary="Eliminar (lógicamente) un desarrollador"
    )

def eliminar_desarrollador_existente(id_desarrollador: int):
    """
    Marca un desarrollador como eliminado (borrado lógico).

    El registro permanece en el sistema (`esta_eliminado = True`) para mantener
    la trazabilidad, pero no aparecerá en las búsquedas normales.
    Devuelve el objeto del desarrollador con el estado actualizado.
    """
    desarrollador_eliminado = crud.eliminar_logico_desarrollador(id_desarrollador=id_desarrollador)
    if desarrollador_eliminado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el desarrollador con ID {id_desarrollador} o ya estaba eliminado."
        )
    # Devuelve el objeto marcado como eliminado (contiene esta_eliminado=True)
    return desarrollador_eliminado

@app.get(
    "/desarrolladores/buscar/por_nombre/",
    response_model=List[Desarrollador],
    tags=["Desarrolladores"],
    summary="Buscar desarrolladores por nombre"
    )

def buscar_desarrolladores(
    consulta_nombre: str = Query(..., min_length=1, description="Texto a buscar en el nombre del desarrollador (búsqueda parcial, insensible a mayúsculas)")
    ):
    """
    Busca desarrolladores activos cuyo nombre contenga el texto proporcionado.

    Endpoint de ejemplo para búsqueda por un atributo diferente al ID.
    """
    try:
        desarrolladores = crud.buscar_desarrolladores_por_nombre(consulta_nombre=consulta_nombre)
        return desarrolladores
    except Exception as e:
        print(f"Error inesperado buscando desarrolladores por nombre: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno durante la búsqueda de desarrolladores.")

# --- Endpoints para Juegos ---

@app.post(
    "/juegos/",
    response_model=Juego,
    status_code=status.HTTP_201_CREATED,
    tags=["Juegos"],
    summary="Crear un nuevo juego"
    )

def crear_nuevo_juego(datos_juego: JuegoCrear):
    """
    Crea un nuevo juego asociado a un desarrollador existente y activo.

    - **datos_juego**: JSON con los datos del juego.
        - `titulo` (str): Requerido.
        - `genero` (str): Requerido.
        - `plataformas` (List[str]): Lista de plataformas.
        - `ano_lanzamiento` (int, opcional): Año de lanzamiento.
        - `desarrollador_id` (int): Requerido, ID de un desarrollador activo.
    \f
    :param datos_juego: Datos Pydantic validados.
    :return: El objeto Juego creado.
    :raises HTTPException 400: Si el `desarrollador_id` no corresponde a un desarrollador activo.
    :raises HTTPException 500: Si ocurre un error interno al guardar.
    """
    try:
        # La función crud maneja la validación del desarrollador (lanzando 400)
        nuevo_juego = crud.crear_juego(datos_juego=datos_juego)
        return nuevo_juego
    except HTTPException as http_exc:
        raise http_exc # Re-lanzar 400 u otros errores HTTP
    except Exception as e:
        print(f"Error inesperado al crear juego: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar crear el juego.")

@app.get(
    "/juegos/",
    response_model=List[Juego],
    tags=["Juegos"],
    summary="Listar juegos"
    )

def leer_juegos(
    saltar: int = 0,
    limite: int = 10,
    incluir_eliminados: bool = Query(False, description="Incluir juegos marcados como eliminados o cuyo desarrollador esté eliminado")
    ):
    """
    Obtiene una lista paginada de juegos.

    Por defecto, solo muestra juegos activos cuyo desarrollador asociado también esté activo.
    La opción `incluir_eliminados` permite ver todos los juegos registrados.
    """
    try:
        juegos = crud.obtener_juegos(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return juegos
    except Exception as e:
        print(f"Error inesperado al obtener juegos: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener la lista de juegos.")

@app.get(
    "/juegos/{id_juego}",
    response_model=Juego,
    tags=["Juegos"],
    summary="Obtener un juego por ID"
    )
def leer_juego_por_id(id_juego: int):
    """
    Obtiene los detalles de un juego específico usando su ID.

    Solo devuelve juegos que **no** estén marcados como eliminados y cuyo
    desarrollador asociado también esté activo.
    """
    db_juego = crud.obtener_juego_activo_por_id(id_juego=id_juego)
    if db_juego is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Juego con ID {id_juego} no encontrado, inactivo o su desarrollador está inactivo."
        )
    return db_juego
@app.put(
    "/juegos/{id_juego}",
    response_model=Juego,
    tags=["Juegos"],
    summary="Actualizar un juego"
    )

def actualizar_juego_existente(id_juego: int, datos_juego: JuegoCrear):
    """
    Actualiza la información de un juego existente.

    Permite modificar todos los campos base. Si se cambia el `desarrollador_id`,
    se valida que el nuevo ID corresponda a un desarrollador activo.
    """
    try:
        juego_actualizado = crud.actualizar_juego(
            id_juego=id_juego,
            datos_actualizacion=datos_juego
        )
        if juego_actualizado is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el juego con ID {id_juego} para actualizar."
            )
        # La excepción 400 por desarrollador inválido se maneja en crud.actualizar_juego
        return juego_actualizado
    except HTTPException as http_exc:
        raise http_exc # Re-lanzar 400, 404 u otros errores HTTP
    except Exception as e:
        print(f"Error inesperado al actualizar juego {id_juego}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar actualizar el juego.")
