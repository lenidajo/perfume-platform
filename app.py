from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS revendedores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        ciudad TEXT,
        inversion TEXT
    )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


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

    @app.route("/")
    def home():

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM revendedores")
        total = cursor.fetchone()[0]

        conn.close()

        return render_template("index.html", total=total)

    conn.commit()
    conn.close()

    return """
    <h2>Bienvenido a la plataforma de revendedores</h2>

    <p>Tu registro fue exitoso.</p>

    <p>Ahora puedes ver el catálogo mayorista y comenzar a vender.</p>

    <br>

    <a href='https://TU_CATALOGO_GITHUB'>VER CATÁLOGO</a>

    <br><br>

    <a href='https://wa.me/573XXXXXXXXX?text=Hola%20quiero%20hacer%20mi%20primer%20pedido%20de%20perfumes'>
    HACER MI PRIMER PEDIDO
    </a>

    <br><br>

    <p>Tip: publica los perfumes en tus redes y comienza a vender hoy.</p>
    """



if __name__ == "__main__":
    init_db()
    app.run(debug=True)
