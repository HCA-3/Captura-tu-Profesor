from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union
from fastapi import UploadFile, File

class ImagenBase(BaseModel):
    nombre_archivo: Optional[str] = Field(None, description="Nombre del archivo de imagen")
    url: Optional[str] = Field(None, description="URL pública de la imagen")

# --- Modelos de Juego ---
class JuegoBase(BaseModel):
    titulo: str = Field(..., example="Elden Ring")
    genero: str = Field(..., example="ARPG")
    plataformas: List[str] = Field(default_factory=list, example=["PC", "PS5", "Xbox Series X"])
    ano_lanzamiento: Optional[int] = Field(None, example=2022)
    nombre_desarrollador: Optional[str] = Field(None, example="FromSoftware")
    imagen: Optional[ImagenBase] = Field(None, description="Información de la imagen asociada")

class JuegoCrear(JuegoBase):
    pass

class Juego(JuegoBase):
    id: int
    esta_eliminado: bool = False

    model_config = ConfigDict(
        from_attributes = True,
        validate_assignment = True
    )

# --- Modelos de Consola ---
class ConsolaBase(BaseModel):
    nombre: str = Field(..., example="PlayStation 5")
    fabricante: Optional[str] = Field(None, example="Sony")
    ano_lanzamiento: Optional[int] = Field(None, example=2020)
    imagen: Optional[ImagenBase] = Field(None, description="Información de la imagen asociada")

class ConsolaCrear(ConsolaBase):
    pass

class Consola(ConsolaBase):
    id: int
    esta_eliminado: bool = False

    model_config = ConfigDict(
        from_attributes = True,
        validate_assignment = True
    )

# --- Modelos de Accesorio ---
class AccesorioBase(BaseModel):
    nombre: str = Field(..., example="DualSense Controller")
    tipo: str = Field(..., example="Control")
    fabricante: Optional[str] = Field(None, example="Sony")
    id_consola: int = Field(..., example=1682292671001, description="ID de la consola a la que pertenece este accesorio")
    imagen: Optional[ImagenBase] = Field(None, description="Información de la imagen asociada")

class AccesorioCrear(AccesorioBase):
    pass

class Accesorio(AccesorioBase):
    id: int
    esta_eliminado: bool = False

    model_config = ConfigDict(
        from_attributes = True,
        validate_assignment = True
    )

# --- Modelos para la Relación Juego-Consola-Accesorio ---
class ConsolaConAccesorios(Consola):
    """Representa una consola junto con sus accesorios asociados."""
    accesorios: List[Accesorio] = Field(default_factory=list, description="Lista de accesorios activos para esta consola")

    model_config = ConfigDict(
        from_attributes = True
    )

class JuegoCompatibilidad(BaseModel):
    """Representa la compatibilidad de un juego con consolas y sus accesorios."""
    juego: Juego = Field(..., description="Detalles del juego consultado")
    consolas_compatibles: List[ConsolaConAccesorios] = Field(default_factory=list, description="Lista de consolas compatibles con el juego, incluyendo sus accesorios")

    model_config = ConfigDict(
        from_attributes = True
    )


# --- Modelo de Respuesta para Subida de Imágenes ---
class RespuestaImagen(BaseModel):
    url: str = Field(..., description="URL de la imagen subida.")
    detail: str = Field(..., description="Detalle del resultado de la operación de subida.")

    model_config = ConfigDict(
        from_attributes = True
    )

