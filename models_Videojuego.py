class Videojuego:
    def __init__(self, id, titulo, desarrollador_id, año_lanzamiento, genero, plataformas, precio, eliminado=False):
        self.id = id
        self.titulo = titulo
        self.desarrollador_id = desarrollador_id
        self.año_lanzamiento = año_lanzamiento
        self.genero = genero
        self.plataformas = plataformas
        self.precio = precio
        self.eliminado = eliminado

    def __str__(self):
        return f"Videojuego {self.id}: {self.titulo} ({self.año_lanzamiento})"