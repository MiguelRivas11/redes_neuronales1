# ================================================================
# tests/test_s2.py
# Pruebas unitarias para el chatbot NLP de la Fase 2.
# ================================================================
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import chatbot_s2


def test_pipeline_nlp_devuelve_tokens():
    tokens = chatbot_s2.pipeline_nlp("Hola, quiero saber el precio de los productos")
    assert isinstance(tokens, list)
    assert len(tokens) > 0


def test_enriquecer_corpus_desde_mongodb_agrega_reconocidas(monkeypatch):
    datos = [
        {"reconocido": True, "usuario": "quiero saber precios", "respuesta": "Tenemos varios planes."},
        {"reconocido": False, "usuario": "pregunta rara", "respuesta": "No se"},
    ]

    monkeypatch.setattr(chatbot_s2, "obtener_todas_sesiones", lambda fase="s1": datos)
    corpus = chatbot_s2.enriquecer_corpus_desde_mongodb()

    assert "quiero saber precios" in corpus
    assert corpus["quiero saber precios"] == "Tenemos varios planes."
    assert "pregunta rara" not in corpus


def test_responder_guarda_como_reconocido(monkeypatch):
    monkeypatch.setattr(chatbot_s2, "obtener_todas_sesiones", lambda fase="s1": [])

    registro = {}

    def fake_guardar_sesion(**kwargs):
        registro.update(kwargs)
        return "fake-id"

    monkeypatch.setattr(chatbot_s2, "guardar_sesion", fake_guardar_sesion)

    bot = chatbot_s2.ChatbotNLP(umbral=0.2)
    respuesta = bot.responder("Cual es el precio de los articulos?")

    assert isinstance(respuesta, str)
    assert registro["fase"] == "s2"
    assert registro["reconocido"] is True
    assert registro["metodo"].startswith("tfidf_cosine_")
    assert registro["similitud"] is not None


def test_responder_guarda_como_no_reconocido(monkeypatch):
    monkeypatch.setattr(chatbot_s2, "obtener_todas_sesiones", lambda fase="s1": [])

    registro = {}

    def fake_guardar_sesion(**kwargs):
        registro.update(kwargs)
        return "fake-id"

    monkeypatch.setattr(chatbot_s2, "guardar_sesion", fake_guardar_sesion)

    bot = chatbot_s2.ChatbotNLP(umbral=0.95)
    respuesta = bot.responder("comida para perros")

    assert "No encontre una respuesta adecuada" in respuesta
    assert registro["reconocido"] is False
    assert registro["metodo"] == "sin_match_nlp"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))