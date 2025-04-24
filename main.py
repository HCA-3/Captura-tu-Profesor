from fastapi import FastAPI, HTTPException, Depends, status, Query
from typing import List, Optional
import crud
import modelos
# Importar todos los modelos necesarios
from modelos import (
    Juego, JuegoCrear,
    Consola, ConsolaCrear,
    Accesorio, AccesorioCrear # Añadir modelos de Accesorio
)

app = FastAPI(
    title="API de Videojuegos, Consolas y Accesorios", # Título actualizado
    description="Una API para gestionar información de videojuegos, consolas y sus accesorios.", # Descripción actualizada
    version="1.2.0" # Versión incrementada
)

# --- Manejador de Excepciones Genérico ---
@app.exception_handler(Exception)
async def manejador_excepciones_generico(request, exc: Exception):
    # Es buena idea loggear el error completo para debugging
    import traceback
    print(f"Error no manejado detectado: {exc}")
    traceback.print_exc() # Imprime el stack trace completo en la consola del servidor
    from fastapi.responses import JSONResponse
    # Devolver un mensaje genérico al cliente por seguridad
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )

# --- Endpoints de Juegos ---
@app.post("/juegos/", response_model=Juego, status_code=status.HTTP_201_CREATED, tags=["Juegos"], summary="Crear un nuevo juego")
def crear_nuevo_juego(datos_juego: JuegoCrear):
    """
    Crea un nuevo registro de videojuego en la base de datos.

    - **titulo**: Nombre del juego (requerido).
    - **genero**: Género principal (requerido).
    - **plataformas**: Lista de plataformas donde está disponible.
    - **ano_lanzamiento**: Año de lanzamiento (opcional).
    - **nombre_desarrollador**: Nombre del estudio desarrollador (opcional).

    *Retorna el objeto del juego creado.*
    """
    try:
        return crud.crear_juego(datos_juego=datos_juego)
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP específicas (como 409 Conflict)
        raise http_exc
    except Exception as e:
        # Capturar otros errores y devolver 500
        print(f"Error inesperado al crear juego: {e}") # Loggear el error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar crear el juego.")

@app.get("/juegos/", response_model=List[Juego], tags=["Juegos"], summary="Listar juegos")
def leer_juegos(
    saltar: int = Query(0, ge=0, description="Número de registros a saltar para paginación"),
    limite: int = Query(10, ge=1, le=100, description="Número máximo de registros a devolver"), # Límite máximo razonable
    incluir_eliminados: bool = Query(False, description="Incluir juegos marcados como eliminados")
):
    """
    Obtiene una lista paginada de videojuegos.
    Permite incluir opcionalmente los juegos marcados como eliminados.
    """
    try:
        juegos = crud.obtener_juegos(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return juegos
    except Exception as e:
        print(f"Error inesperado al obtener juegos: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener la lista de juegos.")


@app.get("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"], summary="Obtener un juego por ID")
def leer_juego_por_id(id_juego: int):
    """Obtiene detalles de un videojuego específico por su ID (solo activos)."""
    db_juego = crud.obtener_juego_activo_por_id(id_juego=id_juego)
    if db_juego is None:
        # Devolver 404 si no se encuentra o está inactivo
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado o inactivo.")
    return db_juego

@app.put("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"], summary="Actualizar un juego")
def actualizar_juego_existente(id_juego: int, datos_juego: JuegoCrear):
    """
    Actualiza la información de un videojuego existente por su ID.
    Solo se pueden actualizar juegos activos.
    Proporciona los campos a modificar en el cuerpo de la solicitud.
    """
    try:
        # La función crud.actualizar_juego ya maneja el 404 si no existe o está eliminado
        juego_actualizado = crud.actualizar_juego(id_juego=id_juego, datos_actualizacion=datos_juego)
        # No es necesario verificar 'is None' aquí si crud lanza la excepción
        return juego_actualizado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al actualizar juego {id_juego}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar actualizar el juego.")

