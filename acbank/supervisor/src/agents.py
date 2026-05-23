from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os

load_dotenv()

_llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7
)

agente_tarjeta_credito = create_agent(
    _llm,
    tools=[],
    system_prompt=("Eres un especialista de crédito del banco ACBank. "
                   "Ayuda al cliente con sus dudas, solicitudes y límites."

    )
)

agente_abrir_cuenta = create_agent(
    _llm,
    tools=[],
    system_prompt=("Eres un especialista en apertura de cuentas del banco ACBank. "
                   "Ayuda al cliente a abrir una cuenta y explica los tipos disponibles de cuenta "
                   "que son cuenta de ahorros y cuenta corriente."
    )
)

def clasificar_pregunta(pregunta:str) -> str:
    prompt= f"""
    Clasifica la intención del usuario.

    Posibles agentes:
    tarjeta_credito
    abrir_cuenta

    pregunta: {pregunta}

    Responde únicamente con el nombre del agente.   
    """
    respuesta = _llm.invoke(prompt)
    return str(respuesta.content).strip()

async def ejecutar_supervisor(texto_usuario:str) -> str:
    agente = clasificar_pregunta(texto_usuario)
    if agente == "tarjeta_credito":
        resultado = agente_tarjeta_credito.invoke(
            {"messages":[HumanMessage(content=texto_usuario)]}
        )
    elif agente == "abrir_cuenta":
        resultado = agente_abrir_cuenta.invoke(
            {"messages":[HumanMessage(content=texto_usuario)]}
        )
    else:
        resultado = "No logré entender su solicitud."

    mensaje_ia = resultado["messages"][-1]

    return mensaje_ia.content