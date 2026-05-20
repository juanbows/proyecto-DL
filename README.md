# 🤖 Agente Anti-Spam IA

Este proyecto es un agente inteligente impulsado por IA (Google Gemini) diseñado para conectarse a tu bandeja de entrada, leer los correos no leídos, filtrar automáticamente el spam, asignar prioridades y sugerir borradores de respuesta.

## 📁 Estructura del Proyecto

El proyecto está compuesto por los siguientes archivos principales:

- **`agent.py`**: El script principal del agente. Se conecta al servidor IMAP de tu correo, recupera los últimos correos no leídos y utiliza la API de Gemini (`gemini-flash-latest`) para analizar su contenido. Descarta el spam y guarda los correos legítimos junto con su prioridad y sugerencia de respuesta en un archivo local llamado `emails_procesados.json`.
- **`leer_correos.py`**: Una herramienta de línea de comandos (CLI) que lee el archivo `emails_procesados.json` y muestra la información en la terminal de forma estructurada y amigable.
- **`index.html`**: Una interfaz web estática construida con Tailwind CSS. Lee localmente el archivo `emails_procesados.json` y muestra los correos, sus prioridades y respuestas en un panel visual atractivo y responsivo.
- **`crear_notebook.py`**: Un script que genera automáticamente un archivo de Jupyter Notebook (`agente_correos.ipynb`). Este notebook contiene celdas para ejecutar el agente de correos paso a paso y mostrar los resultados formateados en HTML dentro del mismo Jupyter.
- **`requirements.txt`**: Archivo que lista las dependencias de Python requeridas (`google-generativeai`, `python-dotenv`).

## 🚀 Instalación y Configuración

1. **Instalar dependencias**:
   Asegúrate de tener Python instalado y ejecuta:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuración de Credenciales**:
   Crea un archivo `.env` en la raíz del proyecto. Debes incluir tus credenciales de correo electrónico y tu clave de API de Gemini:
   ```env
   EMAIL_USER=tu_correo@gmail.com
   EMAIL_PASS=tu_contraseña_de_aplicacion
   GEMINI_API_KEY=tu_clave_de_api_de_google
   ```
   *⚠️ Nota: Si utilizas Gmail u otro proveedor con autenticación de dos factores, debes generar una "Contraseña de aplicación" específica para este script en lugar de usar tu contraseña principal.*

## 💻 ¿Cómo usarlo?

### Paso 1: Procesar Correos
Ejecuta el script principal para que el agente lea tu bandeja de entrada, consulte a la IA y clasifique los correos.
```bash
python agent.py
```
*Si hay correos nuevos, se generará/actualizará el archivo `emails_procesados.json`.*

### Paso 2: Visualizar Resultados
El proyecto te ofrece tres formas de ver los resultados:

- **Opción A: Interfaz Web (Recomendada)**
  Sirve el directorio localmente y visita la web en tu navegador:
  ```bash
  python -m http.server 8000
  ```
  Accede a `http://localhost:8000` en tu navegador para ver la bandeja de forma gráfica.

- **Opción B: En la Terminal**
  Si prefieres la consola, ejecuta:
  ```bash
  python leer_correos.py
  ```

- **Opción C: Jupyter Notebook**
  Genera el notebook ejecutando `python crear_notebook.py`. Luego puedes abrir `agente_correos.ipynb` en tu entorno de Jupyter Notebook o JupyterLab.

## 🧠 Funcionamiento de la IA

El agente realiza un único llamado a la API de Gemini por correo para optimizar tiempo y tokens. A través de un prompt diseñado para actuar como un "asistente ejecutivo", evalúa el mensaje y devuelve directamente un objeto JSON con:
- Si es `spam` o no.
- El nivel de `prioridad` (Alta, Media, Baja).
- Una `suggested_reply` profesional redactada en el mismo idioma del correo recibido.
