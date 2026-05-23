import logging
import requests

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from typing import TypedDict, Annotated, List
from operator import add #Ejecuta más de una respuesta
from src.agents import clasificar_intencion_usuario

logger = logging.getLogger(__name__)

class State(TypedDict):
    query: str
    responses: Annotated[List[str],add]

def request_agent(message: str, agent: str) -> str:
    url = f"http://{agent}:8000/send"
    payload = {"message": message}

    try:
        logger.info(
            f"Enviando solicitud para {agent} en {url} con payload: {payload}"
        )

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()

        logger.info(f"Respuesta recibida de {agent}: {data}")

        return data.get("respuesta", "Respuesta no encontrada.")

    except Exception as e:
        logger.exception(f"Error al enviar la solicitud a {agent}")
        return f"Error al consultar {agent}: {str(e)}"

def nodo_de_enrutamiento(state: State):
    query = state.get("query","")
    classifications = clasificar_intencion_usuario(query)

    return [
        Send(c["agent"], {"query": c["query"]})
        for c in classifications
    ]

def nodo_tarjeta_credito(state: State):
    query = state.get("query","")
    logger.info(f"Ejecutando el agente TARJETA_CREDITO")

    respuesta = request_agent(
        query,
        "agente_tarjeta_credito"
    )

    return {"responses": [respuesta]}

def nodo_abrir_cuenta(state: State):
    query = state.get("query","")
    logger.info(f"Ejecutando el agente ABRIR_CUENTA")

    respuesta = request_agent(
        query,
        "agente_abrir_cuenta"
    )

    return {"responses": [respuesta]}

builder = StateGraph(State)
builder.add_node("tarjeta_credito", nodo_tarjeta_credito)
builder.add_node("abrir_cuenta", nodo_abrir_cuenta)
builder.add_conditional_edges(
    START,
    nodo_de_enrutamiento
)
builder.add_edge("tarjeta_credito", END)
builder.add_edge("abrir_cuenta", END)

graph = builder.compile()

async def ejecutar_supervisor(texto_usuario: str):
    input_state: State = {
        "query": texto_usuario,
        "responses":[]
    }

    result = graph.invoke(input_state)

    return "\n\n".join(result["responses"])