# Respuestas a Preguntas de Razonamiento - Proyecto Final Chatbots

## Semana 1: Flujo de Trabajo y Bases de Datos
**1. ¿Por qué main está protegida y solo recibe cambios via Pull Request?**
Protegemos `main` para evitar que código inestable rompa la aplicación en producción. En equipos, evita que dos desarrolladores sobrescriban el trabajo del otro. Aplica incluso trabajando solo, ya que te obliga a revisar tus propios cambios y pasar por el filtro de los tests automatizados antes de integrar el código final.

**2. ¿Qué información ves en `git log --oneline` y por qué usar commits semánticos?**
Veo el hash del commit y el mensaje estructurado (ej. `feat(s1): chatbot de reglas`). Si todos dijeran "cambios", sería imposible rastrear en qué momento introdujimos un bug o entender la evolución del proyecto sin tener que leer línea por línea cada diferencia.

**3. ¿Diferencia entre `git merge` y `git rebase`?**
`git merge` une dos ramas creando un nuevo commit de fusión (preserva el historial exacto de cuándo se ramificó). `git rebase` toma los commits de la rama actual y los "mueve" para que parezca que se crearon en la punta de la rama principal (historial lineal y más limpio, pero reescribe la historia).

**4. ¿Por qué guardamos el `usuario_raw` además del texto normalizado?**
Guardamos `usuario_raw` porque contiene la forma real en que hablan los humanos (con faltas de ortografía, emojis, puntuación). Nos sirve para entender cómo interactúa el usuario y entrenar mejor a los futuros modelos de NLP. El normalizado solo sirve computacionalmente para la búsqueda inmediata.

**5. ¿Qué pasaría si no usamos Singleton en `get_db()`?**
Si abriéramos una conexión nueva en cada `guardar_sesion()`, agotaríamos rápidamente el límite de conexiones concurrentes del tier gratuito M0 de MongoDB Atlas, provocando bloqueos, cuellos de botella y ralentizando el tiempo de respuesta del bot a varios segundos por mensaje.

---

## Semana 2: NLP y Ramificación
**6. ¿Por qué crear fase-2 desde fase-1 en lugar de desde main?**
Porque necesitamos heredar todo el código funcional (como `db.py` y `chatbot_s1.py`). Si `fase-1` aún no se ha mergeado a `main` (o si se quiere mantener el flujo de feature branches dependientes), ramificar desde `fase-1` garantiza que construimos sobre la iteración tecnológica anterior.

**7. ¿Qué descubriste al correr `analizar_s1.py`?**
Observamos una tasa de éxito cercana al 50%. Las preguntas no reconocidas más comunes eran variaciones coloquiales (ej. "¿a qué hr cierran?"). Esto guió nuestro modelo NLP a requerir tokenización y *stemming* para capturar las raíces de las palabras y no coincidencia exacta.

**8. ¿Por qué `enriquecer_corpus()` solo agrega sesiones con `reconocido: True`?**
Si agregamos preguntas no reconocidas al corpus de TF-IDF, el bot aprendería a asociar texto del usuario con respuestas basura o de error. Al agregar solo las exitosas, garantizamos que las variaciones del lenguaje humano apunten a las respuestas de negocio correctas.

**9. Consulta de MongoDB (Similitud > 0.5 en S2)**
```javascript
db.sesiones.find({
  fase: "s2", 
  similitud: { $gt: 0.5 }
}).sort({ similitud: -1 }).limit(3)
```

**10. ¿Qué pasa si rompes un test y haces push a GitHub Actions?**
El workflow falla (se pone un aspa roja ❌ en Github) y bloquea el Pull Request. Esto protege producción porque impide que un administrador haga "Merge" a `main` si el código nuevo rompió funciones que antes servían.

---

## Semana 3: LLM, RAG y Sentimiento
**11. ¿El bot recuerda la conversación anterior al usar `retomar:SESSION_ID`?**
Sí, el bot retoma el contexto perfectamente. Esto es posible gracias a los documentos generados en la colección `sesiones_s3`, donde cada turno se guarda asociado al UUID único de la sesión y se recuperan los últimos N mensajes ordenados cronológicamente por timestamp.

**12. ¿Por qué el tamaño del historial RAG importa?**
Si enviamos solo 5 conversaciones base, el modelo RAG es más preciso pero limitado. Si enviamos 50, el modelo tiene mucho conocimiento pero el *system prompt* se vuelve gigante; esto puede causar que el LLM sufra de "Lost in the middle" (olvida instrucciones del medio), se ralentice la inferencia y aumenten los costos de tokens en OpenAI.

**13. Flujo completo de datos**
`Usuario -> Input CLI -> chatbot_s3.py -> Recupera RAG de MongoDB (sesiones S1/S2) -> Recupera Historial (sesiones_s3) -> Genera Prompt -> Llama a API (Ollama/OpenAI) -> Responde a Usuario -> Guarda turno en MongoDB`.
*Podría fallar en la conexión a la DB (timeout), en la caída de Ollama (que capturamos con un try/except ConnectionError), o en la cuota límite de la API de OpenAI.*
