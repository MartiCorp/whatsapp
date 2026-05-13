import os
import requests
import base64
from flask import Flask, request, render_template_string
from datetime import datetime

app = Flask(__name__)

missatges_rebuts = []

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Monitor</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #e5ddd5; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
        .header { font-weight: bold; color: #075e54; display: flex; justify-content: space-between; }
        img { max-width: 100%; border-radius: 5px; margin-top: 10px; display: block; }
        .debug-info { font-size: 0.7em; color: #cc0000; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align: center; color: #075e54;">📱 WhatsApp Monitor</h2>
        {% for m in missatges %}
            <div class="card">
                <div class="header">
                    <span>👤 {{ m.remetent }}</span>
                    <span style="font-size: 0.7em; color: #999;">{{ m.hora }}</span>
                </div>
                <div style="margin-top:5px;">{{ m.text }}</div>
                {% if m.imatge %}
                    <img src="data:{{ m.content_type }};base64,{{ m.imatge }}">
                {% elif m.te_media %}
                    <div class="debug-info">⚠️ Hi havia una imatge però no s'ha pogut carregar.</div>
                {% endif %}
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
        content_type = None
        te_media = num_media > 0

        if te_media:
            media_url = dades.get('MediaUrl0')
            content_type = dades.get('MediaContentType0')
            
            print(f"📥 Baixant imatge de: {media_url}")
            
            # Fem la petició per descarregar la imatge
            res = requests.get(media_url, auth=(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN')))
            
            if res.status_code == 200:
                imatge_b64 = base64.b64encode(res.content).decode('utf-8')
                print("✅ Imatge convertida a Base64 correctament")
            else:
                # Si falla sense auth, provem sense (Twilio Sandbox sovint no la demana)
                res = requests.get(media_url)
                if res.status_code == 200:
                    imatge_b64 = base64.b64encode(res.content).decode('utf-8')
                else:
                    print(f"❌ Error descarregant imatge: {res.status_code}")

        missatges_rebuts.append({
            "remetent": remetent,
            "text": text,
            "imatge": imatge_b64,
            "content_type": content_type,
            "hora": hora,
            "te_media": te_media
        })
        
    except Exception as e:
        print(f"💥 ERROR CRÍTIC: {e}")

    return "<Response></Response>", 200

@app.route('/')
def index():
    return render_template_string(HTML_PAGE, missatges=reversed(missatges_rebuts[-20:]))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
