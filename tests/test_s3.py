import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import chatbot_s3


def test_chatbot_s3_basic(monkeypatch):
    # Mock RAG context and historial to avoid DB and LLM
    monkeypatch.setattr(chatbot_s3, 'recuperar_contexto_rag', lambda n=12: 'Pares test')
    monkeypatch.setattr(chatbot_s3, 'recuperar_historial', lambda sid, ventana=8: [])
    monkeypatch.setattr(chatbot_s3, 'llamar_llm', lambda mensajes: 'Respuesta de prueba')

    saved = {}
    def fake_guardar_sesion(**kwargs):
        saved.update(kwargs)
        return 'id'

    monkeypatch.setattr(chatbot_s3, 'guardar_sesion', fake_guardar_sesion)

    resp = chatbot_s3.chatbot_s3('Hola', session_id='s1')
    assert 'Respuesta de prueba' in resp
    assert saved.get('fase') == 's3'


if __name__ == '__main__':
    import pytest
    raise SystemExit(pytest.main([__file__]))
