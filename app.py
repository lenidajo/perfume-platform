from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

# ─── CONFIGURACIÓN ───────────────────────────────────────
CATALOGO_URL  = "https://lenidajo.github.io/catalogo-envases/flipbook.html"
WHATSAPP_NUM  = "573506046792"
MARCA         = "Sweet Perfumes Colombia"
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
# ─────────────────────────────────────────────────────────

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = f"""Eres la asesora virtual de {MARCA}, experta en perfumes de diseñador.

PERSONALIDAD:
- Amable, elegante y muy conocedora de perfumería de lujo
- Respuestas cortas: máximo 3-4 líneas
- Usas emojis con moderación 🌹

REGLAS ESTRICTAS:
- Solo hablas sobre perfumes y sobre {MARCA}
- Si preguntan precios o catálogo, envía el link
- Si quieren pedir, dales el link de WhatsApp
- No inventes precios ni stock
- Puedes mencionar descuento máximo del 10% si el cliente insiste mucho

RESPUESTAS CLAVE:
- Catálogo: Puedes ver todos nuestros perfumes aquí 👉 {CATALOGO_URL}
- Pedido: Para hacer tu pedido escríbenos 👉 https://wa.me/{WHATSAPP_NUM}
- Revendedor: Regístrate gratis aquí 👉 https://perfume-platform-production.up.railway.app/#revendedor

MARCAS: Dior, Chanel, Versace, YSL, Carolina Herrera, Valentino, Giorgio Armani,
Lancôme, Hugo Boss, Paco Rabanne, Dolce & Gabbana, Burberry, Gucci, Tom Ford y más."""


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revendedores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            ciudad TEXT,
            inversion TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_total_revendedores():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM revendedores")
    total = cursor.fetchone()[0]
    conn.close()
    return total


@app.route("/")
def home():
    total = get_total_revendedores()
    return render_template("index.html", total=total, catalogo_url=CATALOGO_URL, whatsapp=WHATSAPP_NUM)

@app.route("/registro", methods=["POST"])
def registro():
    nombre    = request.form["nombre"]
    ciudad    = request.form["ciudad"]
    inversion = request.form["inversion"]
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO revendedores(nombre, ciudad, inversion) VALUES(?,?,?)", (nombre, ciudad, inversion))
    conn.commit()
    conn.close()
    wa_message = f"Hola%2C+soy+{nombre.replace(' ', '+')}+de+{ciudad.replace(' ', '+')}+y+quiero+hacer+mi+primer+pedido"
    return render_template("confirmacion.html", nombre=nombre, ciudad=ciudad,
        catalogo_url=CATALOGO_URL, whatsapp=WHATSAPP_NUM, wa_message=wa_message)

@app.route("/admin")
def admin():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, ciudad, inversion, fecha FROM revendedores ORDER BY fecha DESC")
    revendedores = cursor.fetchall()
    conn.close()
    return render_template("admin.html", revendedores=revendedores)


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "¿En qué te puedo ayudar? 🌹"})
    msg_lower = user_message.lower()
    if any(w in msg_lower for w in ["catálogo", "catalogo", "tienen", "lista", "productos"]):
        return jsonify({"reply": f"Aquí está nuestro catálogo completo 👉 {CATALOGO_URL} 🌹"})
    if any(w in msg_lower for w in ["precio", "cuánto", "cuanto", "vale", "cuesta", "costo"]):
        return jsonify({"reply": f"Todos los precios están en el catálogo 👉 {CATALOGO_URL}\n¿Hay alguna fragancia que te interese? 🌹"})
    if any(w in msg_lower for w in ["pedir", "pedido", "comprar", "quiero uno", "quiero una"]):
        return jsonify({"reply": f"¡Perfecto! Escríbenos por WhatsApp 👉 https://wa.me/{WHATSAPP_NUM}?text=Hola+quiero+hacer+un+pedido 🛍️"})
    if any(w in msg_lower for w in ["revendedor", "vender", "mayorista", "negocio", "ganar"]):
        return jsonify({"reply": "¡Genial! Regístrate como revendedor 👉 https://perfume-platform-production.up.railway.app/#revendedor 💼"})
    if client:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
                temperature=0.5, max_tokens=200
            )
            return jsonify({"reply": response.choices[0].message.content})
        except Exception as e:
            print(f"Groq error: {e}")
    return jsonify({"reply": f"Escríbenos directo 👉 https://wa.me/{WHATSAPP_NUM} 🌹"})


@app.route("/webhook", methods=["GET"])
def webhook_verify():
    VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "sweet_perfumes_token")
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403

@app.route("/webhook", methods=["POST"])
def webhook_receive():
    import requests as req
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
    PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
    try:
        value = request.json["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return "ok", 200
        message = value["messages"][0]
        from_number = message["from"]
        user_text = message["text"]["body"]
        with app.test_client() as c:
            resp = c.post("/chat", json={"message": user_text}, content_type="application/json")
            bot_reply = resp.get_json()["reply"]
        req.post(
            f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages",
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp", "to": from_number, "type": "text", "text": {"body": bot_reply}}
        )
    except Exception as e:
        print(f"Webhook error: {e}")
    return "ok", 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
