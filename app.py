from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

CATALOGO_URL = "https://bit.ly/SweetCatalogo"
WHATSAPP_NUMBER = "573506046792"

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
    return render_template("index.html", total=total, catalogo_url=CATALOGO_URL, whatsapp=WHATSAPP_NUMBER)

@app.route("/registro", methods=["POST"])
def registro():
    nombre = request.form["nombre"]
    ciudad = request.form["ciudad"]
    inversion = request.form["inversion"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO revendedores(nombre, ciudad, inversion) VALUES(?,?,?)",
        (nombre, ciudad, inversion)
    )
    conn.commit()
    conn.close()

    wa_message = f"Hola%2C+soy+{nombre.replace(' ', '+')}+de+{ciudad.replace(' ', '+')}+y+quiero+hacer+mi+primer+pedido+de+perfumes"

    return render_template("confirmacion.html",
        nombre=nombre,
        ciudad=ciudad,
        catalogo_url=CATALOGO_URL,
        whatsapp=WHATSAPP_NUMBER,
        wa_message=wa_message
    )

@app.route("/admin")
def admin():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, ciudad, inversion, fecha FROM revendedores ORDER BY fecha DESC")
    revendedores = cursor.fetchall()
    conn.close()
    return render_template("admin.html", revendedores=revendedores)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    
