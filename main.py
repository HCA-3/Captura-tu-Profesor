from fastapi import FastAPI, HTTPException, Depends, status, Query, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Annotated
import crud
import modelos
from modelos import (
    Juego, JuegoCrear,
    Consola, ConsolaCrear,
    Accesorio, AccesorioCrear,
    JuegoCompatibilidad
)
import almacenamiento

app = FastAPI(
    title="API de Videojuegos, Consolas y Accesorios",
    description="Una API para gestionar información de videojuegos, consolas, sus accesorios y compatibilidad, incluyendo imágenes.",
    version="1.4.0"  # Versión incrementada por la adición de imágenes
)

# Montar directorio de imágenes como ruta estática
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

# --- Manejador de Excepciones Genérico ---
@app.exception_handler(Exception)
async def manejador_excepciones_generico(request, exc: Exception):
    import traceback
    print(f"Error no manejado detectado: {exc}")
    traceback.print_exc()
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )

# --- Endpoints de Juegos ---
@app.post("/juegos/", response_model=Juego, status_code=status.HTTP_201_CREATED, tags=["Juegos"])
async def crear_nuevo_juego(
    titulo: Annotated[str, Form()],
    genero: Annotated[str, Form()],
    plataformas: Annotated[List[str], Form()],
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    nombre_desarrollador: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = None
):
    """Crea un nuevo juego con imagen opcional."""
    datos_juego = modelos.JuegoCrear(
        titulo=titulo,
        genero=genero,
        plataformas=plataformas,
        ano_lanzamiento=ano_lanzamiento,
        nombre_desarrollador=nombre_desarrollador
    )
    
    try:
        return await crud.crear_juego(datos_juego=datos_juego, imagen=imagen)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al crear juego: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error interno al intentar crear el juego."
        )

@app.get("/juegos/", response_model=List[Juego], tags=["Juegos"])
def leer_juegos(
    saltar: int = Query(0, ge=0, description="Número de registros a saltar para paginación"),
    limite: int = Query(10, ge=1, le=100, description="Número máximo de registros a devolver"),
    incluir_eliminados: bool = Query(False, description="Incluir juegos marcados como eliminados")
):
    """Obtiene una lista paginada de videojuegos."""
    try:
        juegos = crud.obtener_juegos(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return juegos
    except Exception as e:
        print(f"Error inesperado al obtener juegos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la lista de juegos."
        )

@app.get("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"])
def leer_juego_por_id(id_juego: int):
    """Obtiene detalles de un videojuego específico por su ID (solo activos)."""
    db_juego = crud.obtener_juego_activo_por_id(id_juego=id_juego)
    if db_juego is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Juego con ID {id_juego} no encontrado o inactivo."
        )
    return db_juego

@app.put("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"])
async def actualizar_juego_existente(
    id_juego: int,
    titulo: Annotated[Optional[str], Form()] = None,
    genero: Annotated[Optional[str], Form()] = None,
    plataformas: Annotated[Optional[List[str]], Form()] = None,
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    nombre_desarrollador: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = None
):
    """Actualiza un juego existente con imagen opcional."""
    datos_actualizacion = modelos.JuegoCrear(
        titulo=titulo if titulo is not None else "",
        genero=genero if genero is not None else "",
        plataformas=plataformas if plataformas is not None else [],
        ano_lanzamiento=ano_lanzamiento,
        nombre_desarrollador=nombre_desarrollador
    )
    
    try:
        return await crud.actualizar_juego(
            id_juego=id_juego,
            datos_actualizacion=datos_actualizacion,
            imagen=imagen
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al actualizar juego {id_juego}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar actualizar el juego."
        )

@app.delete("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"])
def eliminar_juego_existente(id_juego: int):
    """Marca un videojuego como eliminado (borrado lógico)."""
    try:
        juego_eliminado = crud.eliminar_logico_juego(id_juego=id_juego)
        return juego_eliminado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al eliminar juego {id_juego}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar eliminar el juego."
        )

@app.get("/juegos/filtrar/por_genero/", response_model=List[Juego], tags=["Juegos"])
def filtrar_juegos_por_genero_endpoint(
    genero: str = Query(..., min_length=1, description="Género a buscar (coincidencia parcial)")
):
    """Busca juegos activos cuyo género contenga el texto proporcionado."""
    try:
        return crud.filtrar_juegos_por_genero(genero=genero)
    except Exception as e:
        print(f"Error inesperado al filtrar juegos por género: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al filtrar juegos por género."
        )

@app.get("/juegos/buscar/por_desarrollador/", response_model=List[Juego], tags=["Juegos"])
def buscar_juegos_por_desarrollador_endpoint(
    nombre_dev: str = Query(..., min_length=1, description="Nombre del desarrollador a buscar")
):
    """Busca juegos activos cuyo nombre de desarrollador contenga el texto proporcionado."""
    try:
        return crud.buscar_juegos_por_desarrollador(nombre_dev=nombre_dev)
    except Exception as e:
        print(f"Error inesperado al buscar juegos por desarrollador: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al buscar juegos por desarrollador."
        )

