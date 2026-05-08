# Proyecto Final: Arquitectura de Chatbots con IA

## Semana 1: Chatbot de Reglas y Conexión a MongoDB

Este proyecto implementa un chatbot basado en reglas con persistencia en MongoDB Atlas. La idea principal es registrar cada interacción del usuario, responder con una base de conocimiento definida en código y dejar preparada la arquitectura para una futura fase de NLP/entrenamiento con datos reales.

### 1. Configuración del entorno y repositorio

* `.gitignore` configurado para evitar subir archivos sensibles como `.env` y carpetas de entorno virtual como `venv/` o `__pycache__/`.
* Variables de entorno gestionadas con `.env` para mantener segura la URI de MongoDB Atlas.
* Dependencias principales del proyecto:
  * `pymongo`
  * `python-dotenv`
  * `playwright`
  * `beautifulsoup4`
  * `requests`

### 2. Persistencia en base de datos (`src/db.py`)

* Se centraliza la conexión a MongoDB Atlas usando `pymongo`.
* Se aplica un patrón tipo Singleton para reutilizar la misma conexión durante la ejecución.
* La función `guardar_sesion()` almacena cada interacción en la colección `sesiones` con información como:
  * `timestamp`
  * `usuario_raw`
  * `usuario`
  * `respuesta`
  * `reconocido`
  * `metodo`
* La función `estadisticas()` genera métricas básicas sobre las sesiones registradas.

### 3. Lógica del chatbot (`src/chatbot_s1.py`)

* El bot usa una base de reglas con respuestas definidas en el diccionario `BASE`.
* Incluye al menos 8 intenciones/reglas: saludo, despedida, precio, horario, dirección, servicios, mantenimiento, seguridad, gracias y password.
* La función `normalizar()` convierte el texto a minúsculas, elimina acentos y limpia signos de puntuación para mejorar la coincidencia.
* La función `buscar()` primero intenta una coincidencia exacta y luego busca palabras clave dentro del mensaje.
* Si no encuentra coincidencia, el bot devuelve una respuesta genérica y registra el mensaje como no reconocido para análisis posterior.

### 4. Ejecución del chatbot

El bot se ejecuta desde consola y acepta comandos especiales:

* `stats` para ver estadísticas de la colección.
* `salir` para terminar la sesión.

### 5. Requisitos de ejecución

1. Tener Python 3.10 o superior.
2. Instalar las dependencias del proyecto.
3. Crear un archivo `.env` en la raíz con la variable `MONGODB_URI`.

Ejemplo de `.env`:

```env
MONGODB_URI=tu_uri_de_mongodb_atlas
```

### 6. Cómo ejecutar

Instala las dependencias:

```bash
pip install pymongo python-dotenv playwright beautifulsoup4 requests
```

Ejecuta el chatbot:

```bash
python src/chatbot_s1.py
```

### 7. Sobre los datos registrados

Cada conversación se guarda en MongoDB para analizar qué preguntas sí entiende el bot y cuáles no. Eso permite mejorar la base de reglas o usar esos datos como insumo para una siguiente fase del proyecto.

### 8. Observaciones del repositorio

* El archivo `playwrtite.py` sirve como apoyo para extraer contenido de una página web con Playwright y BeautifulSoup.
* En este momento no hay directorio de pruebas ni archivo `requirements.txt`, así que las dependencias deben instalarse manualmente o agregarse después si quieres formalizar el proyecto.
