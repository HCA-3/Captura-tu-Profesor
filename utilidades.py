import time

_ultimo_id = int(time.time() * 1000)

def obtener_siguiente_id() -> int:
    """Genera un ID numérico simple y secuencial."""
    global _ultimo_id
    _ultimo_id += 1
    return _ultimo_id