@app.get("/juegos/{id_juego}/compatibilidad/", response_model=JuegoCompatibilidad, tags=["Juegos", "Compatibilidad"])
def obtener_compatibilidad_juego_endpoint(id_juego: int):
    """Obtiene la información de compatibilidad de un juego con consolas y accesorios."""
    try:
        compatibilidad = crud.obtener_compatibilidad_juego(id_juego=id_juego)
        return compatibilidad
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al obtener compatibilidad para juego {id_juego}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la compatibilidad del juego."
        )

# --- Endpoints de Consolas ---
@app.post("/consolas/", response_model=Consola, status_code=status.HTTP_201_CREATED, tags=["Consolas"])
async def crear_nueva_consola(
    nombre: Annotated[str, Form()],
    fabricante: Annotated[Optional[str], Form()] = None,
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    imagen: Optional[UploadFile] = None
):
    """Crea una nueva consola con imagen opcional."""
    datos_consola = modelos.ConsolaCrear(
        nombre=nombre,
        fabricante=fabricante,
        ano_lanzamiento=ano_lanzamiento
    )
    
    try:
        return await crud.crear_consola(datos_consola=datos_consola, imagen=imagen)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al crear consola: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar crear la consola."
        )

@app.get("/consolas/", response_model=List[Consola], tags=["Consolas"])
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la lista de consolas."
        )

@app.get("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"])
def leer_consola_por_id(id_consola: int):
    """Obtiene detalles de una consola específica por su ID (solo activas)."""
    db_consola = crud.obtener_consola_activa_por_id(id_consola=id_consola)
    if db_consola is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consola con ID {id_consola} no encontrada o inactiva."
        )
    return db_consola

@app.put("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"])
async def actualizar_consola_existente(
    id_consola: int,
    nombre: Annotated[Optional[str], Form()] = None,
    fabricante: Annotated[Optional[str], Form()] = None,
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    imagen: Optional[UploadFile] = None
):
    """Actualiza una consola existente con imagen opcional."""
    datos_actualizacion = modelos.ConsolaCrear(
        nombre=nombre if nombre is not None else "",
        fabricante=fabricante,
        ano_lanzamiento=ano_lanzamiento
    )
    
    try:
        return await crud.actualizar_consola(
            id_consola=id_consola,
            datos_actualizacion=datos_actualizacion,
            imagen=imagen
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al actualizar consola {id_consola}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar actualizar la consola."
        )

@app.delete("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"])
def eliminar_consola_existente(id_consola: int):
    """Marca una consola como eliminada (borrado lógico)."""
    try:
        consola_eliminada = crud.eliminar_logico_consola(id_consola=id_consola)
        return consola_eliminada
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al eliminar consola {id_consola}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar eliminar la consola y sus accesorios."
        )

@app.get("/consolas/buscar/por_fabricante/", response_model=List[Consola], tags=["Consolas"])
def buscar_consolas_por_fabricante_endpoint(
    fabricante: str = Query(..., min_length=1, description="Fabricante a buscar")
):
    """Busca consolas activas cuyo fabricante contenga el texto proporcionado."""
    try:
        consolas = crud.buscar_consolas_por_fabricante(fabricante=fabricante)
        return consolas
    except Exception as e:
        print(f"Error inesperado buscando consolas por fabricante: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al buscar consolas."
        )

@app.get("/consolas/{id_consola}/accesorios/", response_model=List[Accesorio], tags=["Consolas", "Accesorios"])
def leer_accesorios_por_consola(
    id_consola: int,
    incluir_eliminados: bool = Query(False, description="Incluir accesorios marcados como eliminados")
):
    """Obtiene una lista de accesorios asociados a una consola."""
    consola = crud.obtener_consola_por_id(id_consola)
    if consola is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consola con ID {id_consola} no encontrada."
        )

    try:
        accesorios = crud.obtener_accesorios_por_consola(
            id_consola=id_consola,
            incluir_eliminados=incluir_eliminados
        )
        return accesorios
    except Exception as e:
        print(f"Error inesperado al obtener accesorios para consola {id_consola}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los accesorios de la consola."
        )

# --- Endpoints de Accesorios ---
@app.post("/accesorios/", response_model=Accesorio, status_code=status.HTTP_201_CREATED, tags=["Accesorios"])
async def crear_nuevo_accesorio(
    nombre: Annotated[str, Form()],
    tipo: Annotated[str, Form()],
    id_consola: Annotated[int, Form()],
    fabricante: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = None
):
    """Crea un nuevo accesorio con imagen opcional."""
    datos_accesorio = modelos.AccesorioCrear(
        nombre=nombre,
        tipo=tipo,
        fabricante=fabricante,
        id_consola=id_consola
    )
    
    try:
        return await crud.crear_accesorio(datos_accesorio=datos_accesorio, imagen=imagen)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al crear accesorio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar crear el accesorio."
        )

