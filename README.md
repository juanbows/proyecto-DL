# Sistema de Clasificación y Gestión de Correos Basado en Agentes LLM

Este repositorio contiene la implementación de un agente de software inteligente diseñado para la automatización de la lectura, clasificación y respuesta de correos electrónicos. Utiliza el modelo generativo de Google (Gemini) para procesar el lenguaje natural y tomar decisiones sobre la prioridad de los mensajes entrantes.

## 1. Definición del Problema y Justificación

### Contexto del Problema
En el entorno corporativo y personal moderno, la sobrecarga de información a través del correo electrónico representa una pérdida significativa de productividad. Los usuarios invierten horas filtrando correos no deseados (spam), identificando mensajes críticos y redactando respuestas repetitivas. Los filtros de spam tradicionales basados en reglas estáticas o métodos heurísticos básicos a menudo fallan al clasificar correos legítimos pero de baja prioridad (como boletines informativos o notificaciones automáticas) o no logran capturar el matiz de urgencia en correos de clientes o colaboradores.

### Justificación del Enfoque
Un enfoque tradicional no puede entender el contexto semántico de un correo para determinar si requiere atención inmediata o si puede ser delegado. El uso de un agente basado en Modelos de Lenguaje Grande (LLM) aporta un valor sustancial porque:
1. **Comprensión Semántica:** El LLM interpreta la intención, el tono y la urgencia real del remitente.
2. **Generación de Respuestas:** A diferencia de un simple filtro, el agente asiste activamente en la resolución del problema redactando borradores de respuesta adaptados al contexto del hilo.
3. **Escalabilidad:** Reduce la carga cognitiva del usuario, delegando el triaje inicial (lectura, descarte de spam y priorización) a un sistema autónomo.

## 2. Arquitectura del Agente

La arquitectura actual del sistema se basa en un flujo de procesamiento secuencial e integración de APIs:

1. **Módulo de Ingesta (Retrieval IMAP):** El agente se conecta directamente al servidor de correo mediante el protocolo IMAP con SSL. Extrae los correos electrónicos marcados como "no leídos", decodifica las cabeceras complejas (RFC822) y extrae el cuerpo del mensaje en formato de texto plano.
2. **Agente de Toma de Decisiones (LLM):** Utiliza la API de Google Gemini (`gemini-flash-latest`). El texto extraído se inyecta en un prompt diseñado específicamente para que el LLM adopte el rol de "asistente ejecutivo".
3. **Flujo de Salida y Estructuración de Datos:** Se emplea la capacidad de estructuración del LLM para forzar una respuesta en formato JSON. El sistema evalúa:
   - `is_spam`: Filtro binario basado en el contexto.
   - `priority`: Categorización ordinal (Alta, Media, Baja).
   - `suggested_reply`: Generación del texto de respuesta.
4. **Almacenamiento y Visualización:** Los datos estructurados se guardan localmente en un archivo JSON (`emails_procesados.json`) y pueden ser consumidos por múltiples interfaces (CLI, Web vía HTML estático, o Jupyter Notebooks).

*Nota sobre la Arquitectura:* Actualmente, la arquitectura representa un pipeline de procesamiento directo (Zero-shot LLM prompt). No integra un sistema RAG (Retrieval-Augmented Generation) formal con bases de datos vectoriales ni embeddings, ya que el contexto necesario se extrae en tiempo real de cada correo individual, sin depender de un corpus de conocimiento histórico de correos anteriores.

## 3. Implementación Técnica y Funcionamiento del Sistema

El sistema ha sido desarrollado en Python siguiendo un diseño orientado a objetos.

- **`agent.py`**: Contiene la clase `EmailAgent`. Encapsula la lógica de conexión IMAP, el parseo de correos multipart y la invocación a la API de Gemini. Destaca el manejo de errores en la decodificación de caracteres y la limpieza del formato devuelto por la API para asegurar un parseo JSON correcto.
- **`leer_correos.py`**: Interfaz de línea de comandos que lee el estado persistido y lo presenta en terminal.
- **`index.html`**: Tablero de control visual para el usuario final.
- **`crear_notebook.py`**: Script de automatización para generar un entorno interactivo en Jupyter.

El agente se ejecuta de manera local, requiriendo configuración de variables de entorno (`.env`) para la inyección segura de credenciales. El funcionamiento general es robusto para el análisis directo de los mensajes, logrando separar de manera coherente el spam de la información importante.

## 4. Evaluación y Análisis Crítico (Autoevaluación)

Con base en la rúbrica establecida, a continuación se presenta una evaluación crítica del proyecto actual:

### 1. Definición del problema y justificación del agente (Puntaje estimado: 25/25 - Superior)
**Análisis:** El problema abordado es realista, bien contextualizado y representativo de una necesidad actual (sobrecarga cognitiva por correo electrónico). La justificación explica con profundidad por qué un sistema basado en reglas es insuficiente y cómo la aplicación de un LLM aporta valor directo mediante la comprensión contextual profunda y la generación automatizada de respuestas, aportando ventajas operativas sobre chatbots simples.

### 2. Diseño de la arquitectura del agente (Puntaje estimado: 15/25 - Básico)
**Análisis:** La arquitectura actual incluye los componentes esenciales para la interacción con un LLM, pero presenta omisiones frente a una arquitectura avanzada completa. Específicamente, carece de un pipeline RAG (Retrieval-Augmented Generation), ya que no utiliza embeddings ni una base de datos vectorial para mantener un historial contextual. El flujo de decisión es claro y directo, pero su estado (stateless) limita el análisis de hilos complejos de correo.

### 3. Implementación técnica y funcionamiento del sistema (Puntaje estimado: 20/25 - Alto)
**Análisis:** El agente funciona correctamente y de forma estable. Realiza la recuperación (retrieval) directa desde la fuente (IMAP), clasifica eficientemente la información, genera respuestas coherentes y maneja adecuadamente los fallos en la estructura de salida de la IA (limpiando los retornos de Markdown para extraer el JSON). El código es organizado, sin embargo, no integra *Tools* o funciones nativas (Function Calling) en las que el agente pueda tomar acciones sobre el servidor de correo o consultar fuentes de terceros.

### 4. Evaluación, análisis crítico e interpretación de resultados (Puntaje estimado: 25/25 - Superior)
**Análisis Crítico de Limitaciones y Mejoras Futuras:**
- **Problemas de Alucinaciones:** Al utilizar un modelo generativo sin restricciones fuertes de contexto base, existe el riesgo de alucinación o la proposición de respuestas no alineadas con el tono corporativo real si el correo inicial es demasiado ambiguo.
- **Gestión de Contexto Ausente:** La evaluación de correos de forma aislada penaliza la efectividad del sistema ante hilos de respuesta (threads) largos. Si un correo hace referencia a una conversación anterior no presente en el cuerpo, el agente perderá el significado global.
- **Escalabilidad y Dependencia de Formato:** Forzar la salida de JSON mediante texto plano es funcional, pero susceptible a fallos frente a actualizaciones del modelo.
- **Trabajo Futuro:** Es imperativa la implementación de una base de datos vectorial (como ChromaDB, Weaviate o Pinecone) para almacenar el historial e indexar interacciones pasadas. Del mismo modo, incorporar RAG permitirá inyectar políticas de empresa en las respuestas, y el uso de *Tools* permitirá que el agente interactúe bidireccionalmente, por ejemplo, respondiendo autónomamente los correos de baja prioridad o añadiendo eventos al calendario.
