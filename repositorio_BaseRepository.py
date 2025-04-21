import csv
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, TypeVar, Generic

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    def __init__(self, csv_file: str):
        self.csv_file = Path('data') / csv_file
        self.ensure_file_exists()

    def ensure_file_exists(self) -> None:
        self.csv_file.parent.mkdir(exist_ok=True)
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.get_fieldnames())
                writer.writeheader()

    @abstractmethod
    def get_fieldnames(self) -> List[str]:
        pass

    @abstractmethod
    def row_to_model(self, row: Dict[str, str]) -> T:
        pass

    @abstractmethod
    def model_to_row(self, model: T) -> Dict[str, str]:
        pass

    def guardar(self, model: T) -> None:
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.get_fieldnames())
            writer.writerow(self.model_to_row(model))

    def obtener_todos(self, incluir_eliminados: bool = False) -> List[T]:
        try:
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return [
                    self.row_to_model(row)
                    for row in reader
                    if incluir_eliminados or row.get('eliminado', 'False') == 'False'
                ]
        except FileNotFoundError:
            return []

    def obtener_por_id(self, id: str) -> Optional[T]:
        modelos = self.obtener_todos(incluir_eliminados=True)
        for modelo in modelos:
            if str(modelo.id) == str(id):
                return modelo
        return None

    def actualizar(self, modelo_actualizado: T) -> bool:
        modelos = self.obtener_todos(incluir_eliminados=True)
        encontrado = False
        
        for i, modelo in enumerate(modelos):
            if str(modelo.id) == str(modelo_actualizado.id):
                modelos[i] = modelo_actualizado
                encontrado = True
                break
        
        if encontrado:
            self._sobrescribir_todos(modelos)
            return True
        return False

    def eliminar(self, id: str) -> bool:
        modelo = self.obtener_por_id(id)
        if modelo:
            modelo.eliminado = True
            return self.actualizar(modelo)
        return False

    def _sobrescribir_todos(self, modelos: List[T]) -> None:
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.get_fieldnames())
            writer.writeheader()
            for modelo in modelos:
                writer.writerow(self.model_to_row(modelo))

    def contar(self, incluir_eliminados: bool = False) -> int:
        return len(self.obtener_todos(incluir_eliminados))

    def existe_id(self, id: str) -> bool:
        return self.obtener_por_id(id) is not None

    def obtener_ultimo_id(self) -> int:
        modelos = self.obtener_todos(incluir_eliminados=True)
        if not modelos:
            return 0
        return max(int(modelo.id) for modelo in modelos)