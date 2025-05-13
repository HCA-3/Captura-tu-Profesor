from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status, Query
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Annotated
import crud
import modelos
from modelos import (
    Juego, JuegoCrear,
    Consola, ConsolaCrear,
    Accesorio, AccesorioCrear,
    JuegoCompatibilidad
)
import os

app = FastAPI(
    title="API de Videojuegos, Consolas y Accesorios",
    description="API completa para gestionar videojuegos, consolas y accesorios con soporte para imágenes",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración para imágenes
IMAGENES_DIR = "imagenes"
os.makedirs(IMAGENES_DIR, exist_ok=True)
app.mount("/imagenes", StaticFiles(directory=IMAGENES_DIR), name="imagenes")

# --- Endpoints para Juegos ---
@app.post("/juegos/", response_model=Juego, status_code=status.HTTP_201_CREATED, tags=["Juegos"])
async def crear_juego(
    titulo: Annotated[str, Form(..., min_length=1)],
    genero: Annotated[str, Form(..., min_length=1)],
    plataformas: Annotated[List[str], Form()],
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    nombre_desarrollador: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = File(None)
):
    """
    Crea un nuevo juego con la posibilidad de subir una imagen.
    
    - **titulo**: Nombre del juego (requerido)
    - **genero**: Género principal (requerido)
    - **plataformas**: Lista de plataformas compatibles
    - **ano_lanzamiento**: Año de lanzamiento (opcional)
    - **nombre_desarrollador**: Desarrollador del juego (opcional)
    - **imagen**: Archivo de imagen (opcional)
    """
    datos_juego = JuegoCrear(
        titulo=titulo,
        genero=genero,
        plataformas=plataformas,
        ano_lanzamiento=ano_lanzamiento,
        nombre_desarrollador=nombre_desarrollador
    )
    try:
        return await crud.crear_juego(datos_juego, imagen)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/juegos/", response_model=List[Juego], tags=["Juegos"])
def listar_juegos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    incluir_eliminados: bool = Query(False)
):
    """
    Obtiene una lista paginada de juegos.
    
    - **skip**: Número de items a saltar
    - **limit**: Máximo número de items a devolver
    - **incluir_eliminados**: Incluir juegos marcados como eliminados
    """
    try:
        return crud.obtener_juegos(skip, limit, incluir_eliminados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"])
def obtener_juego(id_juego: int):
    """Obtiene los detalles de un juego específico por su ID"""
    juego = crud.obtener_juego_activo_por_id(id_juego)
    if not juego:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return juego

@app.put("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"])
async def actualizar_juego(
    id_juego: int,
    titulo: Annotated[Optional[str], Form()] = None,
    genero: Annotated[Optional[str], Form()] = None,
    plataformas: Annotated[Optional[List[str]], Form()] = None,
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    nombre_desarrollador: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = File(None)
):
    """
    Actualiza un juego existente con la posibilidad de cambiar su imagen.
    """
    datos_actualizacion = JuegoCrear(
        titulo=titulo if titulo is not None else "",
        genero=genero if genero is not None else "",
        plataformas=plataformas if plataformas is not None else [],
        ano_lanzamiento=ano_lanzamiento,
        nombre_desarrollador=nombre_desarrollador
    )
    try:
        return await crud.actualizar_juego(id_juego, datos_actualizacion, imagen)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/juegos/{id_juego}", response_model=Juego, tags=["Juegos"])
def eliminar_juego(id_juego: int):
    """Elimina lógicamente un juego (marcado como eliminado pero no borrado físicamente)"""
    try:
        return crud.eliminar_logico_juego(id_juego)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/juegos/{id_juego}/compatibilidad", response_model=JuegoCompatibilidad, tags=["Juegos"])
def compatibilidad_juego(id_juego: int):
    """Obtiene información de compatibilidad del juego con consolas y accesorios"""
    try:
        return crud.obtener_compatibilidad_juego(id_juego)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints para Consolas ---
@app.post("/consolas/", response_model=Consola, status_code=status.HTTP_201_CREATED, tags=["Consolas"])
async def crear_consola(
    nombre: Annotated[str, Form(..., min_length=1)],
    fabricante: Annotated[Optional[str], Form()] = None,
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    imagen: Optional[UploadFile] = File(None)
):
    """
    Crea una nueva consola con la posibilidad de subir una imagen.
    """
    datos_consola = ConsolaCrear(
        nombre=nombre,
        fabricante=fabricante,
        ano_lanzamiento=ano_lanzamiento
    )
    try:
        return await crud.crear_consola(datos_consola, imagen)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/consolas/", response_model=List[Consola], tags=["Consolas"])
