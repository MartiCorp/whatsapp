import os
import requests
import base64
from flask import Flask, request, render_template_string
from datetime import datetime

app = Flask(__name__)

# Llista per al monitor visual
missatges_rebuts = []

# URL del teu segon servidor a Render (configura-la a les variables d'entorn)
SERVIDOR_RECEPTOR_URL = os.environ.get("SERVIDOR_RECEPTOR_URL")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Orquestrador</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #e5ddd5; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
        .header { font-weight: bold; color: #075e54; display: flex; justify-content: space-between; }
        img { max-width: 100%; border-radius: 8px; margin-top: 10px; }
        .btn-pdf { background: #075e54; color: white; padding: 8px; border-radius: 5px; text-decoration: none; display: inline-block; margin-top: 10px; }
        .status { font-size: 0.7em; color: #666; margin-top: 5px; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📱 Monitor + Reenviament</h2>
        {% for m in missatges %}
            <div class="card">
                <div class="header">
                    <span>👤 {{ m.remetent }}</span>
                    <span style="font-size: 0.7em; color: #999;">{{ m.hora }}</span>
                </div>
                <div>{{ m.text }}</div>
                
                {% if m.imatge %}
                    {% if 'pdf' in m.content_type %}
                        <a href="data:{{ m.content_type }};base64,{{ m.imatge }}" download="document.pdf" class="btn-pdf">📄 Veure PDF</a>
                    {% else %}
                        <img src="data:{{ m.content_type }};base64,{{ m.imatge }}">
                    {% endif %}
                {% endif %}
                <div class="status">📡 Estat enviament: {{ m.estat_enviament }}</div>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route("/whatsapp", methods=['POST'])
def webhook():
    try:
        dades = request.values
        remetent = dades.get('From', '').replace('whatsapp:', '')
        text = dades.get('Body', '')
        num_media = int(dades.get('NumMedia', 0))
        hora = datetime.now().strftime("%H:%M:%S")
        
        imatge_b64 = None
        content_type = "text/plain"
        contingut_binari = None
        estat_enviament = "Cap fitxer per enviar"

        # 1. Si hi ha fitxer, el baixem
        if num_media > 0:
            media_url = dades.get('MediaUrl0')
            content_type = dades.get('MediaContentType0')
            sid = os.environ.get('TWILIO_ACCOUNT_SID')
            token = os.environ.get('TWILIO_AUTH_TOKEN')
            
            res = requests.get(media_url, auth=(sid, token))
            if res.status_code == 200:
                contingut_binari = res.content
                imatge_b64 = base64.b64encode(contingut_binari).decode('utf-8')
                
                # 2. ENVIAR AL SEGON SERVIDOR (POST)
                if SERVIDOR_RECEPTOR_URL:
                    try:
                        fitxers = {'file': ('arxiu', contingut_binari, content_type)}
                        dades_post = {'remetent': remetent, 'text': text}
                        r = requests.post(SERVIDOR_RECEPTOR_URL, files=fitxers, data=dades_post, timeout=10)
                        estat_enviament = f"Enviat al server ({r.status_code})"
                    except Exception as e:
                        estat_enviament = f"Error POST: {e}"
                else:
                    estat_enviament = "URL Receptor no configurada"

        # 3. Guardar per a la web local
        missatges_rebuts.append({
            "remetent": remetent,
            "text": text,
            "imatge": imatge_b64,
            "content_type": content_type,
            "hora": hora,
            "estat_enviament": estat_enviament
        })
        
    except Exception as e:
        print(f"Error: {e}")

    return "<Response></Response>", 200

@app.route('/')
def index():
    return render_template_string(HTML_PAGE, missatges=reversed(missatges_rebuts[-20:]))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
