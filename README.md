# Proyecto Final: Arquitectura de Chatbots con IA

## Semana 1: Chatbot de Reglas y Conexión a MongoDB

En esta primera fase del proyecto, se estableció la arquitectura fundamental del chatbot, enfocándonos en un modelo basado en reglas estáticas (diccionario) y asegurando la persistencia de datos en la nube. A continuación, se detalla todo lo que se implementó y cómo se cumple con cada punto de la rúbrica de la Semana 1.

### 1. Configuración del Entorno y Repositorio
*   **Archivos de configuración:** Se configuraron los archivos `.gitignore` para omitir archivos sensibles (como `.env`) y carpetas virtuales (`venv/`, `__pycache__/`).
*   **Dependencias:** Se configuró el archivo `requirements.txt` incluyendo las versiones necesarias de `pymongo`, `python-dotenv` y otras librerías necesarias para asegurar la reproducibilidad del proyecto.
*   **Variables de Entorno:** Se utilizó un archivo `.env` (no incluido en el repositorio) y un `.env.example` para gestionar la URI de conexión segura hacia MongoDB Atlas sin exponer credenciales.
*   **Control de Versiones:** Todo el trabajo se realizó en una rama específica (`feature/andre` y `fase-1`), manteniendo la rama `main` protegida, y se implementaron **commits semánticos** (ej. `feat(s1): chatbot de reglas con persistencia en MongoDB`).

### 2. Persistencia en Base de Datos (`src/db.py`)
*   **MongoDB Atlas:** Se estableció exitosamente la conexión a la base de datos alojada en la nube mediante `pymongo`.
*   **Patrón Singleton:** Para evitar sobrecargar la base de datos con conexiones simultáneas, la conexión se programó utilizando el patrón de diseño Singleton, asegurando que solo exista una instancia activa en toda la ejecución.
*   **Almacenamiento Crítico:** Se implementó la función `guardar_sesion()` encargada de registrar *cada interacción* en la colección `sesiones`. Se guardan datos vitales como la fecha (timestamp), el mensaje original (`usuario_raw`), el mensaje procesado (`usuario_norm`), la respuesta del bot, y un booleano `reconocido` para identificar si el bot entendió o no la solicitud.

### 3. Lógica del Chatbot (`src/chatbot_s1.py`)
*   **Base de Conocimiento:** Se cumplió el requisito de crear al menos 8 reglas de negocio propias. Se eligió el tema de un negocio local ("Tortas Ahogadas El Chato") y se programaron respuestas para intención de saludo, horarios, ubicación, menú, precios, entre otros.
*   **Normalización de Texto (NLP Básico):** Se creó la función `normalizar()` que limpia la entrada del usuario convirtiendo todo a minúsculas, removiendo acentos (usando transformaciones de caracteres) y eliminando signos de puntuación. Esto permite que el bot identifique las peticiones aunque el usuario escriba con errores de formato.
*   **Algoritmo de Búsqueda:** La función `buscar()` implementa dos estrategias: buscar una coincidencia exacta, y en su defecto, buscar si alguna palabra clave está contenida en la oración del usuario.
*   **Captura de "No Reconocidos":** Si un mensaje no hace *match* con el diccionario, el bot se disculpa e informa que la pregunta fue registrada. Esto es vital porque alimenta la base de datos para la Fase 2 (Entrenamiento NLP con datos reales).

### 4. Pruebas Unitarias (`tests/test_s1.py`)
*   Se creó el directorio de pruebas y se programó el script `test_s1.py`.
*   **Validación de funciones:** Se incluyeron 6 pruebas automatizadas comprobando que `normalizar()` quite acentos, ignore mayúsculas y soporte espacios redundantes, además de comprobar que `buscar()` responda bien tanto a *keywords* conocidos como a peticiones basura (textos desconocidos). Todas las pruebas corren de manera exitosa.

---

### ¿Cómo probar la Semana 1?
1. Asegúrate de tener Python 3.10 o superior y las dependencias instaladas (`pip install -r requirements.txt`).
2. Crea tu propio archivo `.env` en la raíz colocando tu `MONGODB_URI`.
3. Ejecuta el chatbot interactivo en la terminal usando el comando:
   ```bash
   python src/chatbot_s1.py
   ```
4. Para correr las pruebas unitarias, ejecuta:
   ```bash
   python tests/test_s1.py
   ```
