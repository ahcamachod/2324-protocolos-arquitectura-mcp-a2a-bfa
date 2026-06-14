import asyncio
import httpx
from a2a.client import A2ACardResolver

AGENT_ENDPOINTS = [
    "http://agente_tarjeta_credito:8000",
    "http://agente_abrir_cuenta:8000"
]


def normalize(text):
    if not text:
        return ""
    return text.lower().strip()


async def discover_agents():
    registry = {}

    async with httpx.AsyncClient(timeout=5) as client:
        for url in AGENT_ENDPOINTS:

            for attempt in range(3):
                try:
                    resolver = A2ACardResolver(
                        httpx_client=client,
                        base_url=url
                    )

                    card = await resolver.get_agent_card()

                    for skill in card.skills:
                        registry[skill.id] = {
                            "agent_url": url,
                            "name": skill.name,
                            "description": skill.description,
                            "tags": skill.tags,
                            "examples": skill.examples,
                            "type": "agent"
                        }

                    break

                except Exception as e:
                    print(f"El intento {attempt+1} falló en {url}: {e}")
                    await asyncio.sleep(2)

    return registry
