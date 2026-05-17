# ================================================================
# tests/test_s2.py
# Pruebas unitarias para el chatbot de la Semana 2.
# ================================================================

import sys, os
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chatbot_s2 import pipeline_nlp, ChatbotNLP

def test_pipeline_nlp_stopwords():
    # 'el', 'de', 'los' son stopwords en español y deben eliminarse
    tokens = pipeline_nlp("el precio de los productos")
    assert "preci" in tokens  # stemmer.stem("precio")
    assert "el" not in tokens
    assert "de" not in tokens

def test_pipeline_nlp_stemming():
    # 'comprar' y 'comprando' podrían reducirse a la misma raíz
    tokens1 = pipeline_nlp("comprar")
    tokens2 = pipeline_nlp("comprando")
    assert tokens1 == tokens2

@mock.patch('chatbot_s2.obtener_todas_sesiones')
@mock.patch('chatbot_s2.guardar_sesion')
def test_chatbot_nlp_responder(mock_guardar, mock_obtener):
    # Simular sesiones vacías para no depender de la BD
    mock_obtener.return_value = []
    
    bot = ChatbotNLP(umbral=0.2)
    # Probar una pregunta del CORPUS_BASE
    respuesta = bot.responder("cuanto cuesta el producto")
    assert respuesta is not None
    assert "Nuestros productos" in respuesta

    # Probar algo desconocido
    respuesta_desc = bot.responder("xyz123abc")
    assert "No encontre una respuesta" in respuesta_desc

if __name__ == "__main__":
    tests = [
        test_pipeline_nlp_stopwords,
        test_pipeline_nlp_stemming,
        test_chatbot_nlp_responder
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f" PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f" FAIL: {t.__name__} — {e}")
            
    print(f"\n{passed}/{len(tests)} pruebas pasaron.")
