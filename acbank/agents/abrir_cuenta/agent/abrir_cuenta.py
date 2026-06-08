from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver
import os

load_dotenv()

_llm = init_chat_model(
    model="gpt-4o", 
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=0.3
)

client = MultiServerMCPClient(
    {
        "cuenta": {
            "transport": "http",
            "url": "http://recursos:8000/mcp_gateway",
        }
    }
)

memory = InMemorySaver()

async def build_agent():
    tools = await client.get_tools()

    agent = create_agent(
        _llm,
        tools=tools,
        system_prompt=(
            "Eres un asistente del ACBank para apertura de cuentas.\n\n"

            "SIEMPRE debes usar tools para decisiones reales.\n\n"

            "Flujo obligatorio:\n"
            "1. Si el cliente pide tarjeta:\n"
            "   - Usa consultar_cuenta\n"
            "   - Si no existe:\n"
            "       → informa el problema\n"
            "       → ofrece abrir cuenta\n\n"

            "2. Para abrir cuenta:\n"
            "   - Usa generar_prompt_apertura\n"
            "   - Despues crear_o_buscar_cuenta\n\n"

            "3. Después de crear cuenta:\n"
            "   - Usa solicitar_tarjeta\n\n"

            "Reglas:\n"
            "- Nunca inventes datos\n"
            "- Siempre usa tools\n"
            "- Usa mensajes claros para el cliente\n"              
        ),
        checkpointer=memory,
    )

    return agent

async def run_agent(mensaje: str, thread_id: str = "1"): # La identificación de la sesión
    agent = await build_agent()
    resultado = await agent.ainvoke(
        {"messages": [HumanMessage(content=mensaje)]},
        {"configurable": {"thread_id": thread_id}}
    )
    return resultado["messages"][-1].content
