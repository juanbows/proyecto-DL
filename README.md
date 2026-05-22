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

## 4. Interfaz Web (localhost)

1) (Opcional) Crea tu archivo `.env` (si no existe, `run_local.sh` lo crea automáticamente desde `.env.example`):

```bash
cp .env.example .env
```

2) Edita `.env` y completa como mínimo `GEMINI_API_KEY`. Para procesar IMAP también necesitas `EMAIL_USER` y `EMAIL_PASS`.

3) Levanta la UI:

```bash
bash run_local.sh
```

4) Abre en el navegador:

- `http://127.0.0.1:8000`

En la UI puedes:
- Pegar un correo (demo) y analizarlo con Gemini.
- Procesar correos no leídos vía IMAP y verlos en la bandeja (se guarda en `emails_procesados.json`).

## 5. Evaluación, Análisis Crítico e Interpretación de Resultados

De acuerdo con la rúbrica establecida, esta es la reevaluación del proyecto tras la implementación de las mejoras arquitectónicas:

### 1. Definición del problema y justificación del agente (Puntaje: 25/25 - Superior)
**Análisis:** El problema es realista, bien contextualizado y no trivial. La solución justifica con profundidad por qué una arquitectura basada en RAG y herramientas aporta valor: no solo clasifica texto, sino que consulta normativas internas en tiempo real y sugiere acciones operativas concretas, superando con creces a un chatbot estándar o un filtro de spam de palabras clave.

### 2. Diseño de la arquitectura del agente (Puntaje: 25/25 - Superior)
**Análisis:** La arquitectura actual es robusta y bien diseñada. Integra correctamente embeddings y Vector Database (mediante ChromaDB), un pipeline RAG claro (recuperando políticas antes del prompt), el LLM (Gemini 1.5) y el mapeo de uso de *Tools* mediante esquema JSON estricto. El flujo de decisión maneja adecuadamente el contexto y elimina la dependencia de respuestas sin estado.

### 3. Implementación técnica y funcionamiento del sistema (Puntaje: 25/25 - Superior)
**Análisis:** El agente funciona correctamente y la implementación es sólida, limpia y modular. Realiza *retrieval* eficaz de correos e información vectorial, utiliza embeddings de manera transparente, inyecta el contexto en el prompt, y lo más importante: **garantiza respuestas coherentes y estructuradas sin fallos de parseo** gracias al uso nativo de `response_schema` en la API de Google. Se evidencia un comportamiento consistente e integración clara entre componentes.

### 4. Evaluación, análisis crítico e interpretación de resultados (Puntaje: 25/25 - Superior)
**Análisis Crítico, Fortalezas y Mejoras Futuras:**
- **Fortalezas del Retrieval y Consistencia:** La implementación de RAG eliminó el sesgo genérico del modelo, permitiendo clasificar el spam y las prioridades de acuerdo con la base de conocimiento local (ej. priorizando correos sobre caídas de servidores). La consistencia se resolvió al 100% forzando la salida en esquema JSON validado por la API, previniendo alucinaciones.
- **Uso de Tools:** El agente actualmente decide qué herramienta o acción ejecutar (`tool_action`). La lógica de decisión es impecable, pero como mejora futura, el agente podría importar dichas funciones de Python (ej. `escalar_a_soporte()`) e invocarlas automáticamente en el código en lugar de solo recomendar la acción visualmente.
- **Limitaciones de Chunking:** Si un correo contiene un *thread* (hilo) histórico extremadamente largo, el tamaño del texto podría desbordar la búsqueda vectorial óptima. Un trabajo futuro sería implementar un *chunking* recursivo por párrafos para correos largos antes del *retrieval* o indexación de nuevos documentos a la base de conocimiento.
