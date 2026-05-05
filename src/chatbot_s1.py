import unicodedata
import string
from db import guardar_sesion

# Diccionario de reglas - Negocio local en Guadalajara
REGLAS_BOT = {
    "hola": "¡Quiúbole! Bienvenido a Tortas Ahogadas El Chato. ¿Qué se te va a ofrecer?",
    "horarios": "Abrimos todos los días de 9:00 AM a 5:00 PM. ¡Puro horario de comida tapatía!",
    "ubicacion": "Estamos en el centro de Guadalajara, a dos cuadras del Expiatorio.",
    "menu": "Tenemos tortas ahogadas (media o bien ahogada), tacos dorados y tejuino fresquecito.",
    "precio": "La torta ahogada tradicional cuesta $65 pesitos.",
    "pica": "Manejamos puro chile de Yahualica. Si no eres de por acá, te sugiero la media ahogada.",
    "domicilio": "¡Claro! Búscanos en las apps o llama al 33-1234-5678 para pasar a recoger.",
    "gracias": "¡Gracias a ti! Aquí te esperamos para que te eches una buena torta."
}

def normalizar(texto):
    """
    Convierte a minúsculas y elimina acentos y signos de puntuación.
    """
    # 1. Minúsculas
    texto = texto.lower()
    # 2. Eliminar acentos usando unicodedata
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # 3. Eliminar puntuación
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    # 4. Quitar espacios en blanco redundantes
    return texto.strip()

def obtener_respuesta(texto_norm):
    """
    Busca palabras clave en el texto normalizado.
    Retorna una tupla: (respuesta, fue_reconocido_booleano)
    """
    for clave, respuesta in REGLAS_BOT.items():
        if clave in texto_norm:
            return respuesta, True
            
    return "Híjole, no te entendí bien. ¿Me lo repites con otras palabras? Puedes preguntar por menú, horarios o ubicación.", False

def iniciar_chatbot():
    print("="*50)
    print("🤖 Iniciando Chatbot 'El Chato' (Fase 1: Reglas)")
    print("Escribe 'salir' para terminar la conversación.")
    print("="*50 + "\n")
    
    while True:
        entrada_usuario = input("Tú: ")
        
        if entrada_usuario.strip().lower() == 'salir':
            print("Bot: ¡Nos vemos! Que te vaya bonito.")
            break
            
        # Procesamiento
        texto_norm = normalizar(entrada_usuario)
        respuesta, reconocido = obtener_respuesta(texto_norm)
        
        print(f"Bot: {respuesta}")
        
        # Persistencia Crítica
        guardar_sesion(
            fase=1,
            usuario_raw=entrada_usuario,
            usuario_norm=texto_norm,
            respuesta=respuesta,
            reconocido=reconocido,
            metodo="diccionario_reglas"
        )

if __name__ == "__main__":
    iniciar_chatbot()
