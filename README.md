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

