import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.schemas import ChatRequest
from src.agents import ejecutar_supervisor


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    if not payload.message:
        return JSONResponse(status_code=400, content={"error": "El campo 'mensaje' es obligatorio"})
    try:
        logger.info(f"Mensaje recibido en /chat: {payload.message}")
        respuesta = await ejecutar_supervisor(texto_usuario=payload.message)
        logger.info(f"Respuesta generada: {respuesta}")
        return {"respuesta": respuesta}
    except Exception as e:
        logger.exception("Error al procesar la solicitud en el endpoint /chat")
        return JSONResponse(status_code=500, content={"error": str(e)})