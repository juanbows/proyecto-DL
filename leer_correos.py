import json

def leer_resultados():
    try:
        with open("emails_procesados.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
            
        if not datos:
            print("No hay correos para mostrar.")
            return

        print("\n" + "★"*50)
        print("Bandeja de Entrada - Agente IA")
        print("★"*50 + "\n")
        
        for item in datos:
            email = item.get("email", {})
            
            print(f"📌 PRIORIDAD: {item.get('priority', 'N/A')}")
            print(f"📧 DE: {email.get('sender', 'Desconocido')}")
            print(f"📝 ASUNTO: {email.get('subject', 'Sin asunto')}")
            
            respuesta = item.get("suggested_reply", "")
            if respuesta:
                print(f"💡 RESPUESTA SUGERIDA:\n{respuesta}")
                
            accion = item.get("action", "Ninguna")
            if accion != "Ninguna":
                print(f"⚙️ ACCIÓN SUGERIDA: {accion}")
            
            print("-" * 50)
            
            cuerpo = email.get("body", "").strip()
            # Mostramos un resumen del cuerpo para que no ensucie la pantalla
            if len(cuerpo) > 250:
                cuerpo = cuerpo[:250].replace('\n', ' ') + " [...]"
            
            print(f"📄 RESUMEN DEL MENSAJE:\n{cuerpo}")
            print("=" * 60 + "\n")
            
    except FileNotFoundError:
        print("El archivo 'emails_procesados.json' aún no existe. ¡Ejecuta agent.py primero!")

if __name__ == "__main__":
    leer_resultados()
