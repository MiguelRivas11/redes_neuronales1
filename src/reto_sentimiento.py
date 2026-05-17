import os
import uuid
import chromadb
from textblob import TextBlob
from chatbot_s3 import llamar_llm, recuperar_historial, guardar_turno_s3
from chatbot_s2 import CORPUS_BASE

# Inicializar ChromaDB para Búsqueda Semántica
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="tortas_rag")

# Poblar ChromaDB si está vacía
if collection.count() == 0:
    print("[ChromaDB] Inicializando base vectorial con el corpus de Tortas Ahogadas...")
    docs = list(CORPUS_BASE.values())
    ids = [f"doc_{i}" for i in range(len(docs))]
    metadatas = [{"pregunta": q} for q in CORPUS_BASE.keys()]
    collection.add(documents=docs, metadatas=metadatas, ids=ids)

def busqueda_semantica_chroma(texto, n_results=3):
    """Recupera contexto usando búsqueda vectorial pura (Embeddings) en ChromaDB."""
    resultados = collection.query(
        query_texts=[texto],
        n_results=n_results
    )
    contexto = []
    if resultados['documents']:
        for doc in resultados['documents'][0]:
            contexto.append(f"INFO: {doc}")
    return "\n".join(contexto)

def analizar_sentimiento(texto):
    """Retorna estado emocional y polaridad del texto."""
    # Usamos traduccion interna a ingles porque TextBlob es mucho mas preciso ahi.
    # Si falla por conexion, usamos el analisis nativo (aunque menos preciso).
    try:
        analisis = TextBlob(texto).translate(from_lang='es', to='en')
        pol = analisis.sentiment.polarity
    except:
        pol = TextBlob(texto).sentiment.polarity

    if pol < -0.3:
        estado = "enojado"
    elif pol < -0.05:
        estado = "frustrado"
    elif pol < 0.1:
        estado = "neutral"
    elif pol < 0.5:
        estado = "satisfecho"
    else:
        estado = "muy_positivo"
    
    return {"estado": estado, "polaridad": round(pol, 3)}

def instruccion_tono(estado):
    instrucciones = {
        "enojado": "ATENCIÓN: El usuario está extremadamente molesto o enojado. Responde con MÁXIMA EMPATÍA. Pide disculpas sinceramente primero, valida su frustración, y ofrece una solución servicial.",
        "frustrado": "El usuario muestra frustración o impaciencia. Sé muy paciente, ve directo al punto, sé claro y no des respuestas largas.",
        "neutral": "Responde de forma profesional, eficiente y servicial, como un buen mesero tapatío.",
        "satisfecho": "El usuario está satisfecho con el servicio. Puedes ser más amigable y usar un tono cálido.",
        "muy_positivo": "El usuario está súper feliz y entusiasmado. Comparte su entusiasmo, usa signos de exclamación y agradece su preferencia muy alegremente.",
    }
    return instrucciones.get(estado, instrucciones["neutral"])

def chatbot_adaptativo(mensaje, session_id):
    """LLM con tono adaptado al sentimiento y contexto semántico de ChromaDB."""
    
    # 1. Analisis de Sentimiento (Reto 1)
    sentimiento = analizar_sentimiento(mensaje)
    print(f"   [SENTIMIENTO] Detectado: {sentimiento['estado'].upper()} (polaridad: {sentimiento['polaridad']})")
    
    # 2. Búsqueda Semántica con ChromaDB (Reto 2)
    contexto_rag = busqueda_semantica_chroma(mensaje)
    print(f"   [CHROMADB] Búsqueda vectorial exitosa.")
    
    # 3. Recuperar historial de MongoDB
    historial = recuperar_historial(session_id)
    
    # 4. Construir System Prompt Dinámico
    tono = instruccion_tono(sentimiento["estado"])
    
    system = f"""Eres un asistente virtual de atención al cliente de 'Tortas Ahogadas El Chato'.
Responde siempre en español.

CONTEXTO DE LA BASE DE CONOCIMIENTO (Recuperado vía ChromaDB Embeddings):
{contexto_rag}

TONO EMOCIONAL REQUERIDO PARA TU RESPUESTA:
{tono}

INSTRUCCIONES ADICIONALES:
- Usa estrictamente el contexto proporcionado para responder preguntas sobre el negocio.
- Si no sabes algo, admite que no tienes la información. No inventes precios ni reglas."""

    mensajes = [{"role": "system", "content": system}] + historial + [{"role": "user", "content": mensaje}]
    
    # 5. Llamar a Llama 3.2
    respuesta = llamar_llm(mensajes)
    
    # 6. Guardar en MongoDB para persistencia
    guardar_turno_s3(session_id, "user", mensaje)
    guardar_turno_s3(session_id, "assistant", respuesta)
    
    return respuesta, sentimiento

if __name__ == "__main__":
    session_id = str(uuid.uuid4())
    print("\n" + "="*60)
    print("🤖 CHATBOT V4 — RETO EXTRA (Sentimiento + ChromaDB)")
    print("="*60)
    print(f"Session ID: {session_id}")
    print("INSTRUCCIÓN: Prueba escribiendo un mensaje MUY ENOJADO (ej. 'Que asco su servicio') y luego uno MUY FELIZ (ej. 'Me encantó la torta, son los mejores!').")
    print("Escribe 'salir' para terminar.\n")
    
    while True:
        entrada = input("Tú: ").strip()
        if entrada.lower() == "salir":
            break
        if not entrada:
            continue
            
        respuesta, sent = chatbot_adaptativo(entrada, session_id)
        print(f"Bot: {respuesta}\n")
