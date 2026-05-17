# Proyecto Final: Arquitectura de Chatbots con IA

## Semana 1: Chatbot de Reglas y Conexión a MongoDB

Este proyecto implementa un chatbot basado en reglas con persistencia en MongoDB Atlas. La idea principal es registrar cada interacción del usuario, responder con una base de conocimiento definida en código y dejar preparada la arquitectura para una futura fase de NLP/entrenamiento con datos reales.

### 1. Configuración del entorno y repositorio

* `.gitignore` configurado para evitar subir archivos sensibles como `.env` y carpetas de entorno virtual como `venv/` o `__pycache__/`.
* Variables de entorno gestionadas con `.env` para mantener segura la URI de MongoDB Atlas.
* Dependencias de Fase 1:
  * `pymongo`
  * `python-dotenv`
  * `playwright`
  * `beautifulsoup4`
  * `requests`

### 2. Persistencia en base de datos (`src/db.py`)

* Se centraliza la conexión a MongoDB Atlas usando `pymongo`.
* Se aplica un patrón tipo Singleton para reutilizar la misma conexión durante la ejecución.
* Funciones principales:
  * `guardar_sesion()`: Almacena cada interacción con timestamp, usuario_raw, usuario normalizado, respuesta, reconocido y método.
  * `obtener_no_reconocidos()`: Recupera preguntas no reconocidas por fase.
  * `obtener_todas_sesiones()`: Lee sesiones completas de MongoDB para análisis y enriquecimiento de corpus.
  * `estadisticas()`: Genera métricas de reconocimiento y tasa de éxito.

### 3. Lógica del chatbot S1 (`src/chatbot_s1.py`)

* El bot usa una base de reglas con respuestas definidas en diccionario `BASE`.
* Incluye 11 intenciones: hola, adios, precio, horario, dirección, servicios, mantenimiento, seguridad, gracias, password y wildcard (cafe).
* Normalización: minúsculas, eliminación de acentos y puntuación.
* Búsqueda en dos pasos: coincidencia exacta primero, luego por palabras clave.
* Todas las interacciones se guardan en MongoDB para análisis posterior.

### 4. Análisis de datos Semana 1 (`analizar_s1.py`)

* Script que consulta estadísticas de MongoDB.
* Muestra preguntas no reconocidas detectadas en S1.
* Insumo clave para diseñar el corpus de NLP de Fase 2.

Ejecutar:
```bash
python analizar_s1.py
```

---

## Semana 2: Chatbot NLP con TF-IDF y Corpus Enriquecido desde MongoDB

La Fase 2 implementa un chatbot inteligente basado en similitud TF-IDF. El corpus se enriquece automáticamente con las preguntas reales que los usuarios hicieron en S1 (las que sí fueron reconocidas), permitiendo que el modelo aprenda de datos reales de producción.

### 5. Pipeline NLP (`src/chatbot_s2.py`)

* **Tokenización + Stemming**: Procesa texto en español con NLTK.
* **Corpus Base**: 13 intenciones fijas (hola, precio, horario, etc.).
* **Enriquecimiento desde MongoDB**: Lee sesiones de S1 reconocidas y las agrega al corpus.
* **TF-IDF**: Entrena modelo de similitud con el corpus combinado.
* **Cosine Similarity**: Encuentra la respuesta más parecida a la pregunta del usuario.
* **Similitud guardada**: Cada interacción S2 se registra en MongoDB con su puntuación de similitud (0.0 a 1.0).

### 6. Clase ChatbotNLP

Parámetro `umbral` (default 0.2):
- Si similitud >= umbral: pregunta reconocida.
- Si similitud < umbral: pregunta no reconocida pero registrada para mejora futura.

Método `responder()`:
- Busca la mejor coincidencia TF-IDF.
- Guarda en MongoDB con método, similitud y fase.
- Devuelve respuesta con explicación si no fue reconocida.

### 7. Requisitos de ejecución

Python 3.10 o superior + dependencias completas:

```bash
pip install pymongo python-dotenv nltk numpy scikit-learn
```

Opcionales (solo para S1):
```bash
pip install playwright beautifulsoup4 requests
```

### 8. Cómo ejecutar

**Chatbot S1 (Reglas):**
```bash
python src/chatbot_s1.py
```

**Chatbot S2 (NLP + MongoDB):**
```bash
python src/chatbot_s2.py
```

**Análisis de datos:**
```bash
python analizar_s1.py
```

**Pruebas unitarias:**
```bash
pytest tests/
```

### 9. Configuración requerida

Crear archivo `.env` en la raíz:
```env
MONGODB_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/?retryWrites=true&w=majority
```

### 10. Flujo de datos S1 → S2 → S3 (RAG futuro)

1. **S1**: Usuario pregunta → Reglas → Respuesta guardada + reconocido (True/False)
2. **S2**: Preguntas reconocidas de S1 enriquecen el corpus → TF-IDF entrena → Nueva pregunta busca similitud en corpus enriquecido
3. **S3 (futuro)**: Combinar S1 + S2 como contexto para un modelo RAG que genere respuestas más naturales.

### 11. Estructura del repositorio

```
chatbot/
├── .env                    # Variables secretas (MONGODB_URI)
├── .gitignore              # Ignora .env, __pycache__, .pyc, etc.
├── README.md               # Este archivo
├── playwrtite.py           # Utilidad para web scraping
├── analizar_s1.py          # Script análisis Fase 1
├── src/
│   ├── db.py               # Conexión y operaciones MongoDB
│   ├── chatbot_s1.py       # Bot basado en reglas
│   └── chatbot_s2.py       # Bot NLP con TF-IDF
└── tests/
    ├── test_s1.py          # Pruebas unitarias Fase 1
    └── test_s2.py          # Pruebas unitarias Fase 2
```

### 12. Comandos útiles en los bots

Una vez en ejecución:
- `stats`: Ver estadísticas globales de reconocimiento.
- `salir`: Terminar sesión y mostrar resumen.
- Cualquier otro texto: Se procesa según el bot (reglas o NLP).
