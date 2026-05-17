# ================================================================
# src/chatbot_s2.py
# Chatbot NLP con TF-IDF. El corpus se enriquece con datos
# reales de MongoDB generados en la Semana 1.
# ================================================================
import re

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from db import estadisticas, guardar_sesion, obtener_todas_sesiones

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)

stemmer = SnowballStemmer("spanish")
STOP_ES = set(stopwords.words("spanish"))

# ── Corpus base ─────────────────────────────────────────────────
# Este corpus inicial se AMPLIA con datos reales de MongoDB (S1).
# Incluye intenciones basicas + preguntas complejas.
CORPUS_BASE = {
    "hola": "¡Hola! Bienvenido a Gdl Secure Systems. ¿En qué podemos ayudarte hoy?",
    "adios": "Hasta luego. Mantén tus sistemas actualizados y seguros.",
    "gracias": "¡De nada! ¿Hay algo más en lo que pueda apoyarte?",
    "cuanto cuesta el producto": "Nuestros productos van de $100 a $500 MXN segun el modelo.",
    "cual es el precio de los articulos": "Nuestros productos van de $100 a $500 MXN segun el modelo.",
    "en que horario estan abiertos": "Atendemos lunes a viernes de 9am a 6pm.",
    "a que hora cierran": "Cerramos a las 6pm de lunes a viernes.",
    "donde estan ubicados": "Estamos en Av. Universidad 123, Guadalajara, Jalisco.",
    "tienen envios a domicilio": "Si, enviamos en 3-5 dias habiles a toda la republica.",
    "como puedo contactarlos": "Llama al 33-1234-5678 o escribe a info@empresa.com",
    "aceptan tarjeta de credito": "Aceptamos todas las tarjetas Visa y Mastercard.",
    "tienen garantia los productos": "Todos nuestros productos tienen 1 ano de garantia.",
    "aceptan devoluciones": "Aceptamos devoluciones en 30 dias con ticket de compra.",
}


def pipeline_nlp(texto):
    """Tokenizacion + stopwords + stemming en espanol."""
    texto = texto.lower()
    texto = re.sub(r"[^a-z\s]", " ", texto)
    tokens = word_tokenize(texto, language="spanish")
    tokens = [t for t in tokens if t not in STOP_ES and len(t) > 1]
    return [stemmer.stem(t) for t in tokens]


def enriquecer_corpus_desde_mongodb():
    """
    Lee sesiones de S1 RECONOCIDAS y las agrega al corpus.
    """
    sesiones = obtener_todas_sesiones(fase="s1")
    corpus_extra = {}

    for sesion in sesiones:
        usuario = sesion.get("usuario")
        respuesta = sesion.get("respuesta")
        if sesion.get("reconocido") and usuario and respuesta:
            if usuario not in CORPUS_BASE:
                corpus_extra[usuario] = respuesta

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
            lowercase=False,
        )
        self.matriz = self.vec.fit_transform(self.preguntas)
        print(f"[NLP] Modelo entrenado. Vocabulario: {len(self.vec.vocabulary_)} terminos")

    def responder(self, pregunta_raw):
        """Busca la mejor coincidencia y guarda el resultado en MongoDB."""
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
            respuesta = (
                f"No encontre una respuesta adecuada (similitud maxima: {mejor_sim:.2f}). "
                "Tu pregunta queda registrada."
            )
            metodo = "sin_match_nlp"

        guardar_sesion(
            fase="s2",
            usuario_raw=pregunta_raw,
            usuario_norm=pregunta_raw.lower().strip(),
            respuesta=respuesta,
            reconocido=reconocido,
            similitud=round(mejor_sim, 4),
            metodo=metodo,
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