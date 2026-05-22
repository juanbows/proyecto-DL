import imaplib
import email
import os
import json
from email.header import decode_header
import google.generativeai as genai

# RAG y Vector DB
import chromadb

class EmailAgent:
    def __init__(self, email_user, email_pass, gemini_api_key, imap_server="imap.gmail.com"):
        self.email_user = email_user
        self.email_pass = email_pass
        self.imap_server = imap_server
        self.mail = None
        
        # Configurar Gemini
        genai.configure(api_key=gemini_api_key)
        model_name = os.getenv("GEMINI_MODEL") or "models/gemini-flash-latest"
        self.model = genai.GenerativeModel(model_name)
        
        # Inicializar Base de Datos Vectorial para RAG
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="company_knowledge")
        self._seed_knowledge_base()

    def _seed_knowledge_base(self):
        """Puebla la base de datos vectorial con políticas de la empresa si está vacía."""
        if self.collection.count() == 0:
            policies = [
                "Política de urgencia: Todos los correos que contengan las palabras 'factura', 'pago', 'urgente' o 'caída del servidor' son de prioridad Alta.",
                "Política de spam: Los correos promocionales no solicitados de servicios SEO, desarrollo web o marketing digital se consideran SPAM.",
                "Política de respuesta: Las respuestas a clientes deben ser siempre cordiales y confirmar que su solicitud está en proceso de revisión por el equipo.",
                "Política interna: Los correos sobre actividades de integración, celebraciones o noticias generales son de prioridad Baja."
            ]
            ids = [f"pol_{i}" for i in range(len(policies))]
            # chromadb automáticamente genera embeddings usando su modelo por defecto si no se le pasa una función de embedding
            self.collection.add(documents=policies, ids=ids)
            print("Base de datos de conocimiento inicializada.")

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
        """Analiza, detecta spam, prioriza y sugiere respuestas usando Gemini y RAG."""
        results = []
        for em in emails:
            print(f"Procesando correo: {em['subject']}")
            
            analysis = self._analyze_with_gemini(em)
            
            if analysis.get("is_spam", False):
                print(f"[{em['subject']}] marcado como SPAM. Ignorando.")
                continue
                
            results.append({
                "email": em,
                "priority": analysis.get("priority", "Baja"),
                "suggested_reply": analysis.get("suggested_reply", ""),
                "action": analysis.get("tool_action", "Ninguna")
            })
            
        priority_map = {"Alta": 1, "Media": 2, "Baja": 3}
        results.sort(key=lambda x: priority_map.get(x["priority"], 3))
        
        return results

    def _analyze_with_gemini(self, email_data):
        """
        Llama a Gemini inyectando contexto de RAG y forzando salida JSON estricta.
        """
        # Retrieval-Augmented Generation (RAG): Buscar políticas relevantes
        query_text = f"Asunto: {email_data['subject']} | Cuerpo: {email_data['body']}"
        rag_results = self.collection.query(query_texts=[query_text], n_results=2)
        
        context_policies = ""
        if rag_results and "documents" in rag_results and rag_results["documents"]:
            context_policies = "\n".join(rag_results["documents"][0])

        prompt = f"""
        Actúa como un asistente ejecutivo inteligente. Analiza el siguiente correo electrónico:
        
        [CONTEXTO - POLÍTICAS DE LA EMPRESA (Usa esto para guiar tu decisión de spam, prioridad y respuesta)]
        {context_policies}
        
        [DATOS DEL CORREO]
        Remitente: {email_data['sender']}
        Asunto: {email_data['subject']}
        Cuerpo: {email_data['body']}
        """
        
        # Forzar JSON schema mediante Gemini API para evitar fallos de parseo
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=genai.protos.Schema(
                type_=genai.protos.Type.OBJECT,
                properties={
                    "is_spam": genai.protos.Schema(
                        type_=genai.protos.Type.BOOLEAN,
                        description="True si es spam según el contexto",
                    ),
                    "priority": genai.protos.Schema(
                        type_=genai.protos.Type.STRING,
                        enum=["Alta", "Media", "Baja"],
                        description="Nivel de prioridad",
                    ),
                    "suggested_reply": genai.protos.Schema(
                        type_=genai.protos.Type.STRING,
                        description="Borrador de respuesta formal",
                    ),
                    "tool_action": genai.protos.Schema(
                        type_=genai.protos.Type.STRING,
                        description="Acción a delegar: 'escalar_a_soporte', 'archivar', 'notificar_finanzas' o 'ninguna'",
                    ),
                },
                required=["is_spam", "priority", "suggested_reply", "tool_action"],
            ),
        )
        
        try:
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error consultando a Gemini: {e}")
            return {"is_spam": False, "priority": "Baja", "suggested_reply": "No se pudo generar respuesta.", "tool_action": "Ninguna"}

if __name__ == "__main__":
    print("--- Agente de Correos Iniciado ---")
    
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
                with open("emails_procesados.json", "w", encoding="utf-8") as f:
                    json.dump(processed, f, indent=2, ensure_ascii=False)
                print("¡Proceso terminado! Los resultados se han guardado en 'emails_procesados.json'.")
            else:
                print("No hay correos nuevos.")
