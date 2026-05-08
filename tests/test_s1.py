import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from chatbot_s1 import normalizar, buscar

def test_normalizar_minusculas():
    assert normalizar("HOLA") == "hola"

def test_normalizar_acentos():
    assert normalizar("Cuánto cuesta?") == "cuanto cuesta"

def test_normalizar_espacios():
    assert normalizar(" hola ") == "hola"

def test_buscar_exacto():
    respuesta, metodo = buscar("hola")
    assert respuesta is not None
    assert metodo == "exacto"

def test_buscar_keyword():
    respuesta, metodo = buscar("cual es el precio de todo")
    assert respuesta is not None
    assert metodo == "keyword"

def test_buscar_desconocido():
    respuesta, metodo = buscar("xyz123abc")
    assert respuesta is None
    assert metodo is None

if __name__ == "__main__":
    tests = [test_normalizar_minusculas, test_normalizar_acentos,
             test_normalizar_espacios, test_buscar_exacto,
             test_buscar_keyword, test_buscar_desconocido]
    passed = 0
    for t in tests:
        try:
            t()
            print(f" PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f" FAIL: {t.__name__} — {e}")
            
    print(f"\n{passed}/{len(tests)} pruebas pasaron.")
