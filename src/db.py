# ================================================================
# src/db.py
# Modulo centralizado para todas las operaciones con MongoDB.
# ================================================================
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# ── Configuración de Rutas ──────────────────────────────────────
# Obtenemos la ruta de este archivo (src/db.py)
base_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para encontrar el .env en la raiz
ruta_env = os.path.join(base_dir, '..', '.env')

# Cargamos el archivo .env especificando la ruta exacta
if os.path.exists(ruta_env):
    load_dotenv(dotenv_path=ruta_env)
else:
    print(f"[Aviso] No se encontro el archivo .env en: {ruta_env}")

# ── Conexión (Patrón Singleton) ──────────────────────────────────
_client = None
_db = None

def get_db():
    """
    Reutiliza la conexion si ya existe para ahorrar recursos.
    """
    global _client, _db
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            # Si llegas aqui, revisa que el nombre en .env sea exacto
            raise ValueError("Error: MONGODB_URI no esta definida en el archivo .env")
        
        # Conexión con timeout de 5 segundos para no quedar bloqueado
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _db = _client["chatbot_db"]
        
        # Crear índices para optimizar consultas futuras
        _db["sesiones"].create_index([("timestamp", ASCENDING)])
        _db["sesiones"].create_index([("reconocido", ASCENDING)])
        
        print("[DB] Conexion a MongoDB establecida con exito.")
    return _db

# ── Operaciones CRUD ─────────────────────────────────────────────

def guardar_sesion(fase, usuario_raw, usuario_norm, respuesta,
                   reconocido, similitud=None, metodo="desconocido"):
    """
    Guarda cada interaccion en la coleccion 'sesiones'.
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
    resultado = db["sesiones"].insert_one(doc)
    return str(resultado.inserted_id)

def obtener_no_reconocidos(fase="s1", limite=200):
    """
    Recupera mensajes que el bot NO pudo responder.
    Insumo clave para la Fase 2.
    """
    db = get_db()
    cursor = db["sesiones"].find(
        {"fase": fase, "reconocido": False},
        {"usuario": 1, "usuario_raw": 1, "_id": 0}
    ).sort("timestamp", ASCENDING).limit(limite)
    return list(cursor)

def obtener_todas_sesiones(fase=None, limite=1000):
    """
    Recupera sesiones de MongoDB para analitica/entrenamiento.
    Si se indica fase, filtra por esa fase.
    """
    db = get_db()
    filtro = {"fase": fase} if fase else {}
    cursor = db["sesiones"].find(
        filtro,
        {
            "fase": 1,
            "usuario": 1,
            "usuario_raw": 1,
            "respuesta": 1,
            "reconocido": 1,
            "similitud": 1,
            "metodo": 1,
            "timestamp": 1,
            "_id": 0,
        },
    ).sort("timestamp", ASCENDING).limit(limite)
    return list(cursor)

def estadisticas():
    """
    Genera un resumen estadistico para el comando 'stats'.
    """
    try:
        db = get_db()
        col = db["sesiones"]
        total = col.count_documents({})
        if total == 0:
            return {"total": 0, "reconocidos": 0, "tasa_exito": 0}
            
        reconocidos = col.count_documents({"reconocido": True})
        
        return {
            "total": total,
            "reconocidos": reconocidos,
            "no_reconocidos": total - reconocidos,
            "tasa_exito": round(reconocidos/total*100, 1)
        }
    except Exception as e:
        return {"error": str(e)}