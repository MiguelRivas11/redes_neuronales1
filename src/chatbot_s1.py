import re
from db import guardar_sesion, estadisticas

# Diccionario de reglas - Negocio local en Guadalajara
BASE = {
    "hola": "¡Quiúbole! Bienvenido a Tortas Ahogadas El Chato. ¿Qué se te va a ofrecer?",
    "horarios": "Abrimos todos los días de 9:00 AM a 5:00 PM. ¡Puro horario de comida tapatía!",
    "ubicacion": "Estamos en el centro de Guadalajara, a dos cuadras del Expiatorio.",
    "menu": "Tenemos tortas ahogadas (media o bien ahogada), tacos dorados y tejuino fresquecito.",
    "precio": "La torta ahogada tradicional cuesta $65 pesitos.",
    "pica": "Manejamos puro chile de Yahualica. Si no eres de por acá, te sugiero la media ahogada.",
    "domicilio": "¡Claro! Búscanos en las apps o llama al 33-1234-5678 para pasar a recoger.",
    "gracias": "¡Gracias a ti! Aquí te esperamos para que te eches una buena torta."
}

REEMPLAZOS_ACENTO = str.maketrans(
    "aeiouAEIOUáéíóúÁÉÍÓÚüÜñÑ",
    "aeiouaeiouaeiouaeiouuunn"
)

def normalizar(texto):
    """Limpia el texto para comparación."""
    texto = texto.lower().strip()
    texto = texto.translate(REEMPLAZOS_ACENTO)
    texto = re.sub(r"[^\w\s]", "", texto)
    return texto

def buscar(normalizado):
    """
    Dos estrategias de búsqueda:
    1. Match exacto
    2. Palabra clave contenida en el mensaje
    Retorna (respuesta, metodo) o (None, None)
    """
    if normalizado in BASE:
        return BASE[normalizado], "exacto"
    
    for clave in BASE:
        if clave in normalizado.split():
            return BASE[clave], "keyword"
            
    return None, None

def chatbot_s1(mensaje_raw):
    """
    Procesa un mensaje, busca respuesta y guarda en MongoDB.
    Retorna la respuesta al usuario.
    """
    normalizado = normalizar(mensaje_raw)
    respuesta, metodo = buscar(normalizado)
    
    if respuesta:
        reconocido = True
    else:
        reconocido = False
        respuesta = ("No tengo una respuesta para eso. "
                     "Tu pregunta queda registrada para mejorar el sistema.")

    # Guardar en MongoDB
    doc_id = guardar_sesion(
        fase="s1",
        usuario_raw=mensaje_raw,
        usuario_norm=normalizado,
        respuesta=respuesta,
        reconocido=reconocido,
        metodo=metodo or "sin_match"
    )
    if doc_id:
        print(f" [DB] Sesión guardada: {doc_id}")
        
    return respuesta

if __name__ == "__main__":
    print("Chatbot S1 activo. Escribe 'stats' para ver estadísticas.")
    print("Escribe 'salir' para terminar.\n")
    
    while True:
        entrada = input("Tú: ").strip()
        if not entrada:
            continue
            
        if entrada.lower() == "salir":
            stats = estadisticas()
            print(f"\nResumen final: {stats}")
            break
            
        if entrada.lower() == "stats":
            print(estadisticas())
            continue
            
        print(f"Bot: {chatbot_s1(entrada)}\n")
