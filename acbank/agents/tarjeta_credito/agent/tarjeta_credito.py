from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver
import os

load_dotenv()

_llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.2,
)

client = MultiServerMCPClient(
    {
        "cuenta": {
            "transport": "http",
            "url": "http://recursos:8000/mcp_gateway",
        }  # type: ignore
    }
)

memory = InMemorySaver()

agent = None

async def build_tarjeta_agent():
    tools = await client.get_tools()

    agente_tarjetas = create_agent(
        _llm,
        tools=tools,
        system_prompt=(
            "Eres especialista en tarjetas de ACBank.\n\n"

            "Tipos disponibles: platinum, gold, silver, ac+\n\n"

            "=============================\n"
            "REGLAS OBLIGATORIAS (CRÍTICO)\n"
            "=============================\n"
            "1. TIENES QUE obligatoriamente llamar la tool consultar_cuenta\n"
            "2. NO puedes responder sin verificar en el sistema\n"
            "3. NO puedes asumir si el cliente tiene cuenta\n\n"

            "=============================\n"
            "FLUJO\n"
            "=============================\n"

            "PASO 1:\n"
            "→ Identificar el DNI (usar la memoria si ya lo hay)\n"
            "→ Si no hay DNI, solicitarlo al cliente\n\n"

            "PASO 2:\n"
            "→ Llamar consultar_cuenta\n\n"

            "PASO 3:\n"
            "→ Si existe = False:\n"
            "   - Informar que no tiene cuenta\n"
            "   - Ofrecer abrir cuenta\n"
            "   - NO solicitar tarjeta\n\n"

            "→ Si existe = True:\n"
            "   - Llamar solicitar_tarjeta\n\n"

            "=============================\n"
            "REGLAS GENERALES\n"
            "=============================\n"
            "- Siempre usa tools\n"
            "- Nunca inventes datos\n"
            "- Usa la memoria para recuperar el DNI\n"
            "- Nunca saltes etapas\n\n"

            "=============================\n"
            "ERRORES\n"
            "=============================\n"
            "- Usa el mensaje de tool\n"
            "- Explica claramente\n"
        ),
        checkpointer=memory,
    )

    return agente_tarjetas


async def run_agent(mensaje: str, thread_id: str = "1"):
    global agent
    if not agent:
        agent = await build_tarjeta_agent() #Verifica que el agente ya esté siendo ejecutado en memoria
    resultado = await agent.ainvoke(
        {
            "messages": [
                HumanMessage(content=mensaje)
            ]
        },
        {
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return resultado["messages"][-1].content
