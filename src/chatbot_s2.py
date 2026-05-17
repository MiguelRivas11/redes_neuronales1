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
    "hola buenas tardes": "¡Quiúbole! Bienvenido a Tortas Ahogadas El Chato.",
    "que horarios tienen abiertos": "Abrimos todos los días de 9:00 AM a 5:00 PM. ¡Puro horario de comida tapatía!",
    "a que hora cierran el local": "Cerramos a las 5:00 PM todos los días.",
    "donde estan ubicados su direccion": "Estamos en el centro de Guadalajara, a dos cuadras del Expiatorio.",
    "que venden o cual es el menu": "Tenemos tortas ahogadas (media o bien ahogada), tacos dorados y tejuino fresquecito.",
    "cuanto cuesta la torta precio": "La torta ahogada tradicional cuesta $65 pesitos.",
    "pican mucho las tortas": "Manejamos puro chile de Yahualica. Si no eres de por acá, te sugiero la media ahogada.",
    "tienen envios a domicilio": "¡Claro! Búscanos en las apps o llama al 33-1234-5678 para pasar a recoger.",
    "aceptan tarjeta de credito o debito": "Aceptamos efectivo, tarjetas y transferencias.",
    "muchas gracias adios": "¡Gracias a ti! Aquí te esperamos para que te eches una buena torta."
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