@app.delete("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"], summary="Eliminar (lógicamente) un juego")
def eliminar_juego_existente(id_juego: int):
    """
    Marca un videojuego como eliminado (borrado lógico).
    El juego no se borra físicamente, pero se marca como inactivo.
    Retorna el objeto del juego marcado como eliminado.
    """
    try:
         # La función crud.eliminar_logico_juego maneja 404 y 409
        juego_eliminado = crud.eliminar_logico_juego(id_juego=id_juego)
        return juego_eliminado
    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
         print(f"Error inesperado al eliminar juego {id_juego}: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar eliminar el juego.")


@app.get("/juegos/filtrar/por_genero/", response_model=List[Juego], tags=["Juegos"], summary="Filtrar juegos por género")
def filtrar_juegos_por_genero_endpoint(genero: str = Query(..., min_length=1, description="Género a buscar (coincidencia parcial, insensible a mayúsculas)")):
    """Busca juegos activos cuyo género contenga el texto proporcionado."""
    try:
        return crud.filtrar_juegos_por_genero(genero=genero)
    except Exception as e:
        print(f"Error inesperado al filtrar juegos por género: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al filtrar juegos por género.")

@app.get("/juegos/buscar/por_desarrollador/", response_model=List[Juego], tags=["Juegos"], summary="Buscar juegos por nombre de desarrollador")
def buscar_juegos_por_desarrollador_endpoint(nombre_dev: str = Query(..., min_length=1, description="Nombre del desarrollador a buscar (coincidencia parcial, insensible a mayúsculas)")):
    """Busca juegos activos cuyo nombre de desarrollador contenga el texto proporcionado."""
    try:
        return crud.buscar_juegos_por_desarrollador(nombre_dev=nombre_dev)
    except Exception as e:
        print(f"Error inesperado al buscar juegos por desarrollador: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al buscar juegos por desarrollador.")

# --- Endpoints de Consolas ---
@app.post("/consolas/", response_model=Consola, status_code=status.HTTP_201_CREATED, tags=["Consolas"], summary="Crear una nueva consola")
def crear_nueva_consola(datos_consola: ConsolaCrear):
    """
    Crea un nuevo registro de consola.

    - **nombre**: Nombre de la consola (requerido).
    - **fabricante**: Fabricante de la consola (opcional).
    - **ano_lanzamiento**: Año de lanzamiento (opcional).

    *Retorna el objeto de la consola creada.*
    """
    try:
        nueva_consola = crud.crear_consola(datos_consola=datos_consola)
        return nueva_consola
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al crear consola: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar crear la consola.")

@app.get("/consolas/", response_model=List[Consola], tags=["Consolas"], summary="Listar consolas")
def leer_consolas(
    saltar: int = Query(0, ge=0, description="Número de registros a saltar"),
    limite: int = Query(10, ge=1, le=100, description="Número máximo de registros a devolver"),
    incluir_eliminados: bool = Query(False, description="Incluir consolas marcadas como eliminadas")
):
    """Obtiene una lista paginada de consolas."""
    try:
        consolas = crud.obtener_consolas(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return consolas
    except Exception as e:
        print(f"Error inesperado al obtener consolas: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener la lista de consolas.")

@app.get("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"], summary="Obtener una consola por ID")
def leer_consola_por_id(id_consola: int):
    """Obtiene detalles de una consola específica por su ID (solo activas)."""
    db_consola = crud.obtener_consola_activa_por_id(id_consola=id_consola)
    if db_consola is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada o inactiva.")
    return db_consola

@app.put("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"], summary="Actualizar una consola")
def actualizar_consola_existente(id_consola: int, datos_consola: ConsolaCrear):
    """Actualiza la información de una consola existente por su ID (solo activas)."""
    try:
        # crud.actualizar_consola maneja 404
        consola_actualizada = crud.actualizar_consola(id_consola=id_consola, datos_actualizacion=datos_consola)
        return consola_actualizada
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al actualizar consola {id_consola}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar actualizar la consola.")