@app.get("/accesorios/", response_model=List[Accesorio], tags=["Accesorios"])
def leer_accesorios(
    saltar: int = Query(0, ge=0, description="Número de registros a saltar"),
    limite: int = Query(10, ge=1, le=100, description="Número máximo de registros a devolver"),
    incluir_eliminados: bool = Query(False, description="Incluir accesorios marcados como eliminados")
):
    """Obtiene una lista paginada de accesorios."""
    try:
        accesorios = crud.obtener_accesorios(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return accesorios
    except Exception as e:
        print(f"Error inesperado al obtener accesorios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la lista de accesorios."
        )

@app.get("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"])
def leer_accesorio_por_id(id_accesorio: int):
    """Obtiene detalles de un accesorio específico por su ID (solo activos)."""
    db_accesorio = crud.obtener_accesorio_activo_por_id(id_accesorio=id_accesorio)
    if db_accesorio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Accesorio con ID {id_accesorio} no encontrado o inactivo."
        )
    return db_accesorio

@app.put("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"])
async def actualizar_accesorio_existente(
    id_accesorio: int,
    nombre: Annotated[Optional[str], Form()] = None,
    tipo: Annotated[Optional[str], Form()] = None,
    id_consola: Annotated[Optional[int], Form()] = None,
    fabricante: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = None
):
    """Actualiza un accesorio existente con imagen opcional."""
    datos_actualizacion = modelos.AccesorioCrear(
        nombre=nombre if nombre is not None else "",
        tipo=tipo if tipo is not None else "",
        fabricante=fabricante,
        id_consola=id_consola if id_consola is not None else 0  # 0 será reemplazado por el valor actual
    )
    
    try:
        return await crud.actualizar_accesorio(
            id_accesorio=id_accesorio,
            datos_actualizacion=datos_actualizacion,
            imagen=imagen
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al actualizar accesorio {id_accesorio}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar actualizar el accesorio."
        )

@app.delete("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"])
def eliminar_accesorio_existente(id_accesorio: int):
    """Marca un accesorio como eliminado (borrado lógico)."""
    try:
        accesorio_eliminado = crud.eliminar_logico_accesorio(id_accesorio=id_accesorio)
        return accesorio_eliminado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al eliminar accesorio {id_accesorio}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar eliminar el accesorio."
        )

# --- Mapa de Endpoints y Raíz ---
DESCRIPCION_MAPA_ENDPOINTS = """
## Mapa de Endpoints de la API (Juegos, Consolas, Accesorios y Compatibilidad)

**Juegos:**

* `POST /juegos/`: Crea un nuevo juego (con imagen opcional).
* `GET /juegos/`: Lista juegos (paginado, opcional eliminados).
* `GET /juegos/{id_juego}`: Obtiene un juego activo por ID.
* `PUT /juegos/{id_juego}`: Actualiza un juego activo (con imagen opcional).
* `DELETE /juegos/{id_juego}`: Marca un juego como eliminado.
* `GET /juegos/filtrar/por_genero/`: Filtra juegos activos por género.
* `GET /juegos/buscar/por_desarrollador/`: Busca juegos activos por desarrollador.
* `GET /juegos/{id_juego}/compatibilidad/`: Muestra el juego, consolas compatibles y sus accesorios.

**Consolas:**

* `POST /consolas/`: Crea una nueva consola (con imagen opcional).
* `GET /consolas/`: Lista consolas (paginado, opcional eliminadas).
* `GET /consolas/{id_consola}`: Obtiene una consola activa por ID.
* `PUT /consolas/{id_consola}`: Actualiza una consola activa (con imagen opcional).
* `DELETE /consolas/{id_consola}`: Marca una consola y sus accesorios como eliminados.
* `GET /consolas/buscar/por_fabricante/`: Busca consolas activas por fabricante.
* `GET /consolas/{id_consola}/accesorios/`: Lista accesorios para una consola.

**Accesorios:**

* `POST /accesorios/`: Crea un nuevo accesorio (con imagen opcional).
* `GET /accesorios/`: Lista todos los accesorios (paginado, opcional eliminados).
* `GET /accesorios/{id_accesorio}`: Obtiene un accesorio activo por ID.
* `PUT /accesorios/{id_accesorio}`: Actualiza un accesorio activo (con imagen opcional).
* `DELETE /accesorios/{id_accesorio}`: Marca un accesorio como eliminado.
"""

@app.get("/", include_in_schema=False)
async def raiz():
    return {"mensaje": "¡Bienvenido/a a la API de Videojuegos, Consolas y Accesorios! Consulta /docs para la documentación."}

# --- Ejecución del Servidor ---
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*25 + " MAPA DE ENDPOINTS (Juegos, Consolas, Accesorios, Compatibilidad) " + "="*25)
    print(DESCRIPCION_MAPA_ENDPOINTS)
    print("="*80)
    print("Iniciando servidor Uvicorn en http://127.0.0.1:8000")
    print("Accede a la documentación interactiva (Swagger UI) en http://127.0.0.1:8000/docs")
    print("Accede a la documentación alternativa (ReDoc) en http://127.0.0.1:8000/redoc")
    print("="*80)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)