from pydantic import BaseModel, Field
from typing import Optional, List

# --- Modelo Desarrollador ---
class DesarrolladorBase(BaseModel):
    nombre: str = Field(..., example="Naughty Dog")
    pais: Optional[str] = Field(None, example="EEUU")
    ano_fundacion: Optional[int] = Field(None, example=1984)

class DesarrolladorCrear(DesarrolladorBase):
    pass # No necesita campos adicionales para la creación

class Desarrollador(DesarrolladorBase):
    id: int
    esta_eliminado: bool = False # Para borrado lógico
    
 class Config:
        orm_mode = True # Permite compatibilidad con ORMs, útil aquí para estructura
        allow_population_by_field_name = True # Permite usar 'ano_fundacion' en lugar de 'ano_fundacion' si es necesario

class JuegoBase(BaseModel):
    titulo: str = Field(..., example="The Last of Us Parte II")
    genero: str = Field(..., example="Acción-Aventura")
    plataformas: List[str] = Field(default_factory=list, example=["PlayStation 4", "PlayStation 5"])
    ano_lanzamiento: Optional[int] = Field(None, example=2020)
    desarrollador_id: int = Field(..., example=1) # Clave foránea al desarrollador

class JuegoCrear(JuegoBase):
    pass # No necesita campos adicionales para la creación

class Juego(JuegoBase):
    id: int
    esta_eliminado: bool = False # Para borrado lógico
    
class Config:
        orm_mode = True
        allow_population_by_field_name = True