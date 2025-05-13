# API en Render

## Despliegue
1. Conecta este repositorio a [Render](https://render.com).
2. Configura el **Build Command**: `pip install -r requirements.txt`.
3. Configura el **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`.
4. La URL estará disponible en: `https://[nombre-del-servicio].onrender.com`.

## Endpoints
- Documentación: `https://[nombre-del-servicio].onrender.com/docs`
- Lista de juegos: `GET /juegos/`