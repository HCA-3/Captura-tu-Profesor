from pydantic import BaseModel, Field
from typing import Optional, List

# --- Modelo Desarrollador ---
class DesarrolladorBase(BaseModel):
    nombre: str = Field(..., example="Naughty Dog")
    pais: Optional[str] = Field(None, example="EEUU")
    ano_fundacion: Optional[int] = Field(None, example=1984)

class DesarrolladorCrear(DesarrolladorBase):
    pass # No necesita campos adicionales para la creación