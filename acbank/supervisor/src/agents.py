import logging
import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

load_dotenv()

_llm = init_chat_model(
    model="gpt-4o", # No vamos a profundizar en el modelo que vamos a usar en este momento porque no tenemos un evaluator
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=0
)

class RouterOutput(BaseModel):
    agents: List[str] = Field(
        description="Lista de agentes que deben responder a la solicitud"
    )

parser = JsonOutputParser(pydantic_object=RouterOutput)

def clasificar_intencion_usuario(query: str) -> List[dict]:
    """
    Clasifique la pregunta y retorne cuáles agentes deben ser llamados.
    """

    prompt = f"""
    Eres el enrutador de agentes de un banco.

    Agentes disponibles:

    abrir_cuenta
    tarjeta_credito

    Una pregunta puede requerir más de un agente.

    Únicamente responde en formato JSON.

    Pregunta:
    {query} 

    {parser.get_format_instructions()}    
    """
    respuesta = _llm.invoke(prompt)
    resultado = parser.parse(str(respuesta.content))
    agentes = resultado["agents"]

    logger.info(f"Agentes seleccionados: {agentes}")

    return [
        {
            "query": query,
            "agent":agente
        }
        for agente in agentes
    ]