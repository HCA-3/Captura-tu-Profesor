from pydantic import BaseModel, Field
from typing import Optional, List

class JuegoBase(BaseModel):
    titulo: str = Field(..., example="Elden Ring")
    genero: str = Field(..., example="ARPG")
    plataformas: List[str] = Field(default_factory=list, example=["PC", "PS5", "Xbox Series X"])
    ano_lanzamiento: Optional[int] = Field(None, example=2022)
    nombre_desarrollador: Optional[str] = Field(None, example="FromSoftware")

class JuegoCrear(JuegoBase):
    pass 

class Juego(JuegoBase):
    id: int
    esta_eliminado: bool = False 

    class Config:
        orm_mode = True
        allow_population_by_field_name = True 