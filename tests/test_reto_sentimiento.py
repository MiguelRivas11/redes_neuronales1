import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import reto_sentimiento


def test_analizar_sentimiento_detecta_polaridad_basica():
    neg = reto_sentimiento.analizar_sentimiento("Estoy muy enojado, pesimo servicio")
    pos = reto_sentimiento.analizar_sentimiento("Excelente atencion, estoy muy contento")

    assert neg["estado"] in ("enojado", "frustrado")
    assert neg["polaridad"] < 0
    assert pos["estado"] in ("satisfecho", "muy_positivo")
    assert pos["polaridad"] > 0


def test_base_vectorial_indexa_y_busca(monkeypatch, tmp_path):
    datos = [
        {
            "fase": "s2",
            "usuario_raw": "precio de instalacion de camaras",
            "respuesta": "La instalacion basica cuesta 1200 pesos",
            "reconocido": True,
            "metodo": "tfidf",
        },
        {
            "fase": "s1",
            "usuario_raw": "horario de atencion",
            "respuesta": "Lunes a viernes de 9 a 6",
            "reconocido": True,
            "metodo": "reglas",
        },
    ]

    monkeypatch.setattr(reto_sentimiento, "obtener_todas_sesiones", lambda fase=None, limite=1000: datos)

    db = reto_sentimiento.BaseVectorialChroma(
        persist_dir=str(tmp_path / "chroma_test"),
        collection_name="test_collection",
        embedding_function=reto_sentimiento.LocalHashEmbeddingFunction(),
    )

    total = db.indexar_desde_mongodb(limite=100)
    contexto = db.buscar_contexto_semantico("cuanto cuesta instalar camaras", k=2)

    assert total == 2
    assert "Resultados semanticos" in contexto
    assert "camaras" in contexto.lower()


def test_chatbot_adaptativo_inyecta_tono_y_contexto(monkeypatch):
    monkeypatch.setattr(reto_sentimiento, "recuperar_contexto_rag", lambda n=6: "RAG prueba")
    monkeypatch.setattr(reto_sentimiento, "recuperar_historial", lambda sid, ventana=8: [])

    capturado = {"mensajes": None, "guardados": 0}

    def fake_llamar_llm(mensajes):
        capturado["mensajes"] = mensajes
        return "Respuesta adaptativa"

    monkeypatch.setattr(reto_sentimiento, "llamar_llm", fake_llamar_llm)
    monkeypatch.setattr(reto_sentimiento, "guardar_turno_s3", lambda sid, rol, c: capturado.update(guardados=capturado["guardados"] + 1))
    monkeypatch.setattr(reto_sentimiento, "guardar_sesion", lambda **kwargs: "id")

    class FakeVectorDB:
        def buscar_contexto_semantico(self, consulta, k=5):
            return "Resultados semanticos relevantes (ChromaDB):\n[1] (s2, sim=0.77) P: precio\nR: 1000"

    respuesta, sentimiento = reto_sentimiento.chatbot_adaptativo(
        "Estoy enojado con el servicio",
        session_id="abc123",
        base_vectorial=FakeVectorDB(),
    )

    assert respuesta == "Respuesta adaptativa"
    assert sentimiento["estado"] in ("enojado", "frustrado")

    system_prompt = capturado["mensajes"][0]["content"]
    assert "TONO REQUERIDO" in system_prompt
    assert reto_sentimiento.instruccion_tono(sentimiento["estado"]) in system_prompt
    assert "CONTEXTO VECTORIAL" in system_prompt


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
