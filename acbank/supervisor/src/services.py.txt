import logging
import httpx
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from typing import TypedDict, Annotated, List
from operator import add 
from src.agents import clasificar_intencion_usuario

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Part, Role, TextPart

logger = logging.getLogger(__name__)

HTTPX_CLIENT = httpx.AsyncClient(timeout=30)

AGENTS = {
    "tarjeta_credito": "http://agente_tarjeta_credito:8000",
    "abrir_cuenta": "http://agente_abrir_cuenta:8000"
}

CLIENT_CACHE = {}

class State(TypedDict):
    query: str
    responses: Annotated[List[str],add]

async def request_agent(message: str, agent_url: str) -> str:
    if agent_url not in CLIENT_CACHE:
        logger.info(f"Descubriendo AgentCard en {agent_url}")
        resolver = A2ACardResolver(
            httpx_client= HTTPX_CLIENT,
            base_url= agent_url
        )
        agent_card = await resolver.get_agent_card()
        logger.info(f"Agente encontrado: {agent_card.name}")

        config = ClientConfig(
            httpx_client= HTTPX_CLIENT,
            streaming= False
        )

        factory = ClientFactory(config)

        CLIENT_CACHE[agent_url] = factory.create(agent_card)
    
    client = CLIENT_CACHE[agent_url]

    msg = Message(
        role= Role.user,
        message_id= str(uuid.uuid4()),
        parts= [Part(root=TextPart(text=message))]
    )

    logger.info(f"Enviando mensaje al agente: {message}")

    async for event in client.send_message(msg):
        if isinstance(event, Message):
            for part in event.parts:
                if part.root.kind == "text":
                    return part.root.text
    
    return "Sin respuesta del agente."


def nodo_de_enrutamiento(state: State):
    query = state.get("query","")
    classifications = clasificar_intencion_usuario(query)

    logger.info(f"Clasificación: {classifications}")

    return [
        Send(c["agent"], {"query": c["query"]})
        for c in classifications
    ]

async def nodo_tarjeta_credito(state: State):
    query = state.get("query","")
    logger.info(f"Ejecutando el agente TARJETA_CREDITO")

    respuesta = await request_agent(
        query,
        AGENTS["tarjeta_credito"]
    )

    return {"responses": [respuesta]}

async def nodo_abrir_cuenta(state: State):
    query = state.get("query","")
    logger.info(f"Ejecutando el agente ABRIR_CUENTA")

    respuesta = await request_agent(
        query,
        AGENTS["abrir_cuenta"]
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

    result = await graph.ainvoke(input_state)

    return "\n\n".join(result["responses"])
