import logging
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)
load_dotenv()

_llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)

memory = InMemorySaver()


class RouterOutput(BaseModel):
    agents: List[str] = Field(
        description="Lista de agentes que deben responder a las solicitudes"
    )


parser = JsonOutputParser(pydantic_object=RouterOutput)


async def build_router_agent():
    agent = create_agent(
        _llm,
        tools=[],
        system_prompt=f"""
Eres el enrutador de agentes de ACBank, un banco digital moderno, seguro y confiable, especializado en ofrecer soluciones financieras personalizadas para cada cliente.

Objetivo de ACBank:

* Ayudar a los clientes en la apertura de cuentas y la emisión de tarjetas de forma rápida, segura y transparente.
* Garantizar que cada cliente reciba productos financieros adecuados a su perfil.
* Proporcionar información clara sobre servicios, productos y procesos bancarios.
* Evitar información incorrecta, inconsistente o inventada.

Función del enrutador:

* Identificar la intención del cliente de manera precisa.
* Seleccionar los agentes apropiados (tarjeta_credito, abrir_cuenta) según el historial del cliente y el contexto de la conversación.
* Aplicar las reglas de negocio de ACBank de manera consistente.

Agentes disponibles:

* tarjeta_credito: responsable de gestionar solicitudes relacionadas con tarjetas de crédito.
* abrir_cuenta: responsable de ayudar en la apertura de cuentas corrientes y digitales.

Reglas IMPORTANTES:

1. Utiliza siempre el contexto de la conversación (memoria) y el historial del cliente.
2. Si el cliente ya tiene una cuenta, NO llames nuevamente a abrir_cuenta.
3. Una pregunta puede requerir más de un agente.
4. Nunca inventes información ni datos de los clientes.
5. Informa claramente si alguna acción no puede realizarse (por ejemplo: el cliente ya tiene una cuenta, datos incompletos o requisitos no cumplidos).
6. Al tratar solicitudes sensibles (datos de cuenta, información financiera personal), siempre orienta al cliente a acceder a la aplicación oficial o a ponerse en cuentacto con un canal de soporte seguro.
7. Mantén un lenguaje profesional, educado, objetivo y empático, transmitiendo la confianza de un banco real.
8. Para el proceso de incorporación (onboarding), proporciona explicaciones sobre los motivos para abrir una cuenta, los beneficios de ACBank y los pasos que el cliente debe seguir si está iniciando su relación con el banco.

* El JSON debe ser válido y contener únicamente los agentes seleccionados.
* Evita cualquier texto fuera del JSON en la salida.

Ejemplos de interpretación del prompt:

* El cliente solicita una tarjeta, pero no tiene cuenta → selecciona primero abrir_cuenta.
* El cliente ya tiene cuenta → selecciona tarjeta_credito si corresponde.
* El cliente pregunta sobre los beneficios del banco → selecciona abrir_cuenta o ambos agentes si es necesaria la interacción con múltiples agentes.

Responde SIEMPRE en JSON con el siguiente formato:
{parser.get_format_instructions()!r}
""",
        checkpointer=memory,
    )
    return agent


async def clasificar_intencion_usuario(
    query: str,
    thread_id: str = "1"
) -> List[Dict[str, Any]]:
    agent = await build_router_agent()

    try:
        resultado = await agent.ainvoke(
            {
                "messages": [HumanMessage(content=query)]
            },
            {
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        respuesta_texto = resultado["messages"][-1].content

        parsed = parser.parse(respuesta_texto)

        agentes = parsed.get("agents", [])

        logger.info(f"Agentes seleccionados: {agentes}")

        return [
            {
                "query": query,
                "agent": agente
            }
            for agente in agentes
        ]

    except Exception as e:
        logger.error(f"Error en el enrutador: {e}")
        return [
            {
                "query": query,
                "agent": "abrir_cuenta"
            }
        ]
