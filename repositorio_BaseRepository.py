import csv
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, TypeVar, Generic
import logging

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    def __init__(self, csv_file: str):
        """
        Inicializa el repositorio base con el archivo CSV especificado.
        
        Args:
            csv_file (str): Nombre del archivo CSV (se guardará en directorio 'data')
        """
        self.csv_file = Path('data') / csv_file
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ensure_file_exists()
        
    def ensure_file_exists(self) -> None:
        """
        Verifica que el archivo CSV exista, si no, lo crea con los encabezados.
        """
        try:
            self.csv_file.parent.mkdir(exist_ok=True)
            if not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.get_fieldnames())
                    writer.writeheader()
                self.logger.info(f"Archivo {self.csv_file} creado exitosamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar archivo {self.csv_file}: {str(e)}")
            raise
    
    @abstractmethod
    def get_fieldnames(self) -> List[str]:
        """
        Devuelve los nombres de los campos para el CSV.
        
        Returns:
            List[str]: Lista de nombres de campos
        """
        pass
    
    @abstractmethod
    def row_to_model(self, row: Dict[str, str]) -> T:
        """
        Convierte una fila del CSV a un objeto del modelo.
        
        Args:
            row (Dict[str, str]): Fila del CSV como diccionario
            
        Returns:
            T: Instancia del modelo
        """
        pass
    
    @abstractmethod
    def model_to_row(self, model: T) -> Dict[str, str]:
        """
        Convierte un objeto del modelo a una fila de diccionario para el CSV.
        
        Args:
            model (T): Instancia del modelo
            
        Returns:
            Dict[str, str]: Diccionario representando la fila del CSV
        """
        pass
    
    def guardar(self, model: T) -> None:
        """
        Guarda un modelo en el CSV.
        
        Args:
            model (T): Instancia del modelo a guardar
        """
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.get_fieldnames())
                writer.writerow(self.model_to_row(model))
            self.logger.debug(f"Modelo guardado: {model}")
        except Exception as e:
            self.logger.error(f"Error al guardar modelo: {str(e)}")
            raise
    
    def obtener_todos(self, incluir_eliminados: bool = False) -> List[T]:
        """
        Obtiene todos los modelos del CSV.
        
        Args:
            incluir_eliminados (bool): Si incluir modelos marcados como eliminados
            
        Returns:
            List[T]: Lista de modelos
        """
        try:
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return [
                    self.row_to_model(row) 
                    for row in reader 
                    if incluir_eliminados or row.get('eliminado', 'False') == 'False'
                ]
        except FileNotFoundError:
            self.logger.warning(f"Archivo {self.csv_file} no encontrado, devolviendo lista vacía")
            return []
        except Exception as e:
            self.logger.error(f"Error al leer modelos: {str(e)}")
            raise
    
    def obtener_por_id(self, id: str) -> Optional[T]:
        """
        Obtiene un modelo por su ID.
        
        Args:
            id (str): ID del modelo a buscar
            
        Returns:
            Optional[T]: El modelo encontrado o None si no existe
        """
        try:
            modelos = self.obtener_todos(incluir_eliminados=True)
            for modelo in modelos:
                if str(modelo.id) == str(id):
                    return modelo
            return None
        except Exception as e:
            self.logger.error(f"Error al buscar modelo por ID {id}: {str(e)}")
            raise
    
    def actualizar(self, modelo_actualizado: T) -> bool:
        """
        Actualiza un modelo existente en el CSV.
        
        Args:
            modelo_actualizado (T): Modelo con los datos actualizados
            
        Returns:
            bool: True si se actualizó correctamente, False si no se encontró el modelo
        """
        try:
            modelos = self.obtener_todos(incluir_eliminados=True)
            encontrado = False
            
            for i, modelo in enumerate(modelos):
                if str(modelo.id) == str(modelo_actualizado.id):
                    modelos[i] = modelo_actualizado
                    encontrado = True
                    break
            
            if encontrado:
                self._sobrescribir_todos(modelos)
                self.logger.debug(f"Modelo {modelo_actualizado.id} actualizado")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error al actualizar modelo {modelo_actualizado.id}: {str(e)}")
            raise
    
    def eliminar(self, id: str) -> bool:
        """
        Marca un modelo como eliminado (soft delete).
        
        Args:
            id (str): ID del modelo a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no se encontró el modelo
        """
        try:
            modelo = self.obtener_por_id(id)
            if modelo:
                modelo.eliminado = True
                return self.actualizar(modelo)
            return False
        except Exception as e:
            self.logger.error(f"Error al eliminar modelo {id}: {str(e)}")
            raise
    
    def _sobrescribir_todos(self, modelos: List[T]) -> None:
        """
        Sobrescribe todos los modelos en el CSV.
        
        Args:
            modelos (List[T]): Lista de modelos a escribir
        """
        try:
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.get_fieldnames())
                writer.writeheader()
                for modelo in modelos:
                    writer.writerow(self.model_to_row(modelo))
        except Exception as e:
            self.logger.error(f"Error al sobrescribir modelos: {str(e)}")
            raise
    
    def contar(self, incluir_eliminados: bool = False) -> int:
        """
        Cuenta el número de modelos en el repositorio.
        
        Args:
            incluir_eliminados (bool): Si incluir modelos marcados como eliminados
            
        Returns:
            int: Número de modelos
        """
        return len(self.obtener_todos(incluir_eliminados))
    
    def existe_id(self, id: str) -> bool:
        """
        Verifica si existe un modelo con el ID especificado.
        
        Args:
            id (str): ID a verificar
            
        Returns:
            bool: True si existe, False si no
        """
        return self.obtener_por_id(id) is not None
    
    def obtener_ultimo_id(self) -> int:
        """
        Obtiene el último ID numérico utilizado en el repositorio.
        
        Returns:
            int: El último ID utilizado (0 si no hay modelos)
        """
        modelos = self.obtener_todos(incluir_eliminados=True)
        if not modelos:
            return 0
        return max(int(modelo.id) for modelo in modelos)