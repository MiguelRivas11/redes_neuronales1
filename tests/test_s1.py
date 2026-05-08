# ================================================================
# tests/test_s1.py
# Pruebas unitarias para el chatbot de la Fase 1.
# ================================================================
import sys
import os

# Agregamos la carpeta 'src' al path para poder importar el chatbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from chatbot_s1 import normalizar, buscar
except ImportError as e:
    print(f"Error al importar el chatbot: {e}")
    sys.exit(1)

def test_normalizar_minusculas():
    assert normalizar("HOLA") == "hola"

def test_normalizar_acentos():
    # Verifica que quite acentos y el signo de interrogación
    assert normalizar("¿Cuánto cuesta?") == "cuanto cuesta"

def test_normalizar_espacios():
    assert normalizar("  hola  ") == "hola"

def test_buscar_exacto():
    respuesta, metodo = buscar("hola")
    assert respuesta is not None
    assert metodo == "exacto"

def test_buscar_keyword():
    # Verifica que detecte 'precio' dentro de una frase
    respuesta, metodo = buscar("cual es el precio de todo")
    assert respuesta is not None
    assert metodo == "keyword"

def test_buscar_desconocido():
    respuesta, metodo = buscar("xyz123abc")
    assert respuesta is None
    assert metodo is None

if __name__ == "__main__":
    print("--- Ejecutando Pruebas Unitarias - Fase 1 ---")
    tests = [
        test_normalizar_minusculas, 
        test_normalizar_acentos,
        test_normalizar_espacios, 
        test_buscar_exacto,
        test_buscar_keyword, 
        test_buscar_desconocido
    ]
    
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__}")
        except Exception as e:
            print(f"  [ERROR] {t.__name__}: {e}")

    print("-" * 45)
    print(f"Resultado final: {passed}/{len(tests)} pruebas pasaron.")
    
    if passed == len(tests):
        print("\n¡Todo listo! El bot cumple con los requisitos de la Fase 1.")
    else:
        print("\nRevisa los fallos antes de entregar.")