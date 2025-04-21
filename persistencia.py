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
                    
                    if clave in ['id', 'ano_lanzamiento', 'ano_fundacion', 'desarrollador_id']:
                        fila_procesada[clave] = int(valor) if valor else None
                    elif clave == 'esta_eliminado':
                        # Guardamos como 'True'/'False' str, leemos como bool
                        fila_procesada[clave] = valor.strip().lower() == 'true'
                    elif clave == 'plataformas':
                         # Asumiendo que guardamos la lista como string separado por comas
                        fila_procesada[clave] = [p.strip() for p in valor.split(',') if p.strip()] if valor else []
                    else:
                        fila_procesada[clave] = valor if valor else None # Guardar None si está vacío

                    # Asegurar que todas las claves esperadas existan, aunque sea con None
                for campo_esperado in nombres_campos:
                    if campo_esperado not in fila_procesada:
                         fila_procesada[campo_esperado] = None
                         
                datos.append(fila_procesada)

    except FileNotFoundError:
        # Esto no debería pasar por la comprobación inicial, pero por si acaso
        return []
    except Exception as e:
        # Manejo de errores genérico al leer CSV
        print(f"Error al leer el archivo CSV {nombre_archivo}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo cargar los datos desde {os.path.basename(nombre_archivo)}"
        ) from e
    return datos

def _guardar_datos_en_csv(nombre_archivo: str, datos: List[Dict[str, Any]], nombres_campos: List[str]):
    """Guarda datos en un archivo CSV."""
    try:
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
            escritor = csv.DictWriter(archivo_csv, fieldnames=nombres_campos, extrasaction='ignore') # Ignora claves extras en el dict
            escritor.writeheader()
            for item in datos:
                # Preparar fila asegurando el formato correcto para CSV
                fila_a_escribir = {}
                for campo in nombres_campos:
                    valor = item.get(campo)
                    if campo == 'plataformas' and isinstance(valor, list):
                        fila_a_escribir[campo] = ','.join(valor) # Convertir lista a string CSV
                    elif campo == 'esta_eliminado':
                         # Guardar booleano como 'True' o 'False'
                        fila_a_escribir[campo] = str(bool(valor))
                    else:
                        fila_a_escribir[campo] = valor if valor is not None else '' # Guardar vacío si es None

                escritor.writerow(fila_a_escribir)
    except IOError as e:
        print(f"Error al escribir en el archivo CSV {nombre_archivo}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo guardar los datos en {os.path.basename(nombre_archivo)}"
        ) from e

# Funciones específicas para cargar/guardar juegos y desarrolladores

def cargar_juegos() -> List[Dict[str, Any]]:
    """Carga la lista de juegos desde juegos.csv."""
    return _cargar_datos_desde_csv(ARCHIVO_JUEGOS, CAMPOS_JUEGO)