@app.delete("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"], summary="Eliminar (lógicamente) una consola")
def eliminar_consola_existente(id_consola: int):
    """Marca una consola como eliminada (borrado lógico)."""
    try:
        # crud.eliminar_logico_consola maneja 404 y 409
        consola_eliminada = crud.eliminar_logico_consola(id_consola=id_consola)
        # Opcional: Decidir si eliminar lógicamente los accesorios asociados
        # accesorios_asociados = crud.obtener_accesorios_por_consola(id_consola, incluir_eliminados=True)
        # for acc in accesorios_asociados:
        #     if not acc.get('esta_eliminado'):
        #         crud.eliminar_logico_accesorio(acc['id']) # ¡Cuidado con llamadas recursivas o bucles si hay dependencias!
        return consola_eliminada
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al eliminar consola {id_consola}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar eliminar la consola.")


@app.get("/consolas/buscar/por_fabricante/", response_model=List[Consola], tags=["Consolas"], summary="Buscar consolas por fabricante")
def buscar_consolas_por_fabricante_endpoint(fabricante: str = Query(..., min_length=1, description="Fabricante a buscar (parcial, insensible a mayúsculas)")):
    """Busca consolas activas cuyo fabricante contenga el texto proporcionado."""
    try:
        consolas = crud.buscar_consolas_por_fabricante(fabricante=fabricante)
        return consolas
    except Exception as e:
        print(f"Error inesperado buscando consolas por fabricante: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al buscar consolas.")

# --- Endpoints de Accesorios (Nuevo) ---
@app.post("/accesorios/", response_model=Accesorio, status_code=status.HTTP_201_CREATED, tags=["Accesorios"], summary="Crear un nuevo accesorio")
def crear_nuevo_accesorio(datos_accesorio: AccesorioCrear):
    """
    Crea un nuevo accesorio y lo asocia a una consola existente y activa.

    - **nombre**: Nombre del accesorio (requerido).
    - **tipo**: Tipo de accesorio (e.g., 'Control', 'Headset', 'Cámara') (requerido).
    - **fabricante**: Fabricante del accesorio (opcional).
    - **id_consola**: ID de la consola a la que pertenece (requerido). La consola debe existir y estar activa.

    *Retorna el objeto del accesorio creado.*
    """
    try:
        # crud.crear_accesorio maneja la validación de la consola y duplicados
        nuevo_accesorio = crud.crear_accesorio(datos_accesorio=datos_accesorio)
        return nuevo_accesorio
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al crear accesorio: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar crear el accesorio.")

@app.get("/accesorios/", response_model=List[Accesorio], tags=["Accesorios"], summary="Listar accesorios")
def leer_accesorios(
    saltar: int = Query(0, ge=0, description="Número de registros a saltar"),
    limite: int = Query(10, ge=1, le=100, description="Número máximo de registros a devolver"),
    incluir_eliminados: bool = Query(False, description="Incluir accesorios marcados como eliminados")
):
    """Obtiene una lista paginada de todos los accesorios."""
    try:
        accesorios = crud.obtener_accesorios(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return accesorios
    except Exception as e:
        print(f"Error inesperado al obtener accesorios: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener la lista de accesorios.")


@app.get("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"], summary="Obtener un accesorio por ID")
def leer_accesorio_por_id(id_accesorio: int):
    """Obtiene detalles de un accesorio específico por su ID (solo activos)."""
    db_accesorio = crud.obtener_accesorio_activo_por_id(id_accesorio=id_accesorio)
    if db_accesorio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Accesorio con ID {id_accesorio} no encontrado o inactivo.")
    return db_accesorio

@app.put("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"], summary="Actualizar un accesorio")
def actualizar_accesorio_existente(id_accesorio: int, datos_accesorio: AccesorioCrear):
    """
    Actualiza la información de un accesorio existente por su ID (solo activos).
    Permite cambiar los detalles y re-asociarlo a otra consola activa si se incluye `id_consola`.
    """
    try:
        # crud.actualizar_accesorio maneja 404 y validaciones de consola/duplicados
        accesorio_actualizado = crud.actualizar_accesorio(id_accesorio=id_accesorio, datos_actualizacion=datos_accesorio)
        return accesorio_actualizado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al actualizar accesorio {id_accesorio}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar actualizar el accesorio.")