def listar_consolas(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    incluir_eliminados: bool = Query(False)
):
    """Obtiene una lista paginada de consolas"""
    try:
        return crud.obtener_consolas(skip, limit, incluir_eliminados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"])
def obtener_consola(id_consola: int):
    """Obtiene los detalles de una consola específica por su ID"""
    consola = crud.obtener_consola_activa_por_id(id_consola)
    if not consola:
        raise HTTPException(status_code=404, detail="Consola no encontrada")
    return consola

@app.put("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"])
async def actualizar_consola(
    id_consola: int,
    nombre: Annotated[Optional[str], Form()] = None,
    fabricante: Annotated[Optional[str], Form()] = None,
    ano_lanzamiento: Annotated[Optional[int], Form()] = None,
    imagen: Optional[UploadFile] = File(None)
):
    """
    Actualiza una consola existente con la posibilidad de cambiar su imagen.
    """
    datos_actualizacion = ConsolaCrear(
        nombre=nombre if nombre is not None else "",
        fabricante=fabricante,
        ano_lanzamiento=ano_lanzamiento
    )
    try:
        return await crud.actualizar_consola(id_consola, datos_actualizacion, imagen)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/consolas/{id_consola}", response_model=Consola, tags=["Consolas"])
def eliminar_consola(id_consola: int):
    """Elimina lógicamente una consola y sus accesorios asociados"""
    try:
        return crud.eliminar_logico_consola(id_consola)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consolas/{id_consola}/accesorios", response_model=List[Accesorio], tags=["Consolas"])
def listar_accesorios_consola(
    id_consola: int,
    incluir_eliminados: bool = Query(False)
):
    """Obtiene los accesorios asociados a una consola específica"""
    try:
        return crud.obtener_accesorios_por_consola(id_consola, incluir_eliminados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints para Accesorios ---
@app.post("/accesorios/", response_model=Accesorio, status_code=status.HTTP_201_CREATED, tags=["Accesorios"])
async def crear_accesorio(
    nombre: Annotated[str, Form(..., min_length=1)],
    tipo: Annotated[str, Form(..., min_length=1)],
    id_consola: Annotated[int, Form()],
    fabricante: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = File(None)
):
    """
    Crea un nuevo accesorio con la posibilidad de subir una imagen.
    """
    datos_accesorio = AccesorioCrear(
        nombre=nombre,
        tipo=tipo,
        id_consola=id_consola,
        fabricante=fabricante
    )
    try:
        return await crud.crear_accesorio(datos_accesorio, imagen)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/accesorios/", response_model=List[Accesorio], tags=["Accesorios"])
def listar_accesorios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    incluir_eliminados: bool = Query(False)
):
    """Obtiene una lista paginada de accesorios"""
    try:
        return crud.obtener_accesorios(skip, limit, incluir_eliminados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"])
def obtener_accesorio(id_accesorio: int):
    """Obtiene los detalles de un accesorio específico por su ID"""
    accesorio = crud.obtener_accesorio_activo_por_id(id_accesorio)
    if not accesorio:
        raise HTTPException(status_code=404, detail="Accesorio no encontrado")
    return accesorio

@app.put("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"])
async def actualizar_accesorio(
    id_accesorio: int,
    nombre: Annotated[Optional[str], Form()] = None,
    tipo: Annotated[Optional[str], Form()] = None,
    id_consola: Annotated[Optional[int], Form()] = None,
    fabricante: Annotated[Optional[str], Form()] = None,
    imagen: Optional[UploadFile] = File(None)
):
    """
    Actualiza un accesorio existente con la posibilidad de cambiar su imagen.
    """
    datos_actualizacion = AccesorioCrear(
        nombre=nombre if nombre is not None else "",
        tipo=tipo if tipo is not None else "",
        id_consola=id_consola if id_consola is not None else 0,
        fabricante=fabricante
    )
    try:
        return await crud.actualizar_accesorio(id_accesorio, datos_actualizacion, imagen)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/accesorios/{id_accesorio}", response_model=Accesorio, tags=["Accesorios"])
def eliminar_accesorio(id_accesorio: int):
    """Elimina lógicamente un accesorio"""
    try:
        return crud.eliminar_logico_accesorio(id_accesorio)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint de bienvenida ---
@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Bienvenido a la API de Videojuegos, Consolas y Accesorios",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)