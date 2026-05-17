# ================================================================
# src/chatbot_s3.py
# LLM con RAG desde MongoDB. Memoria persistente por session_id.
# Rama: fase-3
# ================================================================

import os
import uuid
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

from db import get_db, guardar_sesion

load_dotenv()

USE_OLLAMA = True  # Cambia a False para usar OpenAI
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2"

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

VENTANA = 8  # Mensajes de historial a incluir

# ── RAG: Construir contexto desde MongoDB ───────────────────────
def recuperar_contexto_rag(n=15):
    """
    Extrae los N pares pregunta-respuesta mas exitosos de MongoDB
    para usarlos como contexto del LLM.
    Criterio de seleccion:
      - Reconocidos correctamente (reconocido: True)
      - De cualquier fase (S1 o S2)
      - Con mayor similitud en S2 (las "mas seguras")
      - Sin duplicar respuestas identicas
    """
    db = get_db()
    
    # Primero los de S2 con alta similitud (mas confiables)
    s2_docs = list(db["sesiones"].find(
        {"fase": "s2", "reconocido": True, "similitud": {"$gte": 0.3}},
        {"usuario_raw": 1, "respuesta": 1, "similitud": 1}
    ).sort("similitud", -1).limit(n))
    
    # Completar con S1 si no hay suficientes de S2
    s1_docs = []
    if len(s2_docs) < n:
        s1_docs = list(db["sesiones"].find(
            {"fase": "s1", "reconocido": True},
            {"usuario_raw": 1, "respuesta": 1}
        ).limit(n - len(s2_docs)))
        
    todos = s2_docs + s1_docs
    
    # Formatear como contexto para el system prompt
    if not todos:
        return "No hay historial previo disponible."
        
    lineas = ["Pares pregunta-respuesta de conversaciones reales:"]
    respuestas_vistas = set()
    
    for doc in todos:
        resp = doc.get("respuesta", "")
        if resp not in respuestas_vistas:
            lineas.append(f"P: {doc.get('usuario_raw','')}")
            lineas.append(f"R: {resp}")
            lineas.append("")
            respuestas_vistas.add(resp)
            
    return "\n".join(lineas)

# ── Memoria persistente por session_id ─────────────────────────
def guardar_turno_s3(session_id, rol, contenido):
    """Guarda un turno del LLM en MongoDB con session_id."""
    db = get_db()
    db["sesiones_s3"].insert_one({
        "session_id": session_id,
        "rol": rol,
        "contenido": contenido,
        "timestamp": datetime.now(timezone.utc)
    })

def recuperar_historial(session_id, ventana=VENTANA):
    """Recupera los ultimos N mensajes de una sesion."""
    db = get_db()
    docs = list(db["sesiones_s3"].find(
        {"session_id": session_id},
        {"rol": 1, "contenido": 1, "_id": 0}
    ).sort("timestamp", -1).limit(ventana))
    
    # Invertir para orden cronologico
    return [
        {"role": d["rol"], "content": d["contenido"]}
        for d in reversed(docs)
    ]

# ── LLM ────────────────────────────────────────────────────────
def llamar_llm(mensajes):
    """Llama al LLM con el historial completo."""
    if USE_OLLAMA:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": mensajes,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 300}
        }
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=60)
            r.raise_for_status()
            return r.json()["message"]["content"]
        except requests.exceptions.ConnectionError:
            return "Error: Ollama no esta corriendo. Ejecuta: ollama serve"
        except Exception as e:
            return f"Error LLM: {e}"
    else:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensajes,
            max_tokens=300,
            temperature=0.7
        )
        return resp.choices[0].message.content

def chatbot_s3(mensaje, session_id):
    """
    Flujo completo de S3:
    1. Recuperar contexto RAG de MongoDB
    2. Recuperar historial de la sesion actual
    3. Construir mensajes con system prompt dinamico
    4. Llamar al LLM
    5. Guardar turno en MongoDB
    """
    # 1. Contexto RAG desde MongoDB
    contexto_rag = recuperar_contexto_rag(n=12)
    
    # 2. Historial de esta sesion
    historial = recuperar_historial(session_id)
    
    # 3. System prompt con RAG integrado
    system = f"""Eres un asistente virtual de atencion al cliente.
Responde siempre en espanol, de forma profesional y empatica.

CONTEXTO BASADO EN CONVERSACIONES REALES:
{contexto_rag}

INSTRUCCIONES:
- Usa el contexto anterior como tu base de conocimiento principal.
- Si la pregunta del usuario coincide con algo del contexto, usa esa informacion.
- Si no tienes la informacion, admitelo y ofrece transferir con un agente.
- Eres consciente del historial de esta conversacion.
- Nunca inventes precios, fechas o datos especificos."""

    mensajes = [
        {"role": "system", "content": system}
    ] + historial + [
        {"role": "user", "content": mensaje}
    ]
    
    # 4. Llamar al LLM
    respuesta = llamar_llm(mensajes)
    
    # 5. Guardar ambos turnos en MongoDB
    guardar_turno_s3(session_id, "user", mensaje)
    guardar_turno_s3(session_id, "assistant", respuesta)
    
    # Tambien registrar en coleccion principal para estadisticas
    guardar_sesion(
        fase="s3",
        usuario_raw=mensaje,
        usuario_norm=mensaje.lower().strip(),
        respuesta=respuesta,
        reconocido=True,  # LLM siempre responde algo
        metodo="llm_rag"
    )
    
    return respuesta

# ── Loop principal ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Chatbot S3 — LLM con RAG desde MongoDB")
    print("Escribe 'nuevo' para nueva sesion, 'salir' para terminar.\n")
    
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print("(Guarda este ID para continuar la conversacion despues)\n")
    
    while True:
        entrada = input("Tu: ").strip()
        if not entrada:
            continue
        if entrada.lower() == "salir":
            break
        if entrada.lower() == "nuevo":
            session_id = str(uuid.uuid4())
            print(f"Nueva sesion iniciada: {session_id}\n")
            continue
        if entrada.lower().startswith("retomar:"):
            session_id = entrada.split(":", 1)[1].strip()
            print(f"Retomando sesion: {session_id}\n")
            continue
            
        respuesta = chatbot_s3(entrada, session_id)
        print(f"Bot: {respuesta}\n")
