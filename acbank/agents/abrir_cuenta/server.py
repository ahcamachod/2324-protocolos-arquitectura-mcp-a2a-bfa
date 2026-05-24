from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from executor import EjecutorAbrirCuenta

# -----------------------
# SKILL Definition
# -----------------------
skill = AgentSkill(
    id="abrir_cuenta",
    name="Apertura de Cuenta ACBank",
    description="Ayuda a los clientes a abrir una cuenta bancaria y explica los tipos de cuenta disponibles.",
    tags=[
        "cuenta",
        "abrir cuenta",
        "abrir cuenta en el banco",
        "cuenta corriente",
        "cuenta de ahorros",
        "abrir cuenta digital",
        "registro bancario"
    ],
    examples=[
        "quiero abrir una cuenta",
        "como hago para abrir una cuenta?",
        "cuales tipos de cuenta me ofrecen?",
        "quiero crear una cuenta corriente",
        "puedo abrir una cuenta digital?"
    ],
)


# -----------------------
# Agent Card
# -----------------------
agent_card = AgentCard(
    name="Agente de Apertura de Cuenta ACBank",
    description="Especialista en apertura de cuentas bancarias do ACBank.",
    url="http://agente_abrir_cuenta:8000/",
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
    agent_executor=EjecutorAbrirCuenta(),
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
