import csv
import os
from typing import List, Dict, Any
from fastapi import HTTPException, status
# Asegúrate que la importación de modelos use los nombres en español
from modelos import Juego, Desarrollador