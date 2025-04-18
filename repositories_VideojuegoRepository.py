from repositories.BaseRepository import BaseRepository
from models.Videojuego import Videojuego

class VideojuegoRepository(BaseRepository):
    def get_fieldnames(self):
        return ['id', 'titulo', 'desarrollador_id', 'año_lanzamiento', 
                'genero', 'plataformas', 'precio', 'eliminado']
    
    def row_to_model(self, row):
        return Videojuego(
            id=row['id'],
            titulo=row['titulo'],
            desarrollador_id=row['desarrollador_id'],
            año_lanzamiento=row['año_lanzamiento'],
            genero=row['genero'],
            plataformas=row['plataformas'].split('|'),
            precio=float(row['precio']),
            eliminado=row['eliminado'] == 'True'
        )
    
    def model_to_row(self, model):
        return {
            'id': model.id,
            'titulo': model.titulo,
            'desarrollador_id': model.desarrollador_id,
            'año_lanzamiento': model.año_lanzamiento,
            'genero': model.genero,
            'plataformas': '|'.join(model.plataformas),
            'precio': str(model.precio),
            'eliminado': str(model.eliminado)
        }