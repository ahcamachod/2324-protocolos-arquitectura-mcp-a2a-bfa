import os
from fastmcp import FastMCP, Context
from fastmcp.prompts import Message
from typing import Optional, Dict, Any
import random
import json

mcp = FastMCP("ACBank")

DB_FILE = "/app/db.json"

def load_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        return {"cuentas": {}, "tarjetas": {}}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"cuentas": {}, "tarjetas": {}}

def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump({
                "cuentas": cuentas_acbank,
                "tarjetas": tarjetas_acbank
            }, f, indent=2)
    except Exception as e:
        print("Error al guardar DB:", e)

db = load_db()
cuentas_acbank = db.get("cuentas", {})
tarjetas_acbank = db.get("tarjetas", {})

def extract_resource_data(resource_result) -> Optional[Dict[str, Any]]:
    if not resource_result:
        return None
    try:
        if not resource_result.contents:
            return None

        raw = resource_result.contents[0].content

        if isinstance(raw, str):
            return json.loads(raw)

        return raw
    except Exception as e:
        print("Error extract_resource_data:", e)
        return None

# ---------------------RESOURCES-------------------------- #

@mcp.resource("cuenta://{dni}")
async def obtener_cuenta(dni: str):
    dni = dni.strip()
    data = cuentas_acbank.get(dni, {"error": "Cuenta no encontrada"})
    return json.dumps(data)


@mcp.resource("tarjeta://{dni}")
async def obtener_tarjeta(dni: str):
    dni = dni.strip()
    data = tarjetas_acbank.get(dni, {"error": "Tarjeta no encontrada"})


# ---------------------PROMPTS-------------------------- #

@mcp.prompt
def abrir_cuenta_prompt(nombre: str, dni: str):
    return [
        Message("El cliente desea abrir una cuenta."),
        Message(f"Nombre: {nombre} | dni: {dni}"),
        Message("Verifique si ya existe una cuenta antes de crearla.", role="assistant"),
    ]


@mcp.prompt
def solicitar_tarjeta_prompt(dni: str, tipo: str):
    return [
        Message(f"El Cliente desea una tarjeta {tipo}"),
        Message(f"dni: {dni}"),
        Message("Verifique si ya tiene una cuenta antes de emitir la tarjeta.",
                role="assistant"),
    ]

# ---------------------TOOLS-------------------------- #

@mcp.tool
async def consultar_cuenta(dni: str, ctx: Context):
    resource = await ctx.read_resource(f"cuenta://{dni}")
    print("\n ================================= \n",
          resource, "\n ================================= \n")
    data = extract_resource_data(resource)
    if not data or "error" in data:
        return {"existe": False}
    return {"existe": True, "cuenta": data}


@mcp.tool
async def consultar_tarjeta(dni: str, ctx: Context):
    resource = await ctx.read_resource(f"tarjeta://{dni}")
    print("\n ================================= \n",
          resource, "\n ================================= \n")
    data = extract_resource_data(resource)
    if not data or "error" in data:
        return {"existe": False}
    return {"existe": True, "tarjeta": data}


@mcp.tool
async def crear_o_buscar_cuenta(nombre: str, dni: str, ctx: Context):
    dni = dni.strip()
    await ctx.info(f"[Cuenta] Processando DNI {dni}")
    resource = await ctx.read_resource(f"cuenta://{dni}")
    data = extract_resource_data(resource)
    if data and "error" not in data:
        return {
            "status": "existente",
            "cuenta": data
        }
    numero_cuenta = random.randint(10000, 99999)
    cuenta = {
        "nombre": nombre,
        "numero": numero_cuenta,
        "saldo": 0.0,
    }

    cuentas_acbank[dni] = cuenta
    save_db()

    return {
        "status": "creada",
        "cuenta": cuenta
    }


@mcp.tool
async def solicitar_tarjeta(dni: str, tipo: str, ctx: Context):
    dni = dni.strip()
    await ctx.info(f"[Tarjeta] Solicitud para el DNI {dni}")

    resource = await ctx.read_resource(f"cuenta://{dni}")
    cuenta = extract_resource_data(resource)

    if not cuenta or "error" in cuenta:
        return {
            "status": "error",
            "mensaje": "El cliente no tiene cuenta"
        }

    resource_tarjeta = await ctx.read_resource(f"tarjeta://{dni}")
    tarjeta_existente = extract_resource_data(resource_tarjeta)

    if tarjeta_existente and "error" not in tarjeta_existente:
        return {
            "status": "existente",
            "tarjeta": tarjeta_existente
        }

    numero_tarjeta = random.randint(100000, 999999)
    tarjeta = {
        "numero": numero_tarjeta,
        "tipo": tipo,
        "limite": random.randint(1000, 5000)
    }

    tarjetas_acbank[dni] = tarjeta
    save_db()

    return {
        "status": "creada",
        "tarjeta": tarjeta
    }


@mcp.tool
async def generar_prompt_apertura(nombre: str, dni: str, ctx: Context):
    prompt = await ctx.get_prompt(
        "abrir_cuenta_prompt",
        {"nombre": nombre, "dni": dni}
    )
    return [m.content for m in prompt.messages]