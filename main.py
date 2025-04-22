from fastapi import FastAPI, HTTPException, Depends, status, Query
from typing import List, Optional
import crud
import modelos
from modelos import Juego, JuegoCrear 

app = FastAPI(
    title="API de Videojuegos (Simplificada)",
    description="Una API para gestionar información de videojuegos.",
    version="1.0.0"
)

@app.exception_handler(Exception)
async def manejador_excepciones_generico(request, exc: Exception):
    print(f"Error no manejado detectado: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )

@app.post(
    "/juegos/",
    response_model=Juego,
    status_code=status.HTTP_201_CREATED,
    tags=["Juegos"],
    summary="Crear un nuevo juego"
    )
def crear_nuevo_juego(datos_juego: JuegoCrear):
    """
    Crea un nuevo juego en la base de datos (archivo CSV).

    - **datos_juego**: JSON con los datos del juego.
        - `titulo` (str): Requerido.
        - `genero` (str): Requerido.
        - `plataformas` (List[str]): Lista de plataformas.
        - `ano_lanzamiento` (int, opcional): Año de lanzamiento.
        - `nombre_desarrollador` (str, opcional): Nombre del desarrollador.
    \f
    :param datos_juego: Datos Pydantic validados.
    :return: El objeto Juego creado.
    :raises HTTPException 500: Si ocurre un error interno al guardar.
    """
    try:
        nuevo_juego = crud.crear_juego(datos_juego=datos_juego)
        return nuevo_juego
    except HTTPException as http_exc:
        raise http_exc
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
    incluir_eliminados: bool = Query(False, description="Incluir juegos marcados como eliminados")
    ):
    """
    Obtiene una lista paginada de juegos.

    Permite incluir opcionalmente los juegos marcados como eliminados.
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

    Solo devuelve juegos que **no** estén marcados como eliminados.
    """
    db_juego = crud.obtener_juego_activo_por_id(id_juego=id_juego)
    if db_juego is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Juego con ID {id_juego} no encontrado o está inactivo."
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
    Permite modificar todos los campos base, incluyendo 'nombre_desarrollador'.
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
        return juego_actualizado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al actualizar juego {id_juego}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar actualizar el juego.")

@app.delete(
    "/juegos/{id_juego}",
    response_model=Juego,
    tags=["Juegos"],
    summary="Eliminar (lógicamente) un juego"
    )
def eliminar_juego_existente(id_juego: int):
    """
    Marca un juego como eliminado (borrado lógico). (Sin cambios)
    """
    juego_eliminado = crud.eliminar_logico_juego(id_juego=id_juego)
    if juego_eliminado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el juego con ID {id_juego} o ya estaba eliminado."
        )
    return juego_eliminado

@app.get(
    "/juegos/filtrar/por_genero/",
    response_model=List[Juego],
    tags=["Juegos"],
    summary="Filtrar juegos por género"
    )
def filtrar_juegos_por_genero_endpoint( # Renombrado para evitar conflicto con la función crud
    genero: str = Query(..., min_length=1, description="Género por el cual filtrar (búsqueda parcial, insensible a mayúsculas)")
    ):
    """
    Filtra la lista de juegos activos cuyo género contenga el texto proporcionado.
    """
    try:
        juegos = crud.filtrar_juegos_por_genero(genero=genero)
        return juegos
    except Exception as e:
        print(f"Error inesperado filtrando juegos por género: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno durante el filtrado de juegos.")

@app.get(
    "/juegos/buscar/por_desarrollador/",
    response_model=List[Juego],
    tags=["Juegos"],
    summary="Buscar juegos por nombre de desarrollador"
    )
def buscar_juegos_por_desarrollador_endpoint(
    nombre_dev: str = Query(..., min_length=1, description="Nombre del desarrollador a buscar (búsqueda parcial, insensible a mayúsculas)")
    ):
    """
    Busca juegos activos cuyo campo 'nombre_desarrollador' contenga el texto proporcionado.
    """
    try:
        juegos = crud.buscar_juegos_por_desarrollador(nombre_dev=nombre_dev)
        return juegos
    except Exception as e:
        print(f"Error inesperado buscando juegos por desarrollador: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno durante la búsqueda de juegos por desarrollador.")

DESCRIPCION_MAPA_ENDPOINTS = """
## Mapa de Endpoints de la API de Videojuegos (Simplificada)

A continuación se describen los endpoints disponibles:

**Juegos:**

* **`POST /juegos/`**: Crea un nuevo juego.
    * *Body (JSON)*: `titulo`(str, req.), `genero`(str, req.), `plataformas`(List[str]), `ano_lanzamiento`(int, opc.), `nombre_desarrollador`(str, opc.).
    * *Respuesta*: JSON del juego creado (incluye `id`, `esta_eliminado=False`). Status 201.
    * *Errores*: 422 (Validación), 500 (Interno).
* **`GET /juegos/`**: Lista juegos (paginado).
    * *Query Params*: `saltar` (int, def 0), `limite` (int, def 10), `incluir_eliminados` (bool, def False).
    * *Respuesta*: Lista [JSON] de juegos. Status 200.
    * *Errores*: 500 (Interno).
* **`GET /juegos/{id_juego}`**: Obtiene un juego activo por ID.
    * *Path Param*: `id_juego` (int).
    * *Respuesta*: JSON del juego. Status 200.
    * *Errores*: 404 (No encontrado o inactivo), 422 (ID inválido).
* **`PUT /juegos/{id_juego}`**: Actualiza un juego por ID.
    * *Path Param*: `id_juego` (int).
    * *Body (JSON)*: Campos a actualizar (`titulo`, `genero`, `plataformas`, `ano_lanzamiento`, `nombre_desarrollador`).
    * *Respuesta*: JSON del juego actualizado. Status 200.
    * *Errores*: 404 (Juego no encontrado), 422 (Validación), 500 (Interno).
* **`DELETE /juegos/{id_juego}`**: Marca un juego como eliminado (borrado lógico).
    * *Path Param*: `id_juego` (int).
    * *Respuesta*: JSON del juego con `esta_eliminado=True`. Status 200.
    * *Errores*: 404 (No encontrado o ya eliminado), 422 (ID inválido).
* **`GET /juegos/filtrar/por_genero/`**: Filtra juegos activos por género.
    * *Query Param*: `genero` (str, req.).
    * *Respuesta*: Lista [JSON] de juegos activos coincidentes. Status 200.
    * *Errores*: 422 (Query param faltante/inválido), 500 (Interno).
* **`GET /juegos/buscar/por_desarrollador/`**: Busca juegos activos por nombre de desarrollador.
    * *Query Param*: `nombre_dev` (str, req.).
    * *Respuesta*: Lista [JSON] de juegos activos coincidentes. Status 200.
    * *Errores*: 422 (Query param faltante/inválido), 500 (Interno).
"""

@app.get("/", include_in_schema=False)
async def raiz():
    return {"mensaje": "¡Bienvenido/a a la API de Videojuegos (Simplificada)! Consulta /docs para la documentación."}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*25 + " MAPA DE ENDPOINTS (Simplificado) " + "="*25)
    print(DESCRIPCION_MAPA_ENDPOINTS)
    print("="*80)
    print("Iniciando servidor Uvicorn en http://127.0.0.1:8000")
    print("Accede a la documentación interactiva (Swagger UI) en http://127.0.0.1:8000/docs")
    print("="*80)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)