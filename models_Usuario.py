class Usuario:
    def __init__(self, id, nombre, email, pais, fecha_registro=None, eliminado=False):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.pais = pais
        self.fecha_registro = fecha_registro if fecha_registro else datetime.now().strftime("%Y-%m-%d")
        self.eliminado = eliminado

    def __str__(self):
        return f"Usuario {self.id}: {self.nombre} ({self.email})"