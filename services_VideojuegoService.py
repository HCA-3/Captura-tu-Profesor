from typing import List, Dict, Optional
from ..models.Videojuego import Videojuego
from ..repositories.VideojuegoRepository import VideojuegoRepository
from ..utils.Exceptions import (
    ElementoNoEncontradoError,
    ElementoDuplicadoError,
    DatosInvalidosError,
    OperacionNoPermitidaError
)
from datetime import datetime

class VideojuegoService:
    def __init__(self, repository: VideojuegoRepository):
        self.repository = repository

    def crear_videojuego(self, videojuego_data: Dict) -> Videojuego:
        if not videojuego_data.get('titulo'):
            raise DatosInvalidosError("El título del videojuego es requerido")
        if not videojuego_data.get('desarrollador_id'):
            raise DatosInvalidosError("El ID del desarrollador es requerido")
        if not isinstance(videojuego_data.get('plataformas', []), list):
            raise DatosInvalidosError("Las plataformas deben ser una lista")

        existentes = self.repository.obtener_todos(incluir_eliminados=True)
        titulo = videojuego_data['titulo'].strip().lower()
        
        if any(v.titulo.lower() == titulo for v in existentes):
            raise ElementoDuplicadoError("Ya existe un videojuego con ese título")

        nuevo_id = str(self.repository.obtener_ultimo_id() + 1)
        
        videojuego = Videojuego(
            id=nuevo_id,
            titulo=videojuego_data['titulo'].strip(),
            desarrollador_id=videojuego_data['desarrollador_id'],
            año_lanzamiento=videojuego_data.get('año_lanzamiento', datetime.now().year),
            genero=videojuego_data.get('genero', 'Desconocido'),
            plataformas=videojuego_data.get('plataformas', []),
            precio=float(videojuego_data.get('precio', 0))
        
        self.repository.guardar(videojuego)
        return videojuego

    def obtener_videojuego(self, id: str) -> Videojuego:
        videojuego = self.repository.obtener_por_id(id)
        if not videojuego or videojuego.eliminado:
            raise ElementoNoEncontradoError(f"Videojuego con ID {id} no encontrado")
        return videojuego

    def listar_videojuegos(self, incluir_eliminados: bool = False) -> List[Videojuego]:
        return self.repository.obtener_todos(incluir_eliminados)

    def actualizar_videojuego(self, id: str, datos_actualizados: Dict) -> Videojuego:
        videojuego = self.obtener_videojuego(id)
        
        if 'titulo' in datos_actualizados:
            nuevo_titulo = datos_actualizados['titulo'].strip().lower()
            existentes = self.repository.obtener_todos(incluir_eliminados=True)
            
            if any(v.id != id and v.titulo.lower() == nuevo_titulo for v in existentes):
                raise ElementoDuplicadoError("Ya existe otro videojuego con ese título")

        campos_permitidos = {'titulo', 'año_lanzamiento', 'genero', 'plataformas', 'precio'}
        for campo, valor in datos_actualizados.items():
            if campo in campos_permitidos:
                if campo == 'plataformas' and not isinstance(valor, list):
                    raise DatosInvalidosError("Las plataformas deben ser una lista")
                if campo == 'precio':
                    try:
                        valor = float(valor)
                    except ValueError:
                        raise DatosInvalidosError("El precio debe ser un número válido")
                
                setattr(videojuego, campo, valor)
        
        if not self.repository.actualizar(videojuego):
            raise ElementoNoEncontradoError(f"Videojuego con ID {id} no pudo ser actualizado")
            
        return videojuego

    def eliminar_videojuego(self, id: str) -> bool:
        videojuego = self.obtener_videojuego(id)
        
        if videojuego.eliminado:
            raise OperacionNoPermitidaError("El videojuego ya está eliminado")
        
        return self.repository.eliminar(id)

    def filtrar_videojuegos(self, genero: str = None, plataforma: str = None,
                           min_precio: float = None, max_precio: float = None) -> List[Videojuego]:
        videojuegos = self.listar_videojuegos()
        filtrados = []
        
        for v in videojuegos:
            cumple_criterios = True
            
            if genero and v.genero.lower() != genero.lower():
                cumple_criterios = False
                
            if plataforma and plataforma.lower() not in [p.lower() for p in v.plataformas]:
                cumple_criterios = False
                
            if min_precio is not None and v.precio < min_precio:
                cumple_criterios = False
                
            if max_precio is not None and v.precio > max_precio:
                cumple_criterios = False
                
            if cumple_criterios:
                filtrados.append(v)
                
        return filtrados

    def buscar_por_titulo(self, titulo: str, exacto: bool = False) -> List[Videojuego]:
        videojuegos = self.listar_videojuegos()
        titulo = titulo.strip().lower()
        resultados = []
        
        for v in videojuegos:
            if exacto:
                if v.titulo.lower() == titulo:
                    resultados.append(v)
            else:
                if titulo in v.titulo.lower():
                    resultados.append(v)
                    
        return resultados

    def contar_videojuegos_por_genero(self) -> Dict[str, int]:
        videojuegos = self.listar_videojuegos()
        conteo = {}
        
        for v in videojuegos:
            genero = v.genero.strip().title()
            conteo[genero] = conteo.get(genero, 0) + 1
            
        return conteo

    def obtener_precio_promedio(self) -> float:
        videojuegos = self.listar_videojuegos()
        if not videojuegos:
            return 0.0
            
        total = sum(v.precio for v in videojuegos)
        return round(total / len(videojuegos), 2)