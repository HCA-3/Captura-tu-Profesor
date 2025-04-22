import csv
import os
from typing import List, Dict, Any
from fastapi import HTTPException, status
from modelos import Juego

DIRECTORIO_DATOS = "datos"
ARCHIVO_JUEGOS = os.path.join(DIRECTORIO_DATOS, "juegos.csv")

os.makedirs(DIRECTORIO_DATOS, exist_ok=True)

CAMPOS_JUEGO = [
    'id', 'titulo', 'genero', 'plataformas',
    'ano_lanzamiento', 'nombre_desarrollador',
    'esta_eliminado'
]

def _cargar_datos_desde_csv(nombre_archivo: str, nombres_campos: List[str]) -> List[Dict[str, Any]]:
    """Carga datos desde un archivo CSV."""
    if not os.path.exists(nombre_archivo):
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
            if not lector.fieldnames or set(lector.fieldnames) != set(nombres_campos):
                 print(f"Advertencia: Las cabeceras del CSV {nombre_archivo} no coinciden o están vacías. Esperadas: {nombres_campos}, Encontradas: {lector.fieldnames}. Se intentará continuar.")

            for fila in lector:
                fila_procesada = {}
                for clave, valor in fila.items():
                    if clave not in nombres_campos:
                        continue
                    if clave == 'id' or clave == 'ano_lanzamiento':
                        fila_procesada[clave] = int(valor) if valor else None
                    elif clave == 'esta_eliminado':
                        fila_procesada[clave] = valor.strip().lower() == 'true'
                    elif clave == 'plataformas':
                        fila_procesada[clave] = [p.strip() for p in valor.split(',') if p.strip()] if valor else []
                    else:
                        fila_procesada[clave] = valor if valor else None

                for campo_esperado in nombres_campos:
                    if campo_esperado not in fila_procesada:
                         fila_procesada[campo_esperado] = None
                datos.append(fila_procesada)

    except FileNotFoundError:
        return []
    except Exception as e:
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
            escritor = csv.DictWriter(archivo_csv, fieldnames=nombres_campos, extrasaction='ignore')
            escritor.writeheader()
            for item in datos:
                fila_a_escribir = {}
                for campo in nombres_campos:
                    valor = item.get(campo)
                    if campo == 'plataformas' and isinstance(valor, list):
                        fila_a_escribir[campo] = ','.join(valor)
                    elif campo == 'esta_eliminado':
                        fila_a_escribir[campo] = str(bool(valor))

                    else:
                        fila_a_escribir[campo] = valor if valor is not None else ''

                escritor.writerow(fila_a_escribir)
    except IOError as e:
        print(f"Error al escribir en el archivo CSV {nombre_archivo}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo guardar los datos en {os.path.basename(nombre_archivo)}"
        ) from e

def cargar_juegos() -> List[Dict[str, Any]]:
    """Carga la lista de juegos desde juegos.csv."""
    return _cargar_datos_desde_csv(ARCHIVO_JUEGOS, CAMPOS_JUEGO)

def guardar_juegos(juegos: List[Dict[str, Any]]):
    """Guarda la lista de juegos en juegos.csv."""
    _guardar_datos_en_csv(ARCHIVO_JUEGOS, juegos, CAMPOS_JUEGO)