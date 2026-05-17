# ================================================================
# src/chatbot_s2.py
# Chatbot NLP con TF-IDF. El corpus se enriquece con datos
# reales de MongoDB generados en la Semana 1.
# Rama: fase-2
# ================================================================

import re
import nltk
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from db import guardar_sesion, obtener_todas_sesiones, estadisticas

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("punkt_tab", quiet=True)

stemmer = SnowballStemmer("spanish")
STOP_ES = set(stopwords.words("spanish"))
STOP_ES.update(["hola", "ok", "oye"])

# ── Corpus base ─────────────────────────────────────────────────
# Este es el corpus inicial. Se AMPLIA con datos de MongoDB.
CORPUS_BASE = {
    "hola buenas tardes buenos dias que tal": "¡Quiúbole! Bienvenido a Tortas Ahogadas El Chato, las más buenas de todo Jalisco.",
    "que horarios tienen abiertos a que hora abren cierran": "Abrimos de lunes a domingo, desde las 9:00 AM hasta las 5:00 PM. ¡Puro horario de comida tapatía!",
    "donde estan ubicados su direccion donde es": "Estamos ubicados en el centro histórico de Guadalajara, exactamente a dos cuadras del Templo Expiatorio. ¡No hay pierde!",
    "que venden cual es el menu que tienen de comer": "Nuestro menú principal son las tradicionales tortas ahogadas (media ahogada, bien ahogada o sin chile). También tenemos tacos dorados de papa, frijol y requesón, y para tomar tenemos un tejuino fresquecito o agua de jamaica.",
    "cuanto cuesta la torta precio de las cosas": "La torta ahogada tradicional cuesta $65 pesos. Los tacos dorados cuestan $15 pesos cada uno, y el vaso de tejuino grande está en $35 pesos.",
    "pican mucho las tortas que chile usan": "Manejamos puro chile de árbol de Yahualica. Es bastante picoso. Si no eres de por acá o no comes chile, te sugiero pedirla 'sin chile' o 'media ahogada' para que no te enchiles feo.",
    "tienen envios a domicilio me la traen a casa": "¡Claro que sí! Puedes buscarnos en aplicaciones de comida como Uber Eats, Rappi o Didi Food. O si prefieres, llama directo al 33-1234-5678 para pasar a recoger tu pedido al local.",
    "aceptan tarjeta de credito o debito bitcoin pagos": "Aceptamos pagos en efectivo, tarjetas de crédito/débito (Visa, Mastercard, Amex) y también transferencias SPEI. Por el momento no aceptamos criptomonedas, vales de despensa ni trueques.",
    "hacen eventos especiales o fiestas facturan": "Sí facturamos, solo pídelo en caja. También podemos llevar nuestras tortas a tus eventos privados o fiestas, tenemos paquetes desde 50 tortas. Llama al número del local para cotizar.",
    "venden comida vegetariana o vegana pizzas hamburguesas": "No vendemos pizzas, hamburguesas ni sushi. Somos una tortería tradicional. Si eres vegetariano, te podemos ofrecer tacos dorados de papa o frijol con pura salsa de jitomate y col, ¡están riquísimos!",
    "quien es el dueno quien es el chato historia": "El negocio fue fundado en 1998 por Don 'Chato' Rodríguez, un tapatío de corazón que empezó con un carrito en la calle y ahora tiene este gran local gracias a su receta secreta de salsa de Yahualica.",
    "tienen sucursales en otras ciudades paises df monterrey": "No, por ahora somos un negocio local y 100% tapatío. Solo tenemos nuestra única sucursal en el centro de Guadalajara. No enviamos tortas por paquetería porque se aguadan.",
    "se puede reservar mesa apartar lugar": "No tomamos reservaciones. El servicio es conforme van llegando los clientes, pero no te preocupes, el servicio es muy rápido y siempre hay lugar o se desocupa una mesa pronto.",
    "dan servilletas cucharas me manche": "¡Claro! La torta ahogada se come con la mano, pero te damos cuchara para la salsita que sobra y todas las servilletas que necesites gratis. ¡Es parte de la experiencia mancharse!",
    "se puede llevar mascotas son pet friendly": "Sí somos un local pet-friendly. Tienes que traer a tu mascota con correa y pueden estar en las mesas de la terraza exterior sin ningún problema.",
    "muchas gracias adios nos vemos": "¡Gracias a ti por tu preferencia! Aquí te esperamos pronto para que te eches otra buena torta ahogada. ¡Que te vaya excelente!"
}

