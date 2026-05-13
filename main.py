import os
import requests
import base64
from flask import Flask, request, render_template_string
from datetime import datetime

app = Flask(__name__)

# Llista global per guardar els missatges a la RAM (s'esborra si el server es reinicia)
missatges_rebuts = []

# Estructura HTML i CSS de la pàgina web
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Monitor</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #e5ddd5; margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); position: relative; }
        .header { font-weight: bold; color: #075e54; display: flex; justify-content: space-between; margin-bottom: 8px; }
        .time { font-size: 0.75em; color: #999; }
        .text { font-size: 1em; color: #333; line-height: 1.4; }
        img { max-width: 100%; border-radius: 8px; margin-top: 10px; border: 1px solid #ddd; display: block; }
        .error-msg { font-size: 0.8em; color: #d32f2f; background: #ffcdd2; padding: 5px; border-radius: 4px; margin-top: 10px; }
        h2 { text-align: center; color: #075e54; text-transform: uppercase; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📱 WhatsApp en Viu</h2>
        {% for m in missatges %}
            <div class="card">
                <div class="header">
                    <span>👤 {{ m.remetent }}</span>
                    <span class="time">{{ m.hora }}</span>
                </div>
                <div class="text">{{ m.text }}</div>
                
                {% if m.imatge %}
                    <img src="data:{{ m.content_type }};base64,{{ m.imatge }}">
                {% elif m.te_media %}
                    <div class="error-msg">⚠️ Imatge detectada però no s'ha pogut carregar (Revisa SID/Token).</div>
                {% endif %}
            </div>
        {% endfor %}
        
        {% if not missatges %}
            <p style="text-align:center; color: #666; margin-top: 50px;">Esperant missatges del Sandbox...</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # Mostrem els últims 20 missatges, el més nou a dalt
    return render_template_string(HTML_PAGE, missatges=reversed(missatges_rebuts[-20:]))

@app.route("/whatsapp", methods=['POST'])
def webhook():
    try:
        # 1. Obtenir dades de la petició de Twilio
        dades = request.values
        remetent = dades.get('From', '').replace('whatsapp:', '')
        text = dades.get('Body', '')
        num_media = int(dades.get('NumMedia', 0))
        hora = datetime.now().strftime("%H:%M:%S")
        
        imatge_b64 = None
        content_type = None
        te_media = num_media > 0

        # 2. Si hi ha una imatge, intentar descarregar-la
        if te_media:
            media_url = dades.get('MediaUrl0')
            content_type = dades.get('MediaContentType0')
            
            # Credencials per descarregar de Twilio
            sid = os.environ.get('TWILIO_ACCOUNT_SID')
            token = os.environ.get('TWILIO_AUTH_TOKEN')
            
            print(f"📥 Intentant baixar imatge per a {remetent}...")
            
            if sid and token:
                res = requests.get(media_url, auth=(sid, token))
                if res.status_code == 200:
                    imatge_b64 = base64.b64encode(res.content).decode('utf-8')
                    print("✅ Imatge processada amb èxit")
                else:
                    print(f"❌ Error Twilio: {res.status_code}")
            else:
                print("⚠️ Falten variables d'entorn (SID/Token)")

        # 3. Guardar a la llista temporal
        missatges_rebuts.append({
            "remetent": remetent,
            "text": text,
            "imatge": imatge_b64,
            "content_type": content_type,
            "hora": hora,
            "te_media": te_media
        })
        
    except Exception as e:
        print(f"💥 Error al Webhook: {e}")

    # Twilio necessita una resposta XML (encara que estigui buida)
    return "<Response></Response>", 200

if __name__ == "__main__":
    # Render ens dóna el port dinàmicament
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
