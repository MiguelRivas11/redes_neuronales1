import sys

sys.path.insert(0, "src")

from db import estadisticas, get_db


def main():
    db = get_db()

    print("=" * 50)
    print("ANALISIS DE DATOS - SEMANA 1")
    print("=" * 50)

    stats = estadisticas()
    if "error" in stats:
        print(f"Error al obtener estadisticas: {stats['error']}")
        return

    total = stats.get("total", 0)
    reconocidos = stats.get("reconocidos", 0)
    no_reconocidos = stats.get("no_reconocidos", total - reconocidos)
    tasa_exito = stats.get("tasa_exito", 0)

    print(f"Total conversaciones  : {total}")
    print(f"Reconocidas           : {reconocidos}")
    print(f"No reconocidas        : {no_reconocidos}")
    print(f"Tasa de exito         : {tasa_exito}%")

    print("\nPreguntas NO reconocidas (ordenadas):")
    cursor = db["sesiones"].find(
        {"fase": "s1", "reconocido": False},
        {"usuario_raw": 1, "_id": 0},
    )

    found = False
    for doc in cursor:
        found = True
        pregunta = doc.get("usuario_raw", "<sin texto>")
        print(f"  - {pregunta}")

    if not found:
        print("  (No hay preguntas no reconocidas registradas en fase s1)")


if __name__ == "__main__":
    main()