def pipeline_nlp(texto):
    """Tokenizacion + stopwords + stemming."""
    texto = texto.lower()
    texto = re.sub(r"[^a-zaeiouan\s]", "", texto)
    tokens = word_tokenize(texto, language="spanish")
    tokens = [t for t in tokens if t not in STOP_ES and len(t) > 1]
    return [stemmer.stem(t) for t in tokens]

def enriquecer_corpus_desde_mongodb():
    """
    Lee las sesiones de S1 que fueron RECONOCIDAS y las agrega al corpus.
    Esto amplia el modelo con variaciones de lenguaje real que los usuarios usaron.
    Nota: Solo se agregan las reconocidas porque sabemos que tienen una respuesta correcta asociada.
    """
    sesiones = obtener_todas_sesiones(fase="s1")
    corpus_extra = {}
    for s in sesiones:
        if s.get("reconocido") and s.get("usuario") and s.get("respuesta"):
            # Evitar duplicados exactos con el corpus base
            if s["usuario"] not in CORPUS_BASE:
                corpus_extra[s["usuario"]] = s["respuesta"]

    print(f"[NLP] Corpus base: {len(CORPUS_BASE)} entradas")
    print(f"[NLP] Entradas de MongoDB: {len(corpus_extra)}")
    return {**CORPUS_BASE, **corpus_extra}

class ChatbotNLP:
    def __init__(self, umbral=0.2):
        self.umbral = umbral
        self.corpus = enriquecer_corpus_desde_mongodb()
        self.preguntas = list(self.corpus.keys())
        self.respuestas = list(self.corpus.values())

        self.vec = TfidfVectorizer(
            tokenizer=pipeline_nlp,
            token_pattern=None,
            lowercase=False
        )
        self.matriz = self.vec.fit_transform(self.preguntas)
        print(f"[NLP] Modelo entrenado. Vocabulario: {len(self.vec.vocabulary_)} terminos")

    def responder(self, pregunta_raw):
        """Busca la mejor coincidencia y guarda en MongoDB."""
        vec_usr = self.vec.transform([pregunta_raw])
        sims = cosine_similarity(vec_usr, self.matriz)[0]
        idx = int(np.argmax(sims))
        mejor_sim = float(sims[idx])

        print(f"  [NLP] Similitud: {mejor_sim:.3f} (umbral: {self.umbral})")
        reconocido = mejor_sim >= self.umbral

        if reconocido:
            respuesta = self.respuestas[idx]
            metodo = f"tfidf_cosine_{mejor_sim:.2f}"
        else:
            respuesta = (f"No encontre una respuesta adecuada (similitud maxima: {mejor_sim:.2f}). "
                         "Tu pregunta queda registrada.")
            metodo = "sin_match_nlp"

        # Guardar en MongoDB con la puntuacion de similitud
        guardar_sesion(
            fase="s2",
            usuario_raw=pregunta_raw,
            usuario_norm=pregunta_raw.lower().strip(),
            respuesta=respuesta,
            reconocido=reconocido,
            similitud=round(mejor_sim, 4),
            metodo=metodo
        )

        return respuesta

if __name__ == "__main__":
    bot = ChatbotNLP(umbral=0.2)
    print("\nChatbot NLP activo. 'stats' para estadisticas, 'salir' para terminar.\n")

    while True:
        entrada = input("Tu: ").strip()
        if not entrada:
            continue
        if entrada.lower() == "salir":
            print(estadisticas())
            break
        if entrada.lower() == "stats":
            print(estadisticas())
            continue

        print(f"Bot: {bot.responder(entrada)}\n")
