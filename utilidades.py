import time

# Una forma simple de generar IDs (en una app real usarías UUIDs o IDs de BD)
_ultimo_id = int(time.time() * 1000)

def obtener_siguiente_id() -> int:
    """Genera un ID numérico simple y secuencial."""
    global _ultimo_id
    _ultimo_id += 1
    return _ultimo_id

a