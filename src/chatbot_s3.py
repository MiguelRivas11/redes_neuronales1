"""
src/chatbot_s3.py
LLM con RAG desde MongoDB y memoria persistente por session_id.
"""
import os
import uuid
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from db import get_db, guardar_sesion

load_dotenv()

USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() in ("1", "true", "yes")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
VENTANA = int(os.getenv("CHATBOT_S3_VENTANA", "8"))

# Intentar importar el Chatbot TF-IDF (S2) para fallback si LLM falla
try:
    from chatbot_s2 import ChatbotNLP
except Exception:
    ChatbotNLP = None

# NLP fallback instance (lazy)
_nlp_bot = None

def _get_nlp():
    global _nlp_bot
    if _nlp_bot is None and ChatbotNLP is not None:
        try:
            _nlp_bot = ChatbotNLP(umbral=0.2)
        except Exception:
            _nlp_bot = None
    return _nlp_bot


def recuperar_contexto_rag(n=15):
    db = get_db()

    s2_docs = list(db["sesiones"].find(
        {"fase": "s2", "reconocido": True, "similitud": {"$gte": 0.3}},
        {"usuario_raw": 1, "respuesta": 1, "similitud": 1}
    ).sort("similitud", -1).limit(n))

    s1_docs = []
    if len(s2_docs) < n:
        s1_docs = list(db["sesiones"].find(
            {"fase": "s1", "reconocido": True},
            {"usuario_raw": 1, "respuesta": 1}
        ).limit(n - len(s2_docs)))

    todos = s2_docs + s1_docs
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


def guardar_turno_s3(session_id, rol, contenido):
    db = get_db()
    db["sesiones_s3"].insert_one({
        "session_id": session_id,
        "rol": rol,
        "contenido": contenido,
        "timestamp": datetime.now(timezone.utc)
    })


def recuperar_historial(session_id, ventana=VENTANA):
    db = get_db()
    docs = list(db["sesiones_s3"].find(
        {"session_id": session_id},
        {"rol": 1, "contenido": 1, "timestamp": 1, "_id": 0}
    ).sort("timestamp", -1).limit(ventana))
    return [{"role": d["rol"], "content": d["contenido"]} for d in reversed(docs)]


def llamar_llm(mensajes):
    if USE_OLLAMA:
        payload = {"model": OLLAMA_MODEL, "messages": mensajes, "stream": False, "options": {"temperature": 0.7}}
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and "message" in data:
                return data["message"].get("content", "")
            return str(data)
        except requests.exceptions.ConnectionError:
            return "Error: Ollama no esta corriendo. Ejecuta: ollama serve"
        except Exception as e:
            return f"Error LLM: {e}"
    else:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_KEY)
            resp = client.chat.completions.create(model="gpt-4o-mini", messages=mensajes, max_tokens=300, temperature=0.7)
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error OpenAI: {e}"


def chatbot_s3(mensaje, session_id):
    contexto_rag = recuperar_contexto_rag(n=12)
    historial = recuperar_historial(session_id)

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

    mensajes = [{"role": "system", "content": system}] + historial + [{"role": "user", "content": mensaje}]

    respuesta = llamar_llm(mensajes)

    metodo = "llm_rag"
    if isinstance(respuesta, str) and respuesta.startswith("Error"):
        nlp = _get_nlp()
        if nlp is not None:
            try:
                respuesta = nlp.responder(mensaje)
                metodo = "llm_rag_fallback_nlp"
            except Exception:
                pass

    guardar_turno_s3(session_id, "user", mensaje)
    guardar_turno_s3(session_id, "assistant", respuesta)

    guardar_sesion(fase="s3", usuario_raw=mensaje, usuario_norm=mensaje.lower().strip(), respuesta=respuesta, reconocido=True, metodo=metodo)
    return respuesta


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
