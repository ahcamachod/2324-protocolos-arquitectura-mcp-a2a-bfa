import logging
import httpx
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, Annotated
from operator import add

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Part, Role, TextPart

from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent
)
from pydantic import BaseModel

from src.agents import clasificar_intencion_usuario

logger = logging.getLogger(__name__)

# -----------------------------
# HTTP CLIENT GLOBAL
# -----------------------------
HTTPX_CLIENT = httpx.AsyncClient(timeout=30)

# -----------------------------
# REGISTRY DE AGENTES
# -----------------------------
AGENTS = {
    "tarjeta_credito": "http://agente_tarjeta_credito:8000",
    "abrir_cuenta": "http://agente_abrir_cuenta:8000"
}

# Cache de clientes A2A
CLIENT_CACHE = {}

# -----------------------------
# STATE DE LANGGRAPH
# -----------------------------


class State(TypedDict):
    query: str
    responses: Annotated[list[str], add]

# -----------------------------
# EVENTO PARA STATE UPDATE
# -----------------------------


class StateUpdateEvent(BaseModel):
    type: str = "STATE_UPDATE"
    state: dict

# -----------------------------
# LLAMADA PARA AGENTE A2A
# -----------------------------


async def request_agent(message: str, agent_url: str) -> str:

    if agent_url not in CLIENT_CACHE:
        logger.info(f"Descubriendo AgentCard en {agent_url}")

        resolver = A2ACardResolver(
            httpx_client=HTTPX_CLIENT,
            base_url=agent_url,
        )

        agent_card = await resolver.get_agent_card()
        logger.info(f"Agent encontrado: {agent_card.name}")

        config = ClientConfig(
            httpx_client=HTTPX_CLIENT,
            streaming=False
        )
        factory = ClientFactory(config)
        CLIENT_CACHE[agent_url] = factory.create(agent_card)

    client = CLIENT_CACHE[agent_url]

    msg = Message(
        role=Role.user,
        message_id=str(uuid.uuid4()),
        parts=[Part(root=TextPart(text=message))],
    )

    logger.info(f"Enviando mensaje para agente: {message}")

    async for event in client.send_message(msg):
        if isinstance(event, Message):
            for part in event.parts:
                if part.root.kind == "text":
                    return part.root.text

    return "Sin respuesta del agente."

# -----------------------------
# ROUTER
# -----------------------------


async def nodo_de_enrutamiento(state: State):
    query = state.get("query", "")
    classifications = await clasificar_intencion_usuario(query)
    logger.info(f"Classificação: {classifications}")
    return [Send(c["agent"], {"query": c["query"]}) for c in classifications]

# -----------------------------
# NODO TARJETA DE CRÉDITO
# -----------------------------


async def nodo_tarjeta_credito(state: State):
    query = state.get("query", "")
    logger.info("Ejecutando el agente tarjeta_credito")
    respuesta = await request_agent(query, AGENTS["tarjeta_credito"])
    return {"responses": [respuesta]}

# -----------------------------
# NODO ABRIR CUENTA
# -----------------------------


async def nodo_abrir_cuenta(state: State):
    query = state.get("query", "")
    logger.info("Ejecutando el agente abrir_cuenta")
    respuesta = await request_agent(query, AGENTS["abrir_cuenta"])
    return {"responses": [respuesta]}

# -----------------------------
# BUILD DEL GRAFO
# -----------------------------
builder = StateGraph(State)
builder.add_node("tarjeta_credito", nodo_tarjeta_credito)
builder.add_node("abrir_cuenta", nodo_abrir_cuenta)
builder.add_conditional_edges(START, nodo_de_enrutamiento)
builder.add_edge("tarjeta_credito", END)
builder.add_edge("abrir_cuenta", END)
graph = builder.compile()

# -----------------------------
# EJECUTOR DEL SUPERVISOR (NORMAL)
# -----------------------------

async def ejecutar_supervisor(texto_usuario: str):
    input_state: State = {"query": texto_usuario, "responses": []}
    result = await graph.ainvoke(input_state)
    return "\n\n".join(result["responses"])

# -----------------------------
# EJECUTOR DO SUPERVISOR (STREAMING COM STATE)
# -----------------------------


async def ejecutar_supervisor_stream(input_data):
    """
    Retorna eventos a AG-UI, incluyendo state compartido.
    """
    messages = input_data.messages
    if not messages:
        user_message = ""
    else:
        user_message = messages[-1].content

    assistant_id = str(uuid.uuid4())

    # Inicio del mensaje de assistant
    yield TextMessageStartEvent(
        type=EventType.TEXT_MESSAGE_START,
        message_id=assistant_id,
        role="assistant"
    )

    # Mensaje inicial
    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta="Analizando tu solicitud...\n\n"
    )

    # Estado inicial
    state = {"user_query": user_message, "responses": []}
    yield StateUpdateEvent(state=state)

    # Clasificación de agentes
    classifications = await clasificar_intencion_usuario(user_message)
    agentes = [c["agent"] for c in classifications]
    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Agentes seleccionados: {', '.join(agentes)}\n\n"
    )

    # Actualizar state
    state["agents"] = agentes
    yield StateUpdateEvent(state=state)

    respuestas = []
    for c in classifications:
        agent_name = c["agent"]

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"Llamando al agente: {agent_name}...\n"
        )

        respuesta = await request_agent(c["query"], AGENTS[agent_name])
        respuestas.append(respuesta)

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"{agent_name} respondió\n\n"
        )

        # Actualiza state tras cada agente
        state["responses"].append({agent_name: respuesta})
        yield StateUpdateEvent(state=state)

    respuesta_final = "\n\n".join(respuestas)

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Resultado final:\n\n{respuesta_final}"
    )

    # Fin del mensaje
    yield TextMessageEndEvent(
        type=EventType.TEXT_MESSAGE_END,
        message_id=assistant_id
    )
