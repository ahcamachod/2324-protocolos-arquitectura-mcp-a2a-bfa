import logging
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from agent.abrir_cuenta import run_agent

logger = logging.getLogger("a2a.abrir_cuenta.ejecutor")


class EjecutorAbrirCuenta(AgentExecutor):

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        logger.info("agent.execute.abrir_cuenta")

        user_text = context.get_user_input()

        response_balance_agent = await run_agent(mensaje=user_text)

        await event_queue.enqueue_event(
            new_agent_text_message(str(response_balance_agent))
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        logger.info("agent.cancel.balance")
