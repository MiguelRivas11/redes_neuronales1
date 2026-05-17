# ================================================================
# tests/test_s3.py
# Pruebas unitarias para el chatbot de la Semana 3.
# Se usan mocks para aislar la base de datos y la API del LLM.
# ================================================================

import sys, os
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chatbot_s3 import recuperar_contexto_rag, llamar_llm

@mock.patch('chatbot_s3.get_db')
def test_recuperar_contexto_vacio(mock_get_db):
    # Simular una base de datos sin historial
    mock_db = mock.MagicMock()
    mock_db["sesiones"].find().sort().limit.return_value = []
    mock_db["sesiones"].find().limit.return_value = []
    mock_get_db.return_value = mock_db
    
    contexto = recuperar_contexto_rag(n=5)
    assert contexto == "No hay historial previo disponible."

@mock.patch('chatbot_s3.requests.post')
def test_llamar_llm_ollama(mock_post):
    # Simular respuesta exitosa de la API de Ollama
    mock_response = mock.MagicMock()
    mock_response.json.return_value = {"message": {"content": "Respuesta simulada del LLM"}}
    mock_post.return_value = mock_response
    
    mensajes = [{"role": "user", "content": "hola"}]
    respuesta = llamar_llm(mensajes)
    assert respuesta == "Respuesta simulada del LLM"

if __name__ == "__main__":
    tests = [
        test_recuperar_contexto_vacio,
        test_llamar_llm_ollama
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
