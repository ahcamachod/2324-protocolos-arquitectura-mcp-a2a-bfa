from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
import os

load_dotenv()

_llm = init_chat_model(
    model="gpt-4o", 
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=0.7
)

app = FastAPI()

agente_abrir_cuenta = create_agent(
    _llm,
    tools=[],
    system_prompt=("Eres un especialista en apertura de cuentas del banco ACBank. "
                   "Ayuda al cliente a abrir una cuenta y explica los tipos disponibles de cuenta "
                   "que son cuenta de ahorros y cuenta corriente."
    )
)

class AbrirCuentaRequest(BaseModel):
    message : str

@app.post("/send")
async def consultar(request: AbrirCuentaRequest):
    mensaje = request.message
    if not mensaje:
        raise HTTPException(
            status_code=400, detail="El campo 'mensaje' es obligatorio"
        )        
    try:
        resultado = agente_abrir_cuenta.invoke(
            {"messages":[HumanMessage(content=mensaje)]}
        )
        mensaje_ia = resultado["messages"][-1]
        return {"respuesta":mensaje_ia.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def health():
    return {"status":"ok"}        