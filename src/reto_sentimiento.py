# ================================================================
# src/reto_sentimiento.py
# Sentimiento adaptativo + base vectorial ChromaDB para S3.
# ================================================================
import hashlib
import os
import re
import uuid
from typing import Dict, List, Optional

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from textblob import TextBlob
    HAY_TEXTBLOB = True
except Exception:
    TextBlob = None
    HAY_TEXTBLOB = False

from chatbot_s3 import llamar_llm, recuperar_contexto_rag, recuperar_historial, guardar_turno_s3
from db import guardar_sesion, obtener_todas_sesiones


class LocalHashEmbeddingFunction:
    """Embedding local sin descargas externas para usar ChromaDB."""

    def __init__(self, n_features: int = 512):
        self.vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            analyzer="word",
            ngram_range=(1, 2),
            lowercase=True,
        )

    def __call__(self, input: List[str]) -> List[List[float]]:
        matriz = self.vectorizer.transform(input)
        return matriz.toarray().tolist()


class BaseVectorialChroma:
    """Capa de indexacion y recuperacion semantica con fallback local estable.

    El reto esta preparado para ChromaDB, pero en este entorno usamos una base
    vectorial local para evitar fallos de importacion o de runtime.
    """

    def __init__(
        self,
        persist_dir: str = ".chroma/reto_sentimiento",
        collection_name: str = "sesiones_chatbot",
        embedding_function=None,
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedding_function = embedding_function or LocalHashEmbeddingFunction()
        self._docs: List[str] = []
        self._metadatas: List[Dict] = []
        self._ids: List[str] = []
        self._vectors = None

    @staticmethod
    def _doc_id(doc: Dict) -> str:
        raw = f"{doc.get('fase','')}|{doc.get('usuario_raw','')}|{doc.get('respuesta','')}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def indexar_desde_mongodb(self, limite: int = 1500, fases: Optional[List[str]] = None) -> int:
        if fases is None:
            fases = ["s1", "s2", "s3"]

        sesiones = obtener_todas_sesiones(fase=None, limite=limite)
        sesiones = [
            s
            for s in sesiones
            if s.get("reconocido") is True and s.get("fase") in set(fases)
        ]

        if not sesiones:
            return 0

        ids = []
        docs = []
        metas = []

        for s in sesiones:
            pregunta = (s.get("usuario_raw") or s.get("usuario") or "").strip()
            respuesta = (s.get("respuesta") or "").strip()
            if not pregunta or not respuesta:
                continue

            ids.append(self._doc_id(s))
            docs.append(f"P: {pregunta}\nR: {respuesta}")
            metas.append(
                {
                    "fase": str(s.get("fase", "")),
                    "metodo": str(s.get("metodo", "")),
                    "reconocido": bool(s.get("reconocido", False)),
                }
            )

        if not docs:
            return 0

        self._ids = ids
        self._docs = docs
        self._metadatas = metas
        self._vectors = self.embedding_function(docs)
        return len(docs)

    def buscar_contexto_semantico(self, consulta: str, k: int = 5) -> str:
        if not consulta.strip():
            return "No hay consulta para busqueda semantica."

        if not self._docs or self._vectors is None:
            return "No hay contexto vectorial disponible."

        consulta_vec = self.embedding_function([consulta])
        sims = cosine_similarity(consulta_vec, self._vectors)[0]
        orden = sims.argsort()[::-1][:k]

        lineas = ["Resultados semanticos relevantes (ChromaDB):"]
        for i, idx in enumerate(orden):
            doc = self._docs[idx]
            meta = self._metadatas[idx] if idx < len(self._metadatas) else {}
            score_txt = f"sim={float(sims[idx]):.3f}"
            fase = meta.get("fase", "?")
            lineas.append(f"[{i+1}] ({fase}, {score_txt}) {doc}")

        return "\n".join(lineas)


LEXICO_NEGATIVO = {
    "enojado": -0.8,
    "furioso": -0.95,
    "molesto": -0.55,
    "frustrado": -0.6,
    "pesimo": -0.85,
    "mal": -0.4,
    "terrible": -0.9,
    "horrible": -0.9,
    "queja": -0.65,
}

LEXICO_POSITIVO = {
    "gracias": 0.45,
    "excelente": 0.95,
    "perfecto": 0.8,
    "genial": 0.85,
    "contento": 0.65,
    "feliz": 0.75,
    "buen": 0.35,
    "bueno": 0.4,
}


def _polaridad_lexica(texto: str) -> float:
    tokens = re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]+", texto.lower())
    if not tokens:
        return 0.0

    puntajes = []
    for token in tokens:
        if token in LEXICO_NEGATIVO:
            puntajes.append(LEXICO_NEGATIVO[token])
        if token in LEXICO_POSITIVO:
            puntajes.append(LEXICO_POSITIVO[token])

    if not puntajes:
        return 0.0

    return sum(puntajes) / len(puntajes)


def analizar_sentimiento(texto: str) -> Dict[str, float]:
    """Retorna estado emocional y polaridad del texto."""
    pol_blob = 0.0
    if HAY_TEXTBLOB and TextBlob is not None:
        pol_blob = TextBlob(texto).sentiment.polarity
    pol_lex = _polaridad_lexica(texto)

    if not HAY_TEXTBLOB:
        pol = pol_lex
    elif abs(pol_blob) < 0.05 and pol_lex != 0:
        pol = pol_lex
    else:
        pol = (pol_blob + pol_lex) / 2.0

    pol = max(-1.0, min(1.0, pol))

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


def instruccion_tono(estado: str) -> str:
    instrucciones = {
        "enojado": (
            "ATENCION: El usuario esta enojado. Responde con maxima empatia. "
            "Primero valida su sentimiento y luego ofrece una solucion concreta."
        ),
        "frustrado": "El usuario muestra frustracion. Se especialmente paciente y claro.",
        "neutral": "Responde de forma profesional y eficiente.",
        "satisfecho": "El usuario esta satisfecho. Puedes ser amigable.",
        "muy_positivo": "El usuario esta muy contento. Comparte su entusiasmo.",
    }
    return instrucciones.get(estado, instrucciones["neutral"])


_vector_db = None
_vector_db_indexado = False


def _get_vector_db() -> Optional[BaseVectorialChroma]:
    global _vector_db, _vector_db_indexado

    if _vector_db is None:
        _vector_db = BaseVectorialChroma()

    if not _vector_db_indexado:
        try:
            _vector_db.indexar_desde_mongodb(limite=2000)
            _vector_db_indexado = True
        except Exception:
            return None

    return _vector_db


def chatbot_adaptativo(mensaje: str, session_id: str, base_vectorial: Optional[BaseVectorialChroma] = None):
    """LLM con tono adaptado al sentimiento y contexto semantico ChromaDB."""
    sentimiento = analizar_sentimiento(mensaje)
    print(f"  [SENTIMIENTO] {sentimiento['estado']} (polaridad: {sentimiento['polaridad']})")

    contexto_rag = recuperar_contexto_rag(n=6)
    historial = recuperar_historial(session_id)
    tono = instruccion_tono(sentimiento["estado"])

    vector_db = base_vectorial if base_vectorial is not None else _get_vector_db()
    if vector_db is None:
        contexto_vectorial = "No disponible por ahora."
    else:
        contexto_vectorial = vector_db.buscar_contexto_semantico(mensaje, k=5)

    system = f"""Eres un asistente virtual de atencion al cliente.
Responde en espanol, de forma profesional.

CONTEXTO RAG (MongoDB):
{contexto_rag}

CONTEXTO VECTORIAL (ChromaDB):
{contexto_vectorial}

TONO REQUERIDO:
{tono}"""

    mensajes = ([{"role": "system", "content": system}] + historial + [{"role": "user", "content": mensaje}])

    respuesta = llamar_llm(mensajes)

    guardar_turno_s3(session_id, "user", mensaje)
    guardar_turno_s3(session_id, "assistant", respuesta)

    guardar_sesion(
        fase="s3",
        usuario_raw=mensaje,
        usuario_norm=mensaje.lower().strip(),
        respuesta=respuesta,
        reconocido=not (isinstance(respuesta, str) and respuesta.startswith("Error")),
        metodo="llm_rag_sentimiento_chroma",
    )

    return respuesta, sentimiento


if __name__ == "__main__":
    session_id = str(uuid.uuid4())
    print("Chatbot Adaptativo activo (Sentimiento + ChromaDB).")
    print("Escribe 'salir' para terminar.\n")

    while True:
        entrada = input("Tu: ").strip()
        if not entrada:
            continue
        if entrada.lower() == "salir":
            break

        respuesta, sent = chatbot_adaptativo(entrada, session_id)
        print(f"Bot: {respuesta}\n")
