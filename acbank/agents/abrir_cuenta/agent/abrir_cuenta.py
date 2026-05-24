from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model
import os

load_dotenv()

_llm = init_chat_model(
    model="gpt-4o", 
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=0.7
)

agente_abrir_cuenta = create_agent(
    _llm,
    tools=[],
    system_prompt=(
        "Eres un especialista en apertura de cuentas del banco ACBank. "
        "Ayuda al cliente a abrir una cuenta y explica los tipos disponibles."
    )
)

async def run_agent(mensaje: str):
    resultado = await agente_abrir_cuenta.ainvoke(
        {"messages":[HumanMessage(content=mensaje)]}
    )
    return resultado["messages"][-1].content
