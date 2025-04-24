import csv
import os
from typing import List, Dict, Any
from fastapi import HTTPException, status
# Asegúrate de importar los nuevos modelos si los usas directamente aquí (aunque no es necesario para esta implementación)
# from modelos import Juego, Consola, Accesorio

DIRECTORIO_DATOS = "datos"
ARCHIVO_JUEGOS = os.path.join(DIRECTORIO_DATOS, "juegos.csv")
ARCHIVO_CONSOLAS = os.path.join(DIRECTORIO_DATOS, "consolas.csv")
ARCHIVO_ACCESORIOS = os.path.join(DIRECTORIO_DATOS, "accesorios.csv") # Nuevo archivo para accesorios

os.makedirs(DIRECTORIO_DATOS, exist_ok=True)

CAMPOS_JUEGO = [
    'id', 'titulo', 'genero', 'plataformas',
    'ano_lanzamiento', 'nombre_desarrollador',
    'esta_eliminado'
]
CAMPOS_CONSOLA = [
    'id', 'nombre', 'fabricante', 'ano_lanzamiento', 'esta_eliminado'
]
CAMPOS_ACCESORIO = [ # Nuevos campos para accesorios
    'id', 'nombre', 'tipo', 'fabricante', 'id_consola', 'esta_eliminado'
]

def _cargar_datos_desde_csv(nombre_archivo: str, nombres_campos: List[str]) -> List[Dict[str, Any]]:
    """Carga datos desde un archivo CSV."""
    if not os.path.exists(nombre_archivo):
        try:
            # Crear archivo con cabeceras si no existe
            with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
                escritor = csv.DictWriter(archivo_csv, fieldnames=nombres_campos)
                escritor.writeheader()
            print(f"Archivo {nombre_archivo} no encontrado. Se ha creado vacío con cabeceras.")
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
            # Validación básica de cabeceras
            if not lector.fieldnames or set(lector.fieldnames) != set(nombres_campos):
                 print(f"Advertencia: Las cabeceras del CSV {nombre_archivo} no coinciden o están vacías. Esperadas: {nombres_campos}, Encontradas: {lector.fieldnames}. Se intentará continuar.")
                 # Podrías decidir lanzar una excepción aquí si las cabeceras son cruciales

            for fila_idx, fila in enumerate(lector):
                fila_procesada = {}
                try:
                    for clave, valor in fila.items():
                        if clave not in nombres_campos:
                            # Ignorar columnas extra en el CSV si las hubiera
                            continue

                        # Conversión de tipos basada en el nombre del campo
                        if clave in ['id', 'ano_lanzamiento', 'id_consola']: # Añadido id_consola
                            fila_procesada[clave] = int(valor) if valor else None
                        elif clave == 'esta_eliminado':
                            # Manejo robusto de booleanos
                            fila_procesada[clave] = valor.strip().lower() in ('true', '1', 't', 'y', 'yes')
                        elif clave == 'plataformas':
                            # Manejo de listas separadas por comas
                            fila_procesada[clave] = [p.strip() for p in valor.split(',') if p.strip()] if valor else []
                        else:
                            # Campos de texto
                            fila_procesada[clave] = valor if valor else None

                    # Asegurar que todos los campos esperados estén presentes, aunque sea con None
                    for campo_esperado in nombres_campos:
                        if campo_esperado not in fila_procesada:
                            fila_procesada[campo_esperado] = None # O un valor por defecto adecuado

                    datos.append(fila_procesada)

                except (ValueError, TypeError) as e:
                     print(f"Error procesando fila {fila_idx + 1} en {nombre_archivo}: {e}. Fila: {fila}. Se omitirá esta fila.")
                except Exception as e: # Captura genérica para otros posibles errores en la fila
                     print(f"Error inesperado procesando fila {fila_idx + 1} en {nombre_archivo}: {e}. Fila: {fila}. Se omitirá esta fila.")


    except FileNotFoundError:
         # Esto no debería ocurrir si se crea el archivo al inicio, pero por si acaso.
        print(f"Archivo {nombre_archivo} no encontrado durante la lectura.")
        return []
    except Exception as e:
        print(f"Error crítico al leer el archivo CSV {nombre_archivo}: {e}")
        # Relanzar como HTTPException para que FastAPI lo maneje
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo cargar los datos desde {os.path.basename(nombre_archivo)} debido a un error interno."
        ) from e
    return datos

def _guardar_datos_en_csv(nombre_archivo: str, datos: List[Dict[str, Any]], nombres_campos: List[str]):
    """Guarda datos en un archivo CSV."""
    try:
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
            # Usar extrasaction='ignore' por si los dicts en memoria tienen más claves
            escritor = csv.DictWriter(archivo_csv, fieldnames=nombres_campos, extrasaction='ignore')
            escritor.writeheader()
            for item in datos:
                fila_a_escribir = {}
                for campo in nombres_campos:
                    valor = item.get(campo)
                    # Formateo específico para guardar en CSV
                    if campo == 'plataformas' and isinstance(valor, list):
                        fila_a_escribir[campo] = ','.join(map(str, valor)) # Asegurar que sean strings
                    elif campo == 'esta_eliminado':
                        # Guardar como True/False en minúsculas para consistencia
                        fila_a_escribir[campo] = str(bool(valor)).lower()
                    else:
                        # Guardar cadena vacía para None o valores falsy que no sean False booleano
                        fila_a_escribir[campo] = '' if valor is None else str(valor)

                escritor.writerow(fila_a_escribir)
    except IOError as e:
        print(f"Error al escribir en el archivo CSV {nombre_archivo}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo guardar los datos en {os.path.basename(nombre_archivo)}"
        ) from e
    except Exception as e: # Captura otros posibles errores (ej. de conversión de datos)
         print(f"Error inesperado al preparar o escribir datos en {nombre_archivo}: {e}")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al guardar datos en {os.path.basename(nombre_archivo)}"
        ) from e


# --- Funciones específicas por modelo ---

def cargar_juegos() -> List[Dict[str, Any]]:
    """Carga la lista de juegos desde juegos.csv."""
    return _cargar_datos_desde_csv(ARCHIVO_JUEGOS, CAMPOS_JUEGO)

def guardar_juegos(juegos: List[Dict[str, Any]]):
    """Guarda la lista de juegos en juegos.csv."""
    _guardar_datos_en_csv(ARCHIVO_JUEGOS, juegos, CAMPOS_JUEGO)

def cargar_consolas() -> List[Dict[str, Any]]:
    """Carga la lista de consolas desde consolas.csv."""
    return _cargar_datos_desde_csv(ARCHIVO_CONSOLAS, CAMPOS_CONSOLA)

def guardar_consolas(consolas: List[Dict[str, Any]]):
    """Guarda la lista de consolas en consolas.csv."""
    _guardar_datos_en_csv(ARCHIVO_CONSOLAS, consolas, CAMPOS_CONSOLA)

# Nuevas funciones para accesorios
def cargar_accesorios() -> List[Dict[str, Any]]:
    """Carga la lista de accesorios desde accesorios.csv."""
    return _cargar_datos_desde_csv(ARCHIVO_ACCESORIOS, CAMPOS_ACCESORIO)

def guardar_accesorios(accesorios: List[Dict[str, Any]]):
    """Guarda la lista de accesorios en accesorios.csv."""
    _guardar_datos_en_csv(ARCHIVO_ACCESORIOS, accesorios, CAMPOS_ACCESORIO)