from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from executor import EjecutorTarjetaCredito

# -----------------------
# SKILL Definition
# -----------------------
skill = AgentSkill(
    id="tarjeta_credito",
    name="tarjetas de Crédito ACBank",
    description="Ayuda a los clientes con dudas, solicitudes y límites de tarjetas de crédito.",
    tags=["tarjeta", "credito", "limite",
          "platinum", "gold", "silver", "ac+"],
    examples=[
        "cuales tarjetas tienen?",
        "quiero solicitar una tarjeta platinum",
        "cual es el limite de mi tarjeta?",
        "puedo aumentar mi limite?",
        "quiero una tarjeta ac+"
    ],
)

# -----------------------
# Agent Card
# -----------------------
agent_card = AgentCard(
    name="Agente de tarjetas ACBank",
    description="Especialista en tarjetas de crédito de ACBank.",
    url="http://agente_tarjeta_credito:8000/",
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[skill],
    version="1.0.0",
    capabilities=AgentCapabilities(),
)
# -----------------------
# Request Handler
# -----------------------
handler = DefaultRequestHandler(
    agent_executor=EjecutorTarjetaCredito(),
    task_store=InMemoryTaskStore(),
)

# -----------------------
# A2A Application
# -----------------------
server = A2AStarletteApplication(
    http_handler=handler,
    agent_card=agent_card,
)

# EXPOSICIÓN DEL APP EN UVICORN
app = server.build()
