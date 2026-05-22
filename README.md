# Sistema de Clasificación y Gestión de Correos Basado en Agentes LLM

Este repositorio contiene la implementación de un agente de software inteligente diseñado para la automatización de la lectura, clasificación y respuesta de correos electrónicos. Utiliza el modelo generativo de Google (Gemini 1.5 Flash), bases de datos vectoriales (ChromaDB) y validación de esquemas JSON para procesar el lenguaje natural y tomar decisiones sobre la prioridad de los mensajes entrantes.

## 1. Definición del Problema y Justificación

### Contexto del Problema
En el entorno corporativo y personal moderno, la sobrecarga de información a través del correo electrónico representa una pérdida significativa de productividad. Los usuarios invierten horas filtrando correos no deseados (spam), identificando mensajes críticos y redactando respuestas repetitivas. Los filtros de spam tradicionales basados en reglas estáticas o métodos heurísticos básicos a menudo fallan al clasificar correos legítimos pero de baja prioridad.

### Justificación del Enfoque
Un enfoque tradicional no puede entender el contexto semántico de un correo para determinar si requiere atención inmediata o si puede ser delegado. El uso de un agente basado en Modelos de Lenguaje Grande (LLM) combinado con un sistema RAG (Retrieval-Augmented Generation) aporta un valor sustancial porque:
1. **Comprensión Semántica:** El LLM interpreta la intención y la urgencia real del remitente.
2. **Contexto Organizacional (RAG):** El sistema consulta políticas internas almacenadas en una base de datos vectorial para tomar decisiones alineadas con las reglas de la empresa.
3. **Generación de Respuestas y Acciones (Tools):** El agente redacta borradores de respuesta y sugiere acciones de sistema (ej. "escalar a soporte"), reduciendo drásticamente el tiempo de triaje.

## 2. Arquitectura del Agente

La arquitectura del sistema es robusta, modular y se basa en el flujo de agentes modernos con RAG:

1. **Módulo de Ingesta (Retrieval IMAP):** El agente extrae correos no leídos directamente del servidor mediante IMAP con SSL, decodificando cabeceras (RFC822) y el cuerpo del mensaje.
2. **Base de Datos Vectorial y RAG:** Se integra **ChromaDB** para mantener un *Knowledge Base* de políticas organizacionales. Antes de analizar un correo, el sistema genera un query basado en el asunto y cuerpo del correo, recuperando (retrieval) las directrices más relevantes mediante similitud de *embeddings*.
3. **Agente de Toma de Decisiones (LLM):** Utiliza Google Gemini. El texto del correo y el contexto recuperado (RAG) se inyectan en el prompt.
4. **Flujo de Salida Estructurado y Tools:** Mediante la configuración `response_schema`, se obliga al modelo a responder nativamente en un formato JSON estricto, previniendo alucinaciones de formato. Además de clasificar (`is_spam`, `priority`, `suggested_reply`), el modelo recomienda el uso de herramientas mediante la propiedad `tool_action`.
5. **Almacenamiento:** Los datos se guardan en `emails_procesados.json` para consumo por interfaces CLI o web.

## 3. Implementación Técnica y Funcionamiento del Sistema

El sistema ha sido desarrollado en Python siguiendo un diseño orientado a objetos y buenas prácticas de modularización.

- **`agent.py`**: Motor principal. Implementa `EmailAgent`, que orquesta IMAP, ChromaDB (para RAG y embeddings automáticos) y la API de Gemini (configurada con schemas y validación estricta).
- **`leer_correos.py`**: Interfaz CLI que lee el estado persistido y presenta de manera amigable las prioridades, respuestas y acciones (tools) sugeridas.
- **`index.html` y `crear_notebook.py`**: Interfaces adicionales para consumo web e interactivo.
- **`local_server.py`**: Servidor local para la interfaz web (endpoints para demo e IMAP).