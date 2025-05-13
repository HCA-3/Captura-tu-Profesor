import csv
import os
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from modelos import ImagenBase

DIRECTORIO_DATOS = "datos"
ARCHIVO_JUEGOS = os.path.join(DIRECTORIO_DATOS, "juegos.csv")
ARCHIVO_CONSOLAS = os.path.join(DIRECTORIO_DATOS, "consolas.csv")
ARCHIVO_ACCESORIOS = os.path.join(DIRECTORIO_DATOS, "accesorios.csv")

os.makedirs(DIRECTORIO_DATOS, exist_ok=True)

CAMPOS_JUEGO = [
    'id', 'titulo', 'genero', 'plataformas',
    'ano_lanzamiento', 'nombre_desarrollador',
    'esta_eliminado', 'imagen_nombre', 'imagen_url'
]

CAMPOS_CONSOLA = [
    'id', 'nombre', 'fabricante', 'ano_lanzamiento', 
    'esta_eliminado', 'imagen_nombre', 'imagen_url'
]

CAMPOS_ACCESORIO = [
    'id', 'nombre', 'tipo', 'fabricante', 
    'id_consola', 'esta_eliminado', 'imagen_nombre', 'imagen_url'
]

def _procesar_imagen_csv(fila: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Procesa campos de imagen para el CSV."""
    imagen_data = {}
    if fila.get('imagen_nombre'):
        imagen_data = {
            'nombre_archivo': fila['imagen_nombre'],
            'url': fila.get('imagen_url', '')
        }
    return imagen_data if imagen_data else None

def _cargar_datos_desde_csv(nombre_archivo: str, nombres_campos: List[str]) -> List[Dict[str, Any]]:
    """Carga datos desde un archivo CSV."""
    if not os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
                escritor = csv.DictWriter(archivo_csv, fieldnames=nombres_campos)
                escritor.writeheader()
            return []
        except IOError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"No se pudo crear el archivo de datos: {os.path.basename(nombre_archivo)}"
            ) from e

    datos = []
    try:
        with open(nombre_archivo, mode='r', newline='', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            
            for fila in lector:
                fila_procesada = {}
                try:
                    for clave, valor in fila.items():
                        if clave not in nombres_campos:
                            continue

                        if clave in ['id', 'ano_lanzamiento', 'id_consola']:
                            fila_procesada[clave] = int(valor) if valor else None
                        elif clave == 'esta_eliminado':
                            fila_procesada[clave] = valor.lower() in ('true', '1', 't', 'y', 'yes')
                        elif clave == 'plataformas':
                            fila_procesada[clave] = [p.strip() for p in valor.split(',') if p.strip()] if valor else []
                        elif clave in ['imagen_nombre', 'imagen_url']:
                            continue
                        else:
                            fila_procesada[clave] = valor if valor else None

                    imagen_data = _procesar_imagen_csv(fila)
                    if imagen_data:
                        fila_procesada['imagen'] = imagen_data

                    datos.append(fila_procesada)
                except (ValueError, TypeError) as e:
                    continue

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer {os.path.basename(nombre_archivo)}: {str(e)}"
        )
    return datos

def _guardar_datos_en_csv(nombre_archivo: str, datos: List[Dict[str, Any]], nombres_campos: List[str]):
    """Guarda datos en un archivo CSV."""
    try:
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
            escritor = csv.DictWriter(archivo_csv, fieldnames=nombres_campos)
            escritor.writeheader()
            
            for item in datos:
                fila = {}
                for campo in nombres_campos:
                    if campo.startswith('imagen_'):
                        continue
                        
                    valor = item.get(campo)
                    
                    if campo == 'plataformas' and isinstance(valor, list):
                        fila[campo] = ','.join(valor)
                    elif campo == 'esta_eliminado':
                        fila[campo] = str(bool(valor)).lower()
                    else:
                        fila[campo] = str(valor) if valor is not None else ''

                if 'imagen' in item and item['imagen']:
                    fila['imagen_nombre'] = item['imagen'].get('nombre_archivo', '')
                    fila['imagen_url'] = item['imagen'].get('url', '')
                else:
                    fila['imagen_nombre'] = ''
                    fila['imagen_url'] = ''

                escritor.writerow(fila)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar en {os.path.basename(nombre_archivo)}: {str(e)}"
        )

# Funciones específicas para cada modelo
def cargar_juegos() -> List[Dict[str, Any]]:
    return _cargar_datos_desde_csv(ARCHIVO_JUEGOS, CAMPOS_JUEGO)

def guardar_juegos(juegos: List[Dict[str, Any]]):
    _guardar_datos_en_csv(ARCHIVO_JUEGOS, juegos, CAMPOS_JUEGO)

def cargar_consolas() -> List[Dict[str, Any]]:
    return _cargar_datos_desde_csv(ARCHIVO_CONSOLAS, CAMPOS_CONSOLA)

def guardar_consolas(consolas: List[Dict[str, Any]]):
    _guardar_datos_en_csv(ARCHIVO_CONSOLAS, consolas, CAMPOS_CONSOLA)

def cargar_accesorios() -> List[Dict[str, Any]]:
    return _cargar_datos_desde_csv(ARCHIVO_ACCESORIOS, CAMPOS_ACCESORIO)

def guardar_accesorios(accesorios: List[Dict[str, Any]]):
    _guardar_datos_en_csv(ARCHIVO_ACCESORIOS, accesorios, CAMPOS_ACCESORIO)