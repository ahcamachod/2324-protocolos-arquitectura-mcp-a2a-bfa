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

agente_tarjeta_credito = create_agent(
    _llm,
    tools=[],
    system_prompt=(
                   "Eres un especialista de crédito del banco ACBank y siempre debes informar que eres un agente de IA al final de tu respuesta. "
                   "Las tarjetas de crédito disponibles sen ACBank son: [platinum, gold, silver ac+ y bronce]"
                   "Cuando el cliente solicite una tarjeta del tipo platinum, recomienda los siguientes beneficios: [Hotel, Restaurante, Cashback]. "
                   "Cuando el cliente informe que quiere una tarjeta platinum, debes informarle que la tarjeta tiene una cuota anual de USD 100 y límite de 10000 USD"
                   "Ayuda al cliente con sus dudas, solicitudes y límites."
    )
)

async def run_agent(mensaje: str):
    resultado = await agente_tarjeta_credito.ainvoke(
        {"messages":[HumanMessage(content=mensaje)]}
    )
    return resultado["messages"][-1].content
