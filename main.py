import os
from flask import Flask, request, render_template_string
import base64
from datetime import datetime

app = Flask(__name__)

# Llista per guardar els missatges a la RAM
missatges_rebuts = []

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Monitor</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #e5ddd5; margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
        .header { font-weight: bold; color: #075e54; margin-bottom: 5px; display: flex; justify-content: space-between; }
        .time { font-size: 0.7em; color: #999; }
        img { max-width: 100%; border-radius: 5px; margin-top: 10px; border: 1px solid #ddd; }
        .text { font-size: 1em; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align: center; color: #075e54;">📱 WhatsApp en Viu</h2>
        {% for m in missatges %}
            <div class="card">
                <div class="header">
                    <span>👤 {{ m.remetent }}</span>
                    <span class="time">{{ m.hora }}</span>
                </div>
                <div class="text">{{ m.text }}</div>
                {% if m.imatge %}
                    <img src="data:{{ m.content_type }};base64,{{ m.imatge }}">
                {% endif %}
            </div>
        {% endfor %}
        {% if not missatges %}
            <p style="text-align:center; color: #666;">Esperant missatges...</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # Mostrem els últims 20 missatges
    return render_template_string(HTML_PAGE, missatges=reversed(missatges_rebuts[-20:]))

@app.route("/whatsapp", methods=['POST'])
def webhook():
    import requests
    dades = request.values
    remetent = dades.get('From', '').replace('whatsapp:', '')
    text = dades.get('Body', '(Sense text)')
    num_media = int(dades.get('NumMedia', 0))
    hora = datetime.now().strftime("%H:%M:%S")
    
    imatge_b64 = None
    content_type = None

    if num_media > 0:
        media_url = dades.get('MediaUrl0')
        content_type = dades.get('MediaContentType0')
        # Descarreguem i convertim a base64 per mostrar-ho sense guardar fitxer
        res = requests.get(media_url)
        imatge_b64 = base64.b64encode(res.content).decode('utf-8')

    # Guardem a la memòria
    missatges_rebuts.append({
        "remetent": remetent,
        "text": text,
        "imatge": imatge_b64,
        "content_type": content_type,
        "hora": hora
    })

    return "<Response></Response>", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