@app.delete("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"], summary="Eliminar (lógicamente) un accesorio")
def eliminar_accesorio_existente(id_accesorio: int):
    """Marca un accesorio como eliminado (borrado lógico)."""
    try:
        # crud.eliminar_logico_accesorio maneja 404 y 409
        accesorio_eliminado = crud.eliminar_logico_accesorio(id_accesorio=id_accesorio)
        return accesorio_eliminado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al eliminar accesorio {id_accesorio}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar eliminar el accesorio.")

# --- Endpoint específico para Accesorios por Consola ---
@app.get("/consolas/{id_consola}/accesorios/", response_model=List[Accesorio], tags=["Consolas", "Accesorios"], summary="Listar accesorios de una consola específica")
def leer_accesorios_por_consola(
    id_consola: int,
    incluir_eliminados: bool = Query(False, description="Incluir accesorios marcados como eliminados")
):
    """
    Obtiene una lista de todos los accesorios asociados a una consola específica por su ID.
    La consola debe existir, pero no necesariamente estar activa para listar sus accesorios históricos (a menos que se modifique la lógica).
    """
    try:
        # crud.obtener_accesorios_por_consola maneja el 404 de la consola
        accesorios = crud.obtener_accesorios_por_consola(id_consola=id_consola, incluir_eliminados=incluir_eliminados)
        return accesorios
    except HTTPException as http_exc:
        raise http_exc # Re-lanzar 404 si la consola no existe
    except Exception as e:
        print(f"Error inesperado al obtener accesorios para consola {id_consola}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener los accesorios de la consola.")


# --- Mapa de Endpoints y Raíz ---

DESCRIPCION_MAPA_ENDPOINTS = """
## Mapa de Endpoints de la API (Juegos, Consolas y Accesorios)

**Juegos:**

* `POST /juegos/`: Crea un nuevo juego.
* `GET /juegos/`: Lista juegos (paginado, opcional eliminados).
* `GET /juegos/{id_juego}`: Obtiene un juego activo por ID.
* `PUT /juegos/{id_juego}`: Actualiza un juego activo por ID.
* `DELETE /juegos/{id_juego}`: Marca un juego como eliminado.
* `GET /juegos/filtrar/por_genero/`: Filtra juegos activos por género.
* `GET /juegos/buscar/por_desarrollador/`: Busca juegos activos por desarrollador.

**Consolas:**

* `POST /consolas/`: Crea una nueva consola.
* `GET /consolas/`: Lista consolas (paginado, opcional eliminados).
* `GET /consolas/{id_consola}`: Obtiene una consola activa por ID.
* `PUT /consolas/{id_consola}`: Actualiza una consola activa por ID.
* `DELETE /consolas/{id_consola}`: Marca una consola como eliminada.
* `GET /consolas/buscar/por_fabricante/`: Busca consolas activas por fabricante.
* `GET /consolas/{id_consola}/accesorios/`: Lista accesorios (opcional eliminados) para una consola específica.

**Accesorios:**

* `POST /accesorios/`: Crea un nuevo accesorio para una consola activa.
* `GET /accesorios/`: Lista todos los accesorios (paginado, opcional eliminados).
* `GET /accesorios/{id_accesorio}`: Obtiene un accesorio activo por ID.
* `PUT /accesorios/{id_accesorio}`: Actualiza un accesorio activo por ID (puede cambiar la consola asociada).
* `DELETE /accesorios/{id_accesorio}`: Marca un accesorio como eliminado.
"""

@app.get("/", include_in_schema=False)
async def raiz():
    return {"mensaje": "¡Bienvenido/a a la API de Videojuegos, Consolas y Accesorios! Consulta /docs para la documentación."}

# --- Ejecución del Servidor (si se corre este archivo directamente) ---
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*25 + " MAPA DE ENDPOINTS (Juegos, Consolas, Accesorios) " + "="*25)
    print(DESCRIPCION_MAPA_ENDPOINTS)
    print("="*80)
    print("Iniciando servidor Uvicorn en http://127.0.0.1:8000")
    print("Accede a la documentación interactiva (Swagger UI) en http://127.0.0.1:8000/docs")
    print("Accede a la documentación alternativa (ReDoc) en http://127.0.0.1:8000/redoc")
    print("="*80)
    # reload=True es útil para desarrollo, considera quitarlo en producción
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)