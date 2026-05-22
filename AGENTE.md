# Documento técnico: Agente de correos (RAG + Gemini)

Este documento describe cómo funciona el agente, cómo está armado el proyecto y cómo se ejecuta en local.

## Objetivo

El agente automatiza el triage de correos:

- Conecta a un buzón por IMAP.
- Lee correos no leídos.
- Usa un LLM (Gemini) para clasificar `spam/no spam`, `prioridad` y proponer una respuesta.
- Usa RAG (ChromaDB) para aplicar políticas internas al análisis.
- Persiste resultados estructurados en `emails_procesados.json` para consumo por CLI o interfaz web.

## Componentes y archivos

- `agent.py`: núcleo del agente (IMAP + RAG + llamada a Gemini + ordenamiento por prioridad).
- `leer_correos.py`: vista CLI de `emails_procesados.json`.
- `local_server.py`: servidor HTTP local (sirve `index.html` y expone APIs para demo e IMAP).
- `index.html`: UI estática (Tailwind por CDN) que consume APIs del servidor local.
- `crear_notebook.py` / `agente_correos.ipynb`: cuadernillo y generador de notebook para correr el flujo en entorno interactivo.
- `chroma_db/`: base persistente local de ChromaDB (se crea en runtime).
- `emails_procesados.json`: salida persistida (se crea/actualiza en runtime).

## Variables de entorno

El servidor local y el agente cargan variables en este orden:

1) `.env` (si existe)
2) `.env.example` (fallback, no pisa lo ya cargado)

Claves:

- `EMAIL_USER`: usuario (correo) para IMAP.
- `EMAIL_PASS`: contraseña de aplicación para IMAP (recomendado para Gmail).
- `GEMINI_API_KEY`: API key para Gemini.
- `GEMINI_MODEL` (opcional): modelo a usar. Por defecto: `models/gemini-flash-latest`.
- `HOST` / `PORT` (opcionales): bind del servidor local. Por defecto: `127.0.0.1:8000`.

## Flujo del agente (alto nivel)

1) **Conexión IMAP**
   - `EmailAgent.connect()` usa `imaplib.IMAP4_SSL` y `login()`.

2) **Extracción de correos no leídos**
   - `EmailAgent.fetch_unread_emails(limit)`:
     - `select("inbox")`
     - `search(None, "UNSEEN")`
     - `fetch(e_id, "(RFC822)")`
     - Decodifica asunto (`decode_header`) y extrae `sender` y `body` (texto plano si existe).

3) **RAG: recuperación de políticas**
   - En `__init__` se crea `chromadb.PersistentClient(path="./chroma_db")`.
   - Se abre/crea la colección `company_knowledge`.
   - `_seed_knowledge_base()` agrega políticas de ejemplo si la colección está vacía.
   - Para cada correo, `_analyze_with_gemini()` hace:
     - `query_text = "Asunto: ... | Cuerpo: ..."`
     - `collection.query(query_texts=[query_text], n_results=2)`
     - Concatena las políticas recuperadas como contexto.

4) **LLM: decisión y salida estructurada**
   - `EmailAgent` crea `genai.GenerativeModel(model_name)`.
   - `_analyze_with_gemini()` genera un prompt con:
     - Políticas recuperadas (RAG)
     - Remitente, asunto, cuerpo
   - Usa `genai.types.GenerationConfig` con:
     - `response_mime_type="application/json"`
     - `response_schema=genai.protos.Schema(...)` para forzar JSON estructurado.
   - El JSON esperado contiene:
     - `is_spam`: boolean
     - `priority`: `"Alta" | "Media" | "Baja"`
     - `suggested_reply`: string
     - `tool_action`: string (acción sugerida; el proyecto no ejecuta herramientas, sólo las sugiere)

5) **Post-proceso y persistencia**
   - `process_emails()` filtra spam y ordena por prioridad (Alta > Media > Baja).
   - El script principal (`if __name__ == "__main__":`) guarda resultados en `emails_procesados.json`.

## Interfaz Web (localhost)

La UI no habla directo con IMAP ni con Gemini; lo hace mediante el backend local:

- `GET /` sirve `index.html`.
- `GET /api/emails` devuelve `{ items: [...] }` leyendo `emails_procesados.json`.
- `POST /api/process_sample` analiza un correo pegado (demo) llamando al análisis LLM.
- `POST /api/process_imap` conecta por IMAP, lee `UNSEEN` y reescribe `emails_procesados.json`.

La UI tiene dos modos:

- **Demo rápida**: pegas `sender/subject/body` y obtienes el JSON del análisis.
- **Procesar IMAP**: solicita al backend procesar correos no leídos (por defecto 30) y luego refresca la bandeja.

## Cómo se armó (decisiones de diseño)

- **Persistencia simple**: `emails_procesados.json` como interfaz entre agente y vistas (CLI/UI).
- **RAG local**: ChromaDB persistente para mantener políticas en disco sin depender de un servicio externo.
- **Salida estructurada**: uso de `response_mime_type` + `response_schema` para minimizar fallos de parseo y facilitar consumo por UI.
- **Servidor sin framework**: `http.server` (stdlib) para evitar dependencias y facilitar ejecución en local.

## Limitaciones conocidas

- El paquete `google.generativeai` emite un warning de deprecación. El código funciona, pero conviene migrar a `google.genai` cuando el proyecto lo requiera.
- `EMAIL_PASS` para Gmail suele requerir contraseña de aplicación y configuración de seguridad en la cuenta.
- El agente procesa sólo texto plano (`text/plain`). Correos HTML pueden llegar sin cuerpo útil si no tienen parte texto.

## Ejecución local

1) Preparar entorno (si no existe `.env`, se crea desde `.env.example`):

```bash
cd proyecto-DL
bash run_local.sh
```

2) Abrir:

- `http://127.0.0.1:8000`

