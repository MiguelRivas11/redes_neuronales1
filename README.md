# Proyecto Final: Arquitectura de Chatbots con IA

## 🛠️ Flujo de Trabajo en GitHub (Metodología de Ingeniería)

Este proyecto no solo se enfoca en el código de IA, sino en seguir un **flujo de trabajo profesional de ingeniería de software** evaluado estrictamente en la rúbrica:

*   **Ramas de Características (Feature Branches):** La rama `main` está protegida. Todo el desarrollo se hace en ramas separadas por fase (ej. `feature/andre-fase1`, `feature/andre-fase2`, `feature/andre-fase3`) que heredan unas de otras.
*   **Pull Requests (PRs):** La integración a la rama principal solo se realiza a través de Pull Requests documentados, permitiendo la revisión de código antes de la fusión.
*   **Commits Semánticos:** Todo el historial de Git utiliza el estándar *Conventional Commits* (ej. `feat(s1): ...`, `fix(db): ...`, `docs: ...`) para contar una historia clara de la evolución del proyecto.
*   **CI/CD con GitHub Actions:** Se cuenta con un flujo continuo automatizado. Cada *push* o *PR* levanta un servidor en la nube que ejecuta las pruebas unitarias para proteger la integridad del código.

---

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

---

## Semana 2: Entrenamiento NLP con Datos Reales

En esta segunda fase, el proyecto evolucionó de un sistema basado en reglas rígidas a un modelo adaptativo de Procesamiento de Lenguaje Natural (NLP). El objetivo principal fue hacer que el bot "aprendiera" de las interacciones reales que ocurrieron durante la Semana 1.

### 1. Análisis de Datos (`analizar_s1.py`)
*   Se creó un script para extraer y analizar las sesiones almacenadas en MongoDB.
*   Esto permitió calcular la **tasa de éxito** inicial y, más importante aún, identificar las preguntas más frecuentes que el bot de reglas estáticas no pudo responder, sirviendo como insumo para mejorar el modelo.

### 2. Pipeline NLP y Enriquecimiento de Corpus (`src/chatbot_s2.py`)
*   **Pipeline NLP:** Se implementó usando la librería `nltk`. El texto entrante pasa por tokenización, eliminación de *stopwords* en español, y *stemming* (SnowballStemmer) para reducir las palabras a su raíz.
*   **Corpus Dinámico:** A diferencia de la Fase 1, el corpus no es estático. El bot se conecta a MongoDB al arrancar, recupera todas las sesiones donde `reconocido: True` de la Fase 1, y **las integra dinámicamente a su conocimiento**.
*   **Similitud Coseno:** En lugar de buscar coincidencias exactas, el sistema utiliza `TfidfVectorizer` de `scikit-learn` para convertir el texto en matrices matemáticas y calcular la similitud del coseno entre la pregunta del usuario y el corpus, con un umbral de tolerancia (0.2).

### 3. Persistencia de Datos Mejorada
*   Se mantuvo la integración con `db.py`.
*   Ahora, cada interacción no solo guarda la pregunta y respuesta, sino que registra `fase: s2`, el método de inferencia utilizado y el puntaje matemático exacto de `similitud`.

### 4. Pruebas Unitarias NLP (`tests/test_s2.py`)
*   Se crearon pruebas para verificar que el pipeline procese correctamente el lenguaje (removiendo *stopwords* y aplicando *stemming* de forma correcta).
*   Se implementaron **Mocks** (simuladores) de la base de datos para aislar el entorno de pruebas, garantizando que el modelo pueda inicializarse y responder a pruebas sin alterar la base de datos de producción.

---

### ¿Cómo probar la Semana 2?
1. Asegúrate de instalar las nuevas dependencias de Machine Learning (`pip install nltk scikit-learn numpy`).
2. Para ver el reporte de la Semana 1, ejecuta:
   ```bash
   python analizar_s1.py
   ```
3. Para iniciar el bot inteligente con TF-IDF, ejecuta:
   ```bash
   python src/chatbot_s2.py
   ```
4. Para correr las pruebas unitarias usando *mocks*, ejecuta:
   ```bash
   python tests/test_s2.py
   ```

---

## Semana 3: LLM con RAG y Memoria Persistente

En la fase final (Semana 3), el chatbot da un salto hacia la inteligencia generativa integrando un Large Language Model (LLM) que utiliza los datos históricos de MongoDB mediante la técnica RAG (Retrieval-Augmented Generation).

### 1. RAG: Retrieval-Augmented Generation (`src/chatbot_s3.py`)
*   **Contexto Dinámico:** El LLM no utiliza conocimiento inventado o pre-entrenado para el negocio, sino que recupera de MongoDB los pares pregunta-respuesta más exitosos y seguros (con alta similitud) registrados en las Semanas 1 y 2.
*   **Inyección de Prompt:** Este conocimiento recuperado se inyecta en el *system prompt* del LLM, logrando que el bot responda con precisión a los datos del negocio sin riesgo de alucinaciones (inventar precios o fechas).

### 2. Memoria Conversacional Persistente
*   **Session ID:** A diferencia de las fases anteriores donde cada turno era aislado, ahora el chatbot genera un `session_id` único para el usuario.
*   **Recuperación de Historial:** Al enviar un mensaje, el sistema recupera los últimos `N` mensajes de la base de datos (MongoDB colección `sesiones_s3`) para enviarlos al LLM.
*   **Continuidad:** Si el usuario cierra la aplicación, puede retomarla usando su `session_id`, logrando que el LLM "recuerde" de qué estaban hablando ayer o hace unas horas.

### 3. Integración de API (OpenAI / Ollama)
*   El sistema es flexible y permite conectarse tanto a modelos locales gratuitos (`Ollama` ejecutando Llama 3) para privacidad total, como a servicios en la nube (`OpenAI API`) configurables desde el archivo `.env`.

### 4. Automatización con GitHub Actions (CI/CD)
*   **Integración Continua:** Se creó un *workflow* en `.github/workflows/ci.yml`.
*   Cada vez que se hace un `push` o `Pull Request` a GitHub, se levanta un servidor virtual de Ubuntu que instala las dependencias y ejecuta automáticamente toda la batería de pruebas (`test_s1.py`, `test_s2.py`, `test_s3.py`) protegiendo el proyecto de errores en producción.

---

### ¿Cómo probar la Semana 3?
1. Instala todas las dependencias completas del proyecto:
   ```bash
   pip install -r requirements.txt
   ```
2. (Opcional) Si usarás OpenAI, asegúrate de poner tu `OPENAI_API_KEY` en el archivo `.env`. Si usas Ollama, asegúrate de que el software de Ollama esté corriendo en tu computadora.
3. Ejecuta el Chatbot Generativo:
   ```bash
   python src/chatbot_s3.py
   ```
4. Escribe un mensaje, cierra el bot, y luego ábrelo de nuevo escribiendo `retomar:TU_SESSION_ID` para comprobar que la memoria es persistente.
