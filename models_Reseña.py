from datetime import datetime

class Reseña:
    def __init__(self, id, id_videojuego, id_usuario, calificacion, comentario, fecha=None, eliminado=False):
        self.id = id
        self.id_videojuego = id_videojuego
        self.id_usuario = id_usuario
        self.calificacion = calificacion  # 1-5
        self.comentario = comentario
        self.fecha = fecha if fecha else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.eliminado = eliminado

    def __str__(self):
        return f"Reseña {self.id}: {self.calificacion} estrellas para juego {self.id_videojuego}"