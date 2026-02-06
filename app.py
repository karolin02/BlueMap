from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import folium
import os
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------ CONFIGURACIÓN ------------------
app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ------------------ DB MAPA ------------------
def get_db_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colonias")
    colonias = cursor.fetchall()

    cursor.execute("SELECT * FROM puntos")
    puntos = cursor.fetchall()

    conn.close()
    return colonias, puntos

# ------------------ RUTAS PRINCIPALES ------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mapa")
def mapa():
    colonias, puntos = get_db_data()

    mapa = folium.Map(location=[25.809, -100.598], zoom_start=13)

    for c in colonias:
        folium.Marker(
            [c[2], c[3]],
            popup=f"Colonia: {c[1]}<br>Horario: {c[4]}",
            icon=folium.Icon(color="red", icon="tint")
        ).add_to(mapa)

    for p in puntos:
        folium.Marker(
            [p[2], p[3]],
            popup=f"Punto: {p[1]}",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(mapa)

    mapa.save(os.path.join(BASE_DIR, "static", "mapa_interactivo.html"))
    return render_template("mapa.html")

# ------------------ CONTENIDO ------------------
@app.route("/ahorro")
def ahorro():
    return render_template("ahorro.html")

@app.route("/cuidado")
def cuidado():
    return render_template("cuidado.html")

@app.route("/ods6")
def ods6():
    return render_template("ods6.html")

@app.route("/purificacion")
def purificacion():
    return render_template("purificacion.html")

# ------------------ REGISTRO ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",
                (nombre, email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return "⚠️ Este correo ya está registrado"
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, nombre, password FROM usuarios WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect(url_for("index"))
        else:
            return "❌ Correo o contraseña incorrectos"

    return render_template("login.html")

# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ------------------ EJECUCIÓN ------------------
if __name__ == "__main__":
    app.run(debug=True)
