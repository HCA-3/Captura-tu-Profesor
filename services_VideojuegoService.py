# services/VideojuegoService.py
from typing import List, Dict, Optional
from models.Videojuego import Videojuego
from repositories.VideojuegoRepository import VideojuegoRepository
from utils.Exceptions import (
    ElementoNoEncontradoError,
    ElementoDuplicadoError,
    DatosInvalidosError,
    OperacionNoPermitidaError
)
import logging
from datetime import datetime

class VideojuegoService:
    def __init__(self, repository: VideojuegoRepository):
        """
        Inicializa el servicio con el repositorio inyectado.
        
        Args:
            repository (VideojuegoRepository): Repositorio de videojuegos
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
        self.logger.info("Servicio de Videojuegos inicializado")

    def crear_videojuego(self, videojuego_data: Dict) -> Videojuego:
        """
        Crea un nuevo videojuego con los datos proporcionados.
        
        Args:
            videojuego_data (Dict): Datos del videojuego a crear
            
        Returns:
            Videojuego: El videojuego creado
            
        Raises:
            DatosInvalidosError: Si los datos no son válidos
            ElementoDuplicadoError: Si ya existe un videojuego con el mismo título
        """
        self.logger.debug(f"Intentando crear videojuego con datos: {videojuego_data}")
        
        # Validaciones básicas
        if not videojuego_data.get('titulo'):
            raise DatosInvalidosError("El título del videojuego es requerido")
        if not videojuego_data.get('desarrollador_id'):
            raise DatosInvalidosError("El ID del desarrollador es requerido")
        if not isinstance(videojuego_data.get('plataformas', []), list):
            raise DatosInvalidosError("Las plataformas deben ser una lista")
        
        # Validar título único
        existentes = self.repository.obtener_todos(incluir_eliminados=True)
        titulo = videojuego_data['titulo'].strip().lower()
        
        if any(v.titulo.lower() == titulo for v in existentes):
            raise ElementoDuplicadoError("Ya existe un videojuego con ese título")
        
        # Generar nuevo ID
        nuevo_id = str(self.repository.obtener_ultimo_id() + 1)
        
        # Crear instancia del videojuego
        videojuego = Videojuego(
            id=nuevo_id,
            titulo=videojuego_data['titulo'].strip(),
            desarrollador_id=videojuego_data['desarrollador_id'],
            año_lanzamiento=videojuego_data.get('año_lanzamiento', datetime.now().year),
            genero=videojuego_data.get('genero', 'Desconocido'),
            plataformas=videojuego_data.get('plataformas', []),
            precio=float(videojuego_data.get('precio', 0))
        )
        
        # Guardar en el repositorio
        self.repository.guardar(videojuego)
        self.logger.info(f"Videojuego creado con ID: {videojuego.id}")
        
        return videojuego

    def obtener_videojuego(self, id: str) -> Videojuego:
        """
        Obtiene un videojuego por su ID.
        
        Args:
            id (str): ID del videojuego
            
        Returns:
            Videojuego: El videojuego encontrado
            
        Raises:
            ElementoNoEncontradoError: Si no se encuentra el videojuego
        """
        self.logger.debug(f"Buscando videojuego con ID: {id}")
        videojuego = self.repository.obtener_por_id(id)
        
        if not videojuego or videojuego.eliminado:
            raise ElementoNoEncontradoError(f"Videojuego con ID {id} no encontrado")
            
        return videojuego

    def listar_videojuegos(self, incluir_eliminados: bool = False) -> List[Videojuego]:
        """
        Lista todos los videojuegos.
        
        Args:
            incluir_eliminados (bool): Si incluir videojuegos marcados como eliminados
            
        Returns:
            List[Videojuego]: Lista de videojuegos
        """
        self.logger.debug("Listando todos los videojuegos")
        return self.repository.obtener_todos(incluir_eliminados)

    def actualizar_videojuego(self, id: str, datos_actualizados: Dict) -> Videojuego:
        """
        Actualiza un videojuego existente.
        
        Args:
            id (str): ID del videojuego a actualizar
            datos_actualizados (Dict): Datos a actualizar
            
        Returns:
            Videojuego: El videojuego actualizado
            
        Raises:
            ElementoNoEncontradoError: Si no se encuentra el videojuego
            DatosInvalidosError: Si los datos no son válidos
        """
        self.logger.debug(f"Actualizando videojuego ID {id} con datos: {datos_actualizados}")
        
        # Obtener videojuego existente
        videojuego = self.obtener_videojuego(id)
        
        # Validar título único si se está actualizando
        if 'titulo' in datos_actualizados:
            nuevo_titulo = datos_actualizados['titulo'].strip().lower()
            existentes = self.repository.obtener_todos(incluir_eliminados=True)
            
            if any(v.id != id and v.titulo.lower() == nuevo_titulo for v in existentes):
                raise ElementoDuplicadoError("Ya existe otro videojuego con ese título")
        
        # Actualizar campos permitidos
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
        
        # Guardar cambios
        if not self.repository.actualizar(videojuego):
            raise ElementoNoEncontradoError(f"Videojuego con ID {id} no pudo ser actualizado")
            
        self.logger.info(f"Videojuego ID {id} actualizado exitosamente")
        return videojuego

    def eliminar_videojuego(self, id: str) -> bool:
        """
        Elimina un videojuego (soft delete).
        
        Args:
            id (str): ID del videojuego a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no
            
        Raises:
            ElementoNoEncontradoError: Si no se encuentra el videojuego
        """
        self.logger.debug(f"Eliminando videojuego con ID: {id}")
        videojuego = self.obtener_videojuego(id)
        
        if videojuego.eliminado:
            raise OperacionNoPermitidaError("El videojuego ya está eliminado")
        
        resultado = self.repository.eliminar(id)
        if resultado:
            self.logger.info(f"Videojuego ID {id} marcado como eliminado")
        else:
            self.logger.warning(f"No se pudo eliminar videojuego ID {id}")
            
        return resultado

    def filtrar_videojuegos(self, genero: str = None, plataforma: str = None, 
                           min_precio: float = None, max_precio: float = None) -> List[Videojuego]:
        """
        Filtra videojuegos según los criterios proporcionados.
        
        Args:
            genero (str, optional): Género para filtrar
            plataforma (str, optional): Plataforma para filtrar
            min_precio (float, optional): Precio mínimo
            max_precio (float, optional): Precio máximo
            
        Returns:
            List[Videojuego]: Lista de videojuegos que cumplen los criterios
        """
        self.logger.debug(f"Filtrando videojuegos - género: {genero}, plataforma: {plataforma}, "
                        f"precio: {min_precio}-{max_precio}")
        
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
                
        self.logger.debug(f"Encontrados {len(filtrados)} videojuegos que cumplen los criterios")
        return filtrados

    def buscar_por_titulo(self, titulo: str, exacto: bool = False) -> List[Videojuego]:
        """
        Busca videojuegos por título.
        
        Args:
            titulo (str): Título o parte del título a buscar
            exacto (bool): Si la búsqueda debe ser exacta (case insensitive)
            
        Returns:
            List[Videojuego]: Lista de videojuegos que coinciden
        """
        self.logger.debug(f"Buscando videojuegos por título: '{titulo}' (exacto: {exacto})")
        
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
                    
        self.logger.debug(f"Encontrados {len(resultados)} coincidencias")
        return resultados

    def contar_videojuegos_por_genero(self) -> Dict[str, int]:
        """
        Cuenta cuántos videojuegos hay por cada género.
        
        Returns:
            Dict[str, int]: Diccionario con géneros como keys y conteos como valores
        """
        self.logger.debug("Contando videojuegos por género")
        
        videojuegos = self.listar_videojuegos()
        conteo = {}
        
        for v in videojuegos:
            genero = v.genero.strip().title()
            conteo[genero] = conteo.get(genero, 0) + 1
            
        self.logger.debug(f"Conteo por género: {conteo}")
        return conteo

    def obtener_precio_promedio(self) -> float:
        """
        Calcula el precio promedio de todos los videojuegos.
        
        Returns:
            float: Precio promedio
        """
        self.logger.debug("Calculando precio promedio de videojuegos")
        
        videojuegos = self.listar_videojuegos()
        if not videojuegos:
            return 0.0
            
        total = sum(v.precio for v in videojuegos)
        promedio = total / len(videojuegos)
        
        self.logger.debug(f"Precio promedio calculado: {promedio:.2f}")
        return round(promedio, 2)