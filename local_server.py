import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from agent import EmailAgent


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_HOST_FALLBACK = "127.0.0.1"
DEFAULT_PORT_FALLBACK = 8000

def _load_env():
    load_dotenv(str(ROOT_DIR / ".env"))
    load_dotenv(str(ROOT_DIR / ".env.example"), override=False)


def _json_response(handler: SimpleHTTPRequestHandler, status: int, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler: SimpleHTTPRequestHandler):
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _load_processed_emails():
    path = ROOT_DIR / "emails_procesados.json"
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_processed_emails(data):
    path = ROOT_DIR / "emails_procesados.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _make_agent(require_imap: bool):
    user = os.getenv("EMAIL_USER") or ""
    password = os.getenv("EMAIL_PASS") or ""
    gemini_key = os.getenv("GEMINI_API_KEY") or ""

    if not gemini_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el entorno (.env).")
    if require_imap and (not user or not password):
        raise RuntimeError("Faltan EMAIL_USER / EMAIL_PASS en el entorno (.env).")

    return EmailAgent(user, password, gemini_key)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return _json_response(self, 200, {"ok": True})

        if parsed.path == "/api/emails":
            return _json_response(self, 200, {"items": _load_processed_emails()})

        if parsed.path in ("/", ""):
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/process_sample":
            payload = _read_json_body(self)
            if payload is None:
                return _json_response(self, 400, {"error": "JSON inválido"})

            subject = (payload.get("subject") or "").strip()
            sender = (payload.get("sender") or "").strip()
            body = (payload.get("body") or "").strip()

            if not subject or not body:
                return _json_response(self, 400, {"error": "Se requiere subject y body"})

            try:
                agent = _make_agent(require_imap=False)
                analysis = agent._analyze_with_gemini(
                    {"subject": subject, "sender": sender or "Desconocido", "body": body}
                )
                return _json_response(self, 200, {"analysis": analysis})
            except Exception as e:
                return _json_response(self, 500, {"error": str(e)})

        if parsed.path == "/api/process_imap":
            payload = _read_json_body(self)
            if payload is None:
                return _json_response(self, 400, {"error": "JSON inválido"})

            limit = payload.get("limit", 30)
            try:
                limit = int(limit)
            except Exception:
                limit = 30
            limit = max(1, min(limit, 50))

            try:
                agent = _make_agent(require_imap=True)
                if not agent.connect():
                    return _json_response(self, 500, {"error": "No se pudo conectar a IMAP"})

                unread = agent.fetch_unread_emails(limit=limit)
                processed = agent.process_emails(unread) if unread else []
                _write_processed_emails(processed)
                return _json_response(self, 200, {"items": processed, "count": len(processed)})
            except Exception as e:
                return _json_response(self, 500, {"error": str(e)})

        return _json_response(self, 404, {"error": "Ruta no encontrada"})


def main():
    _load_env()
    host = os.getenv("HOST", DEFAULT_HOST_FALLBACK)
    port_raw = os.getenv("PORT", str(DEFAULT_PORT_FALLBACK))
    try:
        port = int(port_raw)
    except Exception:
        port = DEFAULT_PORT_FALLBACK

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"UI lista en http://{host}:{port}")
    print("Ctrl+C para detener.")
    server.serve_forever()


if __name__ == "__main__":
    main()
