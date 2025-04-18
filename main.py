# main.py
from fastapi import FastAPI, HTTPException
from services.VideojuegoService import VideojuegoService
from services.DesarrolladorService import DesarrolladorService
from services.UsuarioService import UsuarioService
from services.ReseñaService import ReseñaService
from repositories.VideojuegoRepository import VideojuegoRepository
from repositories.DesarrolladorRepository import DesarrolladorRepository
from repositories.UsuarioRepository import UsuarioRepository
from repositories.ReseñaRepository import ReseñaRepository
from utils.Exceptions import ElementoNoEncontradoError, ElementoDuplicadoError
import uvicorn
import logging

# Configuración inicial
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API de Videojuegos",
    description="Sistema completo de gestión de videojuegos con 4 modelos de datos",
    version="1.0.0"
)

# Inicialización de repositorios y servicios
repositorios = {
    'videojuegos': VideojuegoRepository('videojuegos.csv'),
    'desarrolladores': DesarrolladorRepository('desarrolladores.csv'),
    'usuarios': UsuarioRepository('usuarios.csv'),
    'reseñas': ReseñaRepository('reseñas.csv')
}

servicios = {
    'videojuegos': VideojuegoService(repositorios['videojuegos']),
    'desarrolladores': DesarrolladorService(repositorios['desarrolladores']),
    'usuarios': UsuarioService(repositorios['usuarios']),
    'reseñas': ReseñaService(repositorios['reseñas'])
}

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando API de Videojuegos")
    logger.info("Archivos CSV utilizados:")
    for nombre, repo in repositorios.items():
        logger.info(f"- {nombre}: {repo.csv_file}")

# Endpoints para Videojuegos
@app.post("/videojuegos/", response_model=dict)
def crear_videojuego(videojuego_data: dict):
    try:
        videojuego = servicios['videojuegos'].crear_videojuego(videojuego_data)
        return {
            "mensaje": "Videojuego creado exitosamente",
            "data": videojuego.__dict__
        }
    except (ElementoDuplicadoError, DatosInvalidosError) as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    print("\nSistema de Gestión de Videojuegos")
    print("Archivos CSV principales:")
    print("- videojuegos.csv: Almacena los videojuegos")
    print("- desarrolladores.csv: Almacena los desarrolladores")
    print("- usuarios.csv: Almacena los usuarios registrados")
    print("- reseñas.csv: Almacena las reseñas de los juegos\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)