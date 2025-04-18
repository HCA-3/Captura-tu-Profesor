class Desarrollador:
    def __init__(self, id, nombre, pais, año_fundacion, sitio_web, especialidad, eliminado=False):
        self.id = id
        self.nombre = nombre
        self.pais = pais
        self.año_fundacion = año_fundacion
        self.sitio_web = sitio_web
        self.especialidad = especialidad
        self.eliminado = eliminado

    def __str__(self):
        return f"Desarrollador {self.id}: {self.nombre} ({self.pais})"