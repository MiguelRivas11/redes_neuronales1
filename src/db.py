import os
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── Conexión ────────────────────────────────────────────────────
_client = None
_db = None

def get_db():
    """
    Patrón Singleton: reutiliza la conexión si ya existe.
    Conectar a MongoDB es costoso; no lo hagas en cada operación.
    """
    global _client, _db
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI no está definida en .env")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _db = _client["chatbot_db"]
        
        # Crear índice por timestamp para consultas eficientes
        _db["sesiones"].create_index([("timestamp", ASCENDING)])
        _db["sesiones"].create_index([("reconocido", ASCENDING)])
        print("[DB] Conexión a MongoDB establecida.")
    return _db

def guardar_sesion(fase, usuario_raw, usuario_norm, respuesta, reconocido, similitud=None, metodo="desconocido"):
    """
    Guarda un turno de conversación en la colección 'sesiones'.
    """
    db = get_db()
    doc = {
        "fase": fase,
        "timestamp": datetime.now(timezone.utc),
        "usuario_raw": usuario_raw,
        "usuario": usuario_norm,
        "respuesta": respuesta,
        "reconocido": reconocido,
        "similitud": similitud,
        "metodo": metodo
    }
    try:
        resultado = db["sesiones"].insert_one(doc)
        return str(resultado.inserted_id)
    except Exception as e:
        print(f"Error al guardar la sesión en MongoDB: {e}")
        return None

def obtener_no_reconocidos(fase="s1", limite=200):
    """
    Recupera mensajes que el bot NO pudo responder.
    Estos son el insumo clave para la Fase 2: muestran qué preguntan los usuarios reales.
    Returns: lista de strings (mensajes normalizados)
    """
    db = get_db()
    cursor = db["sesiones"].find(
        {"fase": fase, "reconocido": False},
        {"usuario": 1, "usuario_raw": 1, "_id": 0}
    ).sort("timestamp", ASCENDING).limit(limite)
    return list(cursor)

def obtener_todas_sesiones(fase=None, limite=500):
    """
    Recupera sesiones para análisis o entrenamiento del modelo NLP.
    Si fase=None, devuelve todas las fases.
    """
    db = get_db()
    filtro = {} if fase is None else {"fase": fase}
    cursor = db["sesiones"].find(filtro).sort(
        "timestamp", ASCENDING
    ).limit(limite)
    return list(cursor)

def estadisticas():
    """
    Resumen estadístico de las conversaciones almacenadas.
    Útil para el README y la entrega final.
    """
    db = get_db()
    col = db["sesiones"]
    total = col.count_documents({})
    reconocidos = col.count_documents({"reconocido": True})
    
    pipeline = [
        {"$group": {"_id": "$fase", "count": {"$sum": 1}}}
    ]
    por_fase = {doc["_id"]: doc["count"] for doc in col.aggregate(pipeline)}
    
    return {
        "total": total,
        "reconocidos": reconocidos,
        "no_reconocidos": total - reconocidos,
        "tasa_exito": round(reconocidos/total*100, 1) if total else 0,
        "por_fase": por_fase
    }

