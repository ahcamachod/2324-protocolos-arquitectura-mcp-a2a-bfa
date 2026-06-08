import { HttpAgent } from "@ag-ui/client";

export class ACBankAgent {
  constructor(url, agentName) {
    this.url = url; // ✅ guarda la URL aquí
    this.agent = new HttpAgent({ url });
    this.agentName = agentName;
  }

  async run(message) {
    try {
      console.log("📤 Enviando a:", this.url);

      const response = await fetch(this.url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          session_id: "123",
          client_id: "123",
          agent: this.agentName,
        }),
      });

      console.log("📥 Status:", response.status);

      if (!response.ok) {
        const text = await response.text();
        console.error("❌ Error en el backend:", text);
        throw new Error("Error de API");
      }

      const data = await response.json();

      console.log("✅ Respuesta:", data);

      return {
        messages: [
          {
            role: "assistant",
            content: data?.respuesta || "Sin respuesta",
          },
        ],
      };
    } catch (err) {
      console.error("🔥 ERROR COMPLETO:", err);

      return {
        messages: [
          {
            role: "assistant",
            content: "Error al llamar al agente",
          },
        ],
      };
    }
  }
}
