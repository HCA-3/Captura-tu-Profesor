import csv
import os
from typing import List, Dict, Any
from fastapi import HTTPException, status
# Asegúrate que la importación de modelos use los nombres en español
from modelos import Juego, Desarrollador

DIRECTORIO_DATOS = "datos" # Directorio cambiado a español
ARCHIVO_JUEGOS = os.path.join(DIRECTORIO_DATOS, "juegos.csv")
ARCHIVO_DESARROLLADORES = os.path.join(DIRECTORIO_DATOS, "desarrolladores.csv")

# Asegurarse de que el directorio de datos exista
os.makedirs(DIRECTORIO_DATOS, exist_ok=True)