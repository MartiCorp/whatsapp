import os
import requests
from flask import Flask, request

app = Flask(__name__)

# --- CONFIGURACIÓ DE RUTES ---
SERVIDOR_OCR_URL = "https://el-teu-servidor-ocr.com/api/v1/process"
# Pots tenir una llista de clients autoritzats
CLIENTS = {
    "34600112233": {"nom": "Martí - MCorp", "funcio": "ocr_factura"},
    "34611223344": {"nom": "Gestoria Pérez", "funcio": "reenviar_email"}
}

def processar_ocr(media_url, remetent):
    """Envia el fitxer al servidor d'OCR."""
    res_media = requests.get(media_url)
    files = {'file': (f'doc_{remetent}.pdf', res_media.content)}
    try:
        r = requests.post(SERVIDOR_OCR_URL, files=files, data={'remetent': remetent})
        return r.status_code == 200
    except:
        return False

@app.route("/whatsapp", methods=['POST'])
def webhook():
    dades = request.values
    remetent = dades.get('From', '').replace('whatsapp:+', '')
    num_media = int(dades.get('NumMedia', 0))
    text_missatge = dades.get('Body', '').lower()

    # 1. Identificar el client
    client = CLIENTS.get(remetent)
    
    if not client:
        return "<Response><Message>Ho sento, aquest número no està registrat a la plataforma.</Message></Response>", 200

    # 2. Decidir acció segons el tipus de contingut
    if num_media > 0:
        media_url = dades.get('MediaUrl0')
        
        if client['funcio'] == "ocr_factura":
            # ENVIAR AL SERVIDOR OCR
            exit = processar_ocr(media_url, remetent)
            msg = "He rebut la teva factura i l'estic analitzant. Te la veuràs a FacturaDirecta en breu." if exit else "Error en connectar amb el servidor OCR."
        else:
            # ALTRES LOGIQUES (Exemple: reenviaments simples)
            msg = f"Gràcies {client['nom']}, he rebut el teu fitxer però encara no tinc configurat el reenviament."
            
    else:
        # 3. Acció si només és TEXT (Chatbot)
        msg = f"Hola {client['nom']}! Envia'm una foto d'una factura si vols que la processi."

    return f"<Response><Message>{msg}</Message></Response>", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
