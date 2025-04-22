from fastapi import FastAPI, HTTPException, Depends, status, Query
from typing import List, Optional
import crud
import modelos
from modelos import Juego, JuegoCrear, Consola, ConsolaCrear 

app = FastAPI(
    title="API de Videojuegos y Consolas",
    description="Una API para gestionar información de videojuegos y consolas.",
    version="1.1.0" 
)

@app.exception_handler(Exception)
async def manejador_excepciones_generico(request, exc: Exception):
    print(f"Error no manejado detectado: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )

@app.post("/juegos/", response_model=Juego, status_code=status.HTTP_201_CREATED, tags=["Juegos"], summary="Crear un nuevo juego")
def crear_nuevo_juego(datos_juego: JuegoCrear):
    try: return crud.crear_juego(datos_juego=datos_juego)
    except HTTPException as http_exc: raise http_exc
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear juego.")

@app.get("/juegos/", response_model=List[Juego], tags=["Juegos"], summary="Listar juegos")
def leer_juegos(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = Query(False, description="Incluir juegos marcados como eliminados")):
    try: return crud.obtener_juegos(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener juegos.")

@app.get("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"], summary="Obtener un juego por ID")
def leer_juego_por_id(id_juego: int):
    db_juego = crud.obtener_juego_activo_por_id(id_juego=id_juego)
    if db_juego is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado o inactivo.")
    return db_juego

@app.put("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"], summary="Actualizar un juego")
def actualizar_juego_existente(id_juego: int, datos_juego: JuegoCrear):
    try:
        juego_actualizado = crud.actualizar_juego(id_juego=id_juego, datos_actualizacion=datos_juego)
        if juego_actualizado is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado.")
        return juego_actualizado
    except HTTPException as http_exc: raise http_exc
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar juego.")

@app.delete("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"], summary="Eliminar (lógicamente) un juego")
def eliminar_juego_existente(id_juego: int):
    juego_eliminado = crud.eliminar_logico_juego(id_juego=id_juego)
    if juego_eliminado is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado o ya eliminado.")
    return juego_eliminado

@app.get("/juegos/filtrar/por_genero/", response_model=List[Juego], tags=["Juegos"], summary="Filtrar juegos por género")
def filtrar_juegos_por_genero_endpoint(genero: str = Query(..., min_length=1, description="Género a buscar")):
    try: return crud.filtrar_juegos_por_genero(genero=genero)
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al filtrar juegos.")

@app.get("/juegos/buscar/por_desarrollador/", response_model=List[Juego], tags=["Juegos"], summary="Buscar juegos por nombre de desarrollador")
def buscar_juegos_por_desarrollador_endpoint(nombre_dev: str = Query(..., min_length=1, description="Nombre del desarrollador a buscar")):
    try: return crud.buscar_juegos_por_desarrollador(nombre_dev=nombre_dev)
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al buscar juegos.")


@app.post("/consolas/", response_model=Consola, status_code=status.HTTP_201_CREATED, tags=["Consolas"], summary="Crear una nueva consola")
def crear_nueva_consola(datos_consola: ConsolaCrear):
    """Crea una nueva consola."""
    try:
        nueva_consola = crud.crear_consola(datos_consola=datos_consola)
        return nueva_consola
    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        print(f"Error inesperado al crear consola: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar crear la consola.")

@app.get("/consolas/", response_model=List[Consola], tags=["Consolas"], summary="Listar consolas")
def leer_consolas(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = Query(False, description="Incluir consolas marcadas como eliminadas")):
    """Obtiene una lista paginada de consolas."""
    try:
        consolas = crud.obtener_consolas(saltar=saltar, limite=limite, incluir_eliminados=incluir_eliminados)
        return consolas
    except Exception as e:
        print(f"Error inesperado al obtener consolas: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener la lista de consolas.")

@app.get("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"], summary="Obtener una consola por ID")
def leer_consola_por_id(id_consola: int):
    """Obtiene detalles de una consola específica (solo activas)."""
    db_consola = crud.obtener_consola_activa_por_id(id_consola=id_consola)
    if db_consola is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada o inactiva.")
    return db_consola

@app.put("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"], summary="Actualizar una consola")
def actualizar_consola_existente(id_consola: int, datos_consola: ConsolaCrear):
    """Actualiza la información de una consola existente."""
    try:
        consola_actualizada = crud.actualizar_consola(id_consola=id_consola, datos_actualizacion=datos_consola)
        if consola_actualizada is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada.")
        return consola_actualizada
    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        print(f"Error inesperado al actualizar consola {id_consola}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al intentar actualizar la consola.")

@app.delete("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"], summary="Eliminar (lógicamente) una consola")
def eliminar_consola_existente(id_consola: int):
    """Marca una consola como eliminada (borrado lógico)."""
    consola_eliminada = crud.eliminar_logico_consola(id_consola=id_consola)
    if consola_eliminada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada o ya eliminada.")
    return consola_eliminada 
@app.get("/consolas/buscar/por_fabricante/", response_model=List[Consola], tags=["Consolas"], summary="Buscar consolas por fabricante")
def buscar_consolas_por_fabricante_endpoint(fabricante: str = Query(..., min_length=1, description="Fabricante a buscar")):
    """Busca consolas activas por fabricante."""
    try:
        consolas = crud.buscar_consolas_por_fabricante(fabricante=fabricante)
        return consolas
    except Exception as e:
        print(f"Error inesperado buscando consolas: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al buscar consolas.")

DESCRIPCION_MAPA_ENDPOINTS = """
## Mapa de Endpoints de la API (Juegos y Consolas)

**Juegos:**

* **`POST /juegos/`**: Crea un nuevo juego. (Body: `titulo`, `genero`, `plataformas`, `ano_lanzamiento`, `nombre_desarrollador`)
* **`GET /juegos/`**: Lista juegos. (Params: `saltar`, `limite`, `incluir_eliminados`)
* **`GET /juegos/{id_juego}`**: Obtiene un juego activo por ID.
* **`PUT /juegos/{id_juego}`**: Actualiza un juego por ID. (Body: igual que POST)
* **`DELETE /juegos/{id_juego}`**: Marca un juego como eliminado.
* **`GET /juegos/filtrar/por_genero/`**: Filtra juegos activos por género. (Param: `genero`)
* **`GET /juegos/buscar/por_desarrollador/`**: Busca juegos activos por nombre de desarrollador. (Param: `nombre_dev`)

**Consolas:**

* **`POST /consolas/`**: Crea una nueva consola. (Body: `nombre`, `fabricante`, `ano_lanzamiento`)
* **`GET /consolas/`**: Lista consolas. (Params: `saltar`, `limite`, `incluir_eliminados`)
* **`GET /consolas/{id_consola}`**: Obtiene una consola activa por ID.
* **`PUT /consolas/{id_consola}`**: Actualiza una consola por ID. (Body: igual que POST)
* **`DELETE /consolas/{id_consola}`**: Marca una consola como eliminada.
* **`GET /consolas/buscar/por_fabricante/`**: Busca consolas activas por fabricante. (Param: `fabricante`)
"""

@app.get("/", include_in_schema=False)
async def raiz():
    return {"mensaje": "¡Bienvenido/a a la API de Videojuegos y Consolas! Consulta /docs para la documentación."}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*25 + " MAPA DE ENDPOINTS (Juegos y Consolas) " + "="*25)
    print(DESCRIPCION_MAPA_ENDPOINTS)
    print("="*80)
    print("Iniciando servidor Uvicorn en http://127.0.0.1:8000")
    print("Accede a la documentación interactiva (Swagger UI) en http://127.0.0.1:8000/docs")
    print("="*80)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)