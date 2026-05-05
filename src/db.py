import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

class MongoDBConnection:
    _instance = None

    def __new__(cls):
        # Patrón Singleton: Si no existe la instancia, la crea. Si ya existe, devuelve la misma.
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            uri = os.getenv("MONGODB_URI")
            
            try:
                # Inicializar el cliente de MongoDB
                cls._instance.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                # Seleccionar la base de datos (se creará automáticamente si no existe)
                cls._instance.db = cls._instance.client['chatbot_ai_db']
                
                # Verificar conexión haciendo un ping
                cls._instance.client.admin.command('ping')
                print("✅ Conexión a MongoDB Atlas exitosa (Singleton inicializado).")
            except Exception as e:
                print(f"❌ Error al conectar a MongoDB: {e}")
                cls._instance.client = None
                cls._instance.db = None
                
        return cls._instance

    def get_db(self):
        return self.db

def guardar_sesion(fase, usuario_raw, usuario_norm, respuesta, reconocido, metodo):
    """
    Guarda la interacción en la colección 'sesiones'.
    """
    db_conn = MongoDBConnection()
    db = db_conn.get_db()
    
    if db is not None:
        try:
            coleccion = db['sesiones']
            documento = {
                "fase": fase,
                "timestamp": datetime.utcnow(),
                "usuario_raw": usuario_raw,
                "usuario_norm": usuario_norm,
                "respuesta": respuesta,
                "reconocido": reconocido,
                "metodo": metodo
            }
            coleccion.insert_one(documento)
        except Exception as e:
            print(f"Error al guardar la sesión en MongoDB: {e}")
    else:
        print("Advertencia: No se guardó la sesión (sin conexión a BD).")
