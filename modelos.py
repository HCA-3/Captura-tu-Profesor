from pydantic import BaseModel, Field, ConfigDict 
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

    model_config = ConfigDict(
        from_attributes = True, 
        validate_assignment = True 

    )


class ConsolaBase(BaseModel):
    nombre: str = Field(..., example="PlayStation 5")
    fabricante: Optional[str] = Field(None, example="Sony")
    ano_lanzamiento: Optional[int] = Field(None, example=2020)

class ConsolaCrear(ConsolaBase):
    pass 

class Consola(ConsolaBase):
    id: int
    esta_eliminado: bool = False 

    model_config = ConfigDict(
        from_attributes = True, 
        validate_assignment = True
    )