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

# Definir las cabeceras (fieldnames) para cada CSV EN ESPAÑOL
CAMPOS_JUEGO = ['id', 'titulo', 'genero', 'plataformas', 'ano_lanzamiento', 'desarrollador_id', 'esta_eliminado']
CAMPOS_DESARROLLADOR = ['id', 'nombre', 'pais', 'ano_fundacion', 'esta_eliminado']

def _cargar_datos_desde_csv(nombre_archivo: str, nombres_campos: List[str]) -> List[Dict[str, Any]]:
    """Carga datos desde un archivo CSV."""
    if not os.path.exists(nombre_archivo):
        # Si el archivo no existe, lo creamos con las cabeceras
        try:
            with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
                escritor = csv.DictWriter(archivo_csv, fieldnames=nombres_campos)
                escritor.writeheader()
            return []
        except IOError as e:
            print(f"Error: No se pudo crear el archivo CSV inicial {nombre_archivo}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"No se pudo crear el archivo de datos necesario: {os.path.basename(nombre_archivo)}"
            ) from e

datos = []
    try:
        with open(nombre_archivo, mode='r', newline='', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            # Validación simple de cabeceras (podría ser más robusta)
            if not lector.fieldnames or set(lector.fieldnames) != set(nombres_campos):
                 print(f"Advertencia: Las cabeceras del CSV {nombre_archivo} no coinciden o están vacías. Esperadas: {nombres_campos}, Encontradas: {lector.fieldnames}. Se intentará continuar.")
                 
            for fila in lector:
                # Convertir tipos de datos y manejar posibles valores faltantes o incorrectos
                fila_procesada = {}
                for clave, valor in fila.items():
                    if clave not in nombres_campos: # Ignorar columnas extra no esperadas
                        continue