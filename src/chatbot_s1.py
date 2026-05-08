# ================================================================
# src/chatbot_s1.py
# Chatbot basado en reglas con persistencia en MongoDB.
# ================================================================
import re
from db import guardar_sesion, estadisticas

# ── Base de conocimiento ─────────────────────────────────────────
# Negocio: "Gdl Secure Systems" - Soporte técnico y Ciberseguridad.
# Estas preguntas son clave para filtrar clientes antes de una consulta humana.
BASE = {
    "hola": "¡Hola! Bienvenido a Gdl Secure Systems. ¿En qué podemos ayudarte hoy?",
    "adios": "Hasta luego. Mantén tus sistemas actualizados y seguros.",
    "precio": "El diagnóstico de hardware cuesta $300 MXN. Las auditorías de red inician en $1,500.",
    "horario": "Atendemos de lunes a viernes de 9:00 AM a 6:00 PM y sábados de 10:00 AM a 2:00 PM.",
    "direccion": "Nuestra oficina está en la Colonia Americana, Guadalajara.",
    "servicios": "Ofrecemos limpieza de hardware, eliminación de malware y configuración de VPNs.",
    "mantenimiento": "Recomendamos mantenimiento preventivo cada 6 meses para evitar sobrecalentamiento.",
    "seguridad": "Si sospechas de un acceso no autorizado, desconecta el equipo de la red de inmediato.",
    "gracias": "¡De nada! ¿Hay algo más en lo que pueda apoyarte?",
    "password": "No compartas tus contraseñas por correo. Usa siempre un gestor de contraseñas seguro.",
    # Wildcard (Variedad):
    "cafe": "No vendemos café, pero si vienes a la oficina, ¡tenemos una cafetera lista para los clientes!"
}

# Mapa para limpiar acentos de forma eficiente
REEMPLAZOS_ACENTO = str.maketrans(
    "áéíóúÁÉÍÓÚüÜñÑ",
    "aeiouaeiouuunn"
)

def normalizar(texto):
    """Limpia el texto: minúsculas, quita acentos y signos de puntuación."""
    texto = texto.lower().strip()
    texto = texto.translate(REEMPLAZOS_ACENTO)
    # Elimina todo lo que no sea una letra o espacio
    texto = re.sub(r"[^\w\s]", "", texto)
    return texto

def buscar(normalizado):
    """Busca por coincidencia exacta o palabra clave."""
    # 1. Intento: Coincidencia exacta
    if normalizado in BASE:
        return BASE[normalizado], "exacto"
    
    # 2. Intento: Palabra clave contenida en la oración
    palabras = normalizado.split()
    for clave in BASE:
        if clave in palabras:
            return BASE[clave], "keyword"
            
    return None, None

def chatbot_s1(mensaje_raw):
    """Procesa el mensaje y lo registra en MongoDB Atlas."""
    normalizado = normalizar(mensaje_raw)
    respuesta, metodo = buscar(normalizado)

    if respuesta:
        reconocido = True
    else:
        reconocido = False
        respuesta = ("No tengo una respuesta exacta para eso, pero he registrado tu duda "
                     "para que un técnico la revise pronto.")

    # Guardado CRÍTICO en la base de datos
    try:
        doc_id = guardar_sesion(
            fase="s1",
            usuario_raw=mensaje_raw,
            usuario_norm=normalizado,
            respuesta=respuesta,
            reconocido=reconocido,
            metodo=metodo or "sin_match"
        )
        print(f"  [DB] Registro exitoso (ID: {doc_id})")
    except Exception as e:
        print(f"  [Error DB] No se pudo guardar: {e}")

    return respuesta

# ── Interfaz de Consola ──────────────────────────────────────────
if __name__ == "__main__":
    print("=== Gdl Secure Systems: Chatbot S1 activo ===")
    print("Comandos especiales: 'stats' para métricas, 'salir' para terminar.\n")
    
    while True:
        entrada = input("Tú: ").strip()
        
        if not entrada: continue
        
        if entrada.lower() == "salir":
            print(f"\nResumen de hoy: {estadisticas()}")
            break
            
        if entrada.lower() == "stats":
            print(f"\n[ESTADÍSTICAS] {estadisticas()}\n")
            continue
            
        bot_response = chatbot_s1(entrada)
        print(f"Bot: {bot_response}\n")