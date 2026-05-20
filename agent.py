import imaplib
import email
import os
import json
from email.header import decode_header
import google.generativeai as genai

# Dependencias recomendadas a instalar posteriormente:
# pip install google-generativeai python-dotenv

class EmailAgent:
    def __init__(self, email_user, email_pass, gemini_api_key, imap_server="imap.gmail.com"):
        self.email_user = email_user
        self.email_pass = email_pass
        self.imap_server = imap_server
        self.mail = None
        
        # Configurar Gemini
        genai.configure(api_key=gemini_api_key)
        # Usamos el modelo más reciente (gemini-flash-latest es excelente para tareas rápidas de texto)
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def connect(self):
        """Conecta al servidor IMAP."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_user, self.email_pass)
            print("Conectado exitosamente al correo.")
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False

    def fetch_unread_emails(self, limit=10):
        """Lee los correos no leídos."""
        self.mail.select("inbox")
        status, messages = self.mail.search(None, "UNSEEN")
        
        email_ids = messages[0].split()
        emails_data = []

        for e_id in email_ids[-limit:]:
            _, msg_data = self.mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        try:
                            # Intenta decodificar con el encoding dado, o utf-8 si no existe
                            subject = subject.decode(encoding if encoding and encoding != "unknown-8bit" else "utf-8", errors="replace")
                        except LookupError:
                            subject = subject.decode("utf-8", errors="replace")
                    
                    sender = msg.get("From")
                    body = self._get_email_body(msg)
                    
                    emails_data.append({
                        "id": e_id.decode() if isinstance(e_id, bytes) else e_id,
                        "subject": subject,
                        "sender": sender,
                        "body": body
                    })
        return emails_data

    def _get_email_body(self, msg):
        """Extrae el texto del cuerpo del correo."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode()
                    except:
                        pass
        else:
            return msg.get_payload(decode=True).decode()
        return ""

    def process_emails(self, emails):
        """Analiza, detecta spam, prioriza y sugiere respuestas usando Gemini."""
        results = []
        for em in emails:
            print(f"Procesando correo: {em['subject']}")
            
            # Realizar un único llamado a Gemini para extraer toda la información y ahorrar tiempo/tokens
            analysis = self._analyze_with_gemini(em)
            
            if analysis.get("is_spam", False):
                print(f"[{em['subject']}] marcado como SPAM. Ignorando.")
                continue
                
            results.append({
                "email": em,
                "priority": analysis.get("priority", "Baja"),
                "suggested_reply": analysis.get("suggested_reply", "")
            })
            
        # Ordenar por prioridad (Alta > Media > Baja)
        priority_map = {"Alta": 1, "Media": 2, "Baja": 3}
        results.sort(key=lambda x: priority_map.get(x["priority"], 3))
        
        return results

    def _analyze_with_gemini(self, email_data):
        """
        Llama a Gemini para evaluar si es spam, definir prioridad y crear una respuesta.
        """
        prompt = f"""
        Actúa como un asistente ejecutivo inteligente. Analiza el siguiente correo electrónico:
        
        Remitente: {email_data['sender']}
        Asunto: {email_data['subject']}
        Cuerpo: {email_data['body']}
        
        Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura (sin bloques de código extra):
        {{
            "is_spam": true o false,
            "priority": "Alta", "Media" o "Baja",
            "suggested_reply": "Un borrador de respuesta profesional en el idioma del correo, o vacío si es spam"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Limpiar posible formato markdown en la respuesta
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            return json.loads(response_text)
        except Exception as e:
            print(f"Error consultando a Gemini: {e}")
            return {"is_spam": False, "priority": "Baja", "suggested_reply": "No se pudo generar respuesta."}

if __name__ == "__main__":
    print("--- Agente de Correos Iniciado ---")
    
    # Para usarlo de forma segura, lee las variables de entorno
    # 1. Crea un archivo .env en esta carpeta
    # 2. Agrega: EMAIL_USER=tu_correo@gmail.com, EMAIL_PASS=tu_clave, GEMINI_API_KEY=tu_api_key
    
    from dotenv import load_dotenv
    load_dotenv()
    
    USER = os.getenv("EMAIL_USER")
    PASS = os.getenv("EMAIL_PASS")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    
    if not USER or not PASS or not GEMINI_KEY:
        print("Por favor, asegúrate de configurar tu .env con EMAIL_USER, EMAIL_PASS y GEMINI_API_KEY.")
    else:
        agent = EmailAgent(USER, PASS, GEMINI_KEY)
        if agent.connect():
            unread = agent.fetch_unread_emails(limit=5)
            if unread:
                processed = agent.process_emails(unread)
                # Guardar el JSON en un archivo para poder verlo
                with open("emails_procesados.json", "w", encoding="utf-8") as f:
                    json.dump(processed, f, indent=2, ensure_ascii=False)
                print("¡Proceso terminado! Los resultados se han guardado en 'emails_procesados.json'.")
            else:
                print("No hay correos nuevos.")
        else:
            print("No se pudo iniciar el agente debido a un error de conexión.")
