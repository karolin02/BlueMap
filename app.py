from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import psycopg2


import os
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime, timedelta
import secrets
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from authlib.integrations.flask_client import OAuth
from markupsafe import escape
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import requests



load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_FRONTEND_KEY = os.getenv("GOOGLE_GEOCODING_KEY")
sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

def validar_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[0-9]", password)
    )

# CONFIGURACIÓN----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")

csrf = CSRFProtect(app)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)



# CONFIGURACIÓN SEGURA DE COOKIES DE SESIÓN-----------------------------------------------
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['PREFERRED_URL_SCHEME'] = 'https'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")



# PERFIL USUARIO -------------------------------------------------------------------------
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "perfiles")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# CONFIGURACIÓN DE AUTENTICACIÓN OAUTH (GOOGLE)---------------------------------------------
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# validar_password----------------------------------------------------------------------------
def enviar_correo_sendgrid(destino, asunto, contenido_html):
    mensaje = Mail(
        from_email='bluemap561@gmail.com',
        to_emails=destino,
        subject=asunto,
        html_content=contenido_html
    )

    try:
        print("API KEY:", os.environ.get('SENDGRID_API_KEY'))
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(mensaje)
        print("✅ Status:", response.status_code)
        return True
    except Exception as e:
        print("❌ Error SendGrid:", e)
        return False



# DB MAPA ------------------------------------------------------------------------------
def get_db_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colonias")
    colonias = cursor.fetchall()

    cursor.execute("SELECT * FROM puntos")
    puntos = cursor.fetchall()

    conn.close()
    return colonias, puntos
#--------------------------------------------------------------------------------------
import psycopg2
import psycopg2.extras
import sqlite3

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(
            database_url,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn



#========================================================================================
#Base de datos---------------------------------------------------------------------------
#========================================================================================


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS colonias (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        lat REAL,
        lon REAL,
        horario TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        email TEXT UNIQUE,
        password TEXT,
        municipio TEXT,
        colonia TEXT,
        verificado BOOLEAN,
        token_verificacion TEXT,
        token_recuperacion TEXT,
        expiracion_token TIMESTAMP,
        imagen TEXT,
        fecha_registro TIMESTAMP,
        rol TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contactos (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        email TEXT,
        mensaje TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notificaciones (
        id SERIAL PRIMARY KEY,
        titulo TEXT,
        mensaje TEXT,
        municipio TEXT,
        colonia TEXT,
        fecha TIMESTAMP,
        lat REAL,
        lng REAL
    );
    """)

    conn.commit()
    conn.close()

    #-----------------------------------------------------------------------------------
def insertar_colonias():
    colonias = [
        (2,"Colonia Centro",25.809,-100.598,"8:00 - 18:00"),
        (3,"Alfonso Martínez Domínguez",25.8068363,-100.6048764,None),
        (4,"Alta Villa",25.7904031,-100.5197683,None),
        (5,"Altrysa",25.7653498,-100.4526698,None),
        (6,"Ampliación Cerritos",25.8202523,-100.6112099,None),
        (7,"Ampliación Los Nogales",25.8027624,-100.6006544,None),
        (8,"Arana",25.801032,-100.5861995,None),
        (9,"Arbórea",25.7646882,-100.4425044,None),
        (10,"Arcos del Poniente",25.8070539,-100.5619349,None),
        (11,"Arezzo Residencial",25.7686193,-100.4688274,None),
        (12,"Atera Residencial",25.7677686,-100.469331,None),
        (13,"Aura Residencial",25.7608102,-100.4694183,None),
        (14,"Ayuccá Residencial",25.7657047,-100.4733013,None),
        (15,"Avance Popular",25.8073381,-100.6129693,None),
        (16,"Balcones de García",25.7952497,-100.6034691,None),
        (17,"Benito Juárez",25.8059422,-100.5906213,None),
        (18,"Cerradas Lumina",25.7584358,-100.4633972,None),
        (19,"Cerradas Solé",25.7691468,-100.449078,None),
        (20,"Ciudad Cumbres",25.7656524,-100.457921,None),
        (21,"Colinas del Río",25.805508,-100.6080431,None),
        (22,"Dominio Cumbres",25.7656524,-100.457921,None),
        (23,"El Fraile",25.8071675,-100.5039667,None),
        (24,"El Milagro",25.9174939,-100.8063518,None),
        (25,"El Palmital",25.8399697,-100.601358,None),
        (26,"El Porvenir",25.8871602,-100.6745687,None),
        (27,"El Temporal",25.801032,-100.5861995,None),
        (28,"Garzas y Capellanía",25.807615,-100.573434,None),
        (29,"Hacienda del Sol",25.7933789,-100.5591474,None),
        (30,"La Candelaria",25.6783333,-100.7033333,None),
        (31,"La Esperanza",25.7202803,-100.520223,None),
        (32,"La Soledad",25.7755668,-100.692176,None),
        (33,"Las Lomas",25.7692131,-100.4284482,None),
        (34,"Las Palmas",25.6660772,-100.7159389,None),
        (35,"Las Torres",25.7816686,-100.5891991,None),
        (36,"Los Cerritos",25.8277193,-100.6189515,None),
        (37,"Los Fierros",25.7124998,-100.708611,None),
        (38,"Los Nogales",25.7982755,-100.6020617,None),
        (39,"Maravillas",25.7994021,-100.6121055,None),
        (40,"Misión San Juan",25.7857118,-100.4635418,None),
        (41,"Nuevo Cerritos",25.8277193,-100.6189515,None),
        (42,"Paseo de Capellanía",25.7974492,-100.6133212,None),
        (43,"Paseo de las Minas",25.8005012,-100.5816573,None),
        (44,"Paseo de las Torres",25.7898173,-100.5978397,None),
        (45,"Portal de Lincoln",25.8041612,-100.5415654,None),
        (46,"Privada Cumbres",25.72634,-100.3487369,None),
        (47,"Privalia Cumbres",25.7660279,-100.4628392,None),
        (48,"Privalia Cumbres II",25.7660279,-100.4628392,None),
        (49,"Privalia García",25.7885965,-100.6003344,None),
        (50,"Punta Alta",25.7867178,-100.5318392,None),
        (51,"Punta Diamante",25.7913289,-100.5923781,None),
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    for c in colonias:
        cursor.execute("""
            INSERT INTO colonias (id, nombre, lat, lon, horario)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, c)

    conn.commit()
    cursor.close()
    conn.close()



    #-------------------------------------------------------------------------------------
 

#==================================================================================================
#==================================================================================================








# RUTAS PRINCIPALES ---------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route('/')
def inicio():
    return render_template('index.html')



# MAPA -----------------------------------------------------------------------------------
@app.route("/mapa")
def mapa():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()

    # 👑 ADMIN
    if session.get('rol') == 'admin':
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM colonias")
        colonias = cursor.fetchall()

        cursor.execute("""
            SELECT titulo, mensaje, lat, lng 
            FROM notificaciones
        """)
        notificaciones = cursor.fetchall()

        notificaciones = [
            [n["titulo"], n["mensaje"], n["lat"], n["lng"]]
            for n in notificaciones
        ]

        conn.close()
        return render_template(
        "mapa.html",
        colonias=colonias,
        notificaciones=notificaciones,
        google_api_key=GOOGLE_API_KEY
    )

    # 👤 USUARIO
    if session.get('municipio', '').lower().replace("í", "i") != "garcia":
        conn.close()
        return "Acceso restringido"

    # 🔥 ESTO DEBE IR DENTRO
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, lat, lon FROM colonias")
    colonias = cursor.fetchall()

    cursor.execute("""
        SELECT titulo, mensaje, lat, lng 
        FROM notificaciones
    """)
    notificaciones = cursor.fetchall()

    notificaciones = [
        [n["titulo"], n["mensaje"], n["lat"], n["lng"]]
        for n in notificaciones
    ]

    conn.close()

    return render_template(
        "mapa.html",
        colonias=colonias,
        notificaciones=notificaciones,
        google_api_key=GOOGLE_API_KEY


    )


# API ----------------------------------------------------------------------------
@app.route("/api/geocode")
def geocode():
    direccion = request.args.get("direccion")

    if not direccion:
        return {"error": "Dirección requerida"}, 400

    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": direccion,
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        print("STATUS GOOGLE:", data.get("status"))
        print("RESPUESTA COMPLETA:", data)

        if response.status_code != 200:
            return {"error": "Error externo"}, 500

        if data.get("status") != "OK":
            return {
                "error": "Dirección no encontrada",
                "google_status": data.get("status")
            }, 404

        location = data["results"][0]["geometry"]["location"]

        return {
            "lat": location["lat"],
            "lng": location["lng"]
        }

    except requests.exceptions.Timeout:
        return {"error": "Timeout externo"}, 504

    except Exception as e:
        print("ERROR:", e)
        return {"error": "Error interno"}, 500
    
#----------------------------------------------------------------------------------
from flask import jsonify
@app.route("/api/colonias")
def obtener_colonias():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT nombre, lat, lon FROM colonias")
    datos = cursor.fetchall()

    colonias = []
    for c in datos:
        colonias.append({
            "nombre": c["nombre"],
            "lat": c["lat"],
            "lng": c["lon"]
        })

    conn.close()
    return jsonify(colonias)


# CONTENIDO -----------------------------------------------------------------------
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



# REGISTRO ----------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔥 TRAER COLONIAS SIEMPRE
    cursor.execute("SELECT id, nombre FROM colonias")
    colonias = cursor.fetchall()

    if request.method == 'POST':

        nombre = escape(request.form.get('nombre', '').strip())
        email = escape(request.form.get('email', '').strip())
        password = request.form.get('password', '').strip()
        municipio = escape(request.form.get('municipio', '').strip())
        colonia = escape(request.form.get('colonia', '').strip())

        # Validar campos vacíos
        if not nombre or not email or not password or not municipio or not colonia:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("register.html", colonias=colonias)

        # Validar longitud nombre
        if len(nombre) < 3 or len(nombre) > 50:
            flash("El nombre debe tener entre 3 y 50 caracteres.", "danger")
            return render_template("register.html", colonias=colonias)

        # Validar email formato
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email) or len(email) > 100:
            flash("Correo inválido.", "danger")
            return render_template("register.html", colonias=colonias)

        # Validar contraseña fuerte
        if not validar_password(password):
            flash("La contraseña debe tener mínimo 8 caracteres, una mayúscula y un número.", "danger")
            return render_template("register.html", colonias=colonias)

        # Validar municipio permitido
        if municipio.lower() != "garcia":
            flash("Solo se permite registro en García.", "danger")
            return render_template("register.html", colonias=colonias)

        password_hash = generate_password_hash(password)
        token = secrets.token_urlsafe(32)

        try:
            cursor.execute("""
            INSERT INTO usuarios 
            (nombre, email, password, municipio, colonia, verificado, token_verificacion)
            VALUES (%s, %s, %s, %s, %s, 0, %s)
            """, (nombre, email, password_hash, municipio, colonia, token))

            conn.commit()

        
        except Exception:
            conn.rollback()
            conn.close()
            flash("El correo ya está registrado.", "danger")
            return render_template("register.html", colonias=colonias)

        conn.close()

        # Link dinámico correcto
        link_verificacion = url_for('verificar', token=token, _external=True)

       
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Arial, sans-serif;">

        <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
        <tr>
        <td align="center">

        <table width="600" cellpadding="0" cellspacing="0" 
        style="background:white; padding:30px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.05);">

            <!-- LOGO -->
            <tr>
                <td align="center">
                    <img src="https://res.cloudinary.com/dcwdpn3oj/image/upload/v1771703112/logo_aaq5hv.jpg" 
                        alt="BlueMap Logo" 
                        width="120" 
                        style="margin-bottom:20px;">
                </td>
            </tr>

            <!-- TITULO -->
            <tr>
                <td align="center">
                    <h2 style="color:#245b92; margin-bottom:10px;">
                        Bienvenido a BlueMap 💧
                    </h2>
                </td>
            </tr>

            <!-- TEXTO -->
            <tr>
                <td align="center" style="color:#555; font-size:16px;">
                    Gracias por registrarte en nuestra plataforma.
                    <br><br>
                    Haz clic en el botón para verificar tu cuenta:
                </td>
            </tr>

            <!-- BOTON -->
            <tr>
                <td align="center" style="padding:25px;">
                    <a href="{link_verificacion}" 
                    style="background:#28a745; 
                            color:white; 
                            padding:14px 28px; 
                            text-decoration:none; 
                            border-radius:6px; 
                            font-weight:bold;
                            display:inline-block;">
                        Verificar cuenta
                    </a>
                </td>
            </tr>

            <!-- FOOTER -->
            <tr>
                <td align="center" style="font-size:13px; color:#999;">
                    Si no creaste esta cuenta, puedes ignorar este mensaje.
                    <br><br>
                    © 2026 BlueMap
                </td>
            </tr>

        </table>

        </td>
        </tr>
        </table>

        </body>
        </html>
        """

        enviar_correo_sendgrid(
        email,
        "Confirma tu cuenta",
        html
    )

      
        flash("Registro exitoso. Revisa tu correo para verificar tu cuenta.", "success")
        return redirect(url_for("login"))

    # 🔥 GET (cuando solo carga la página)
    conn.close()
    return render_template('register.html', colonias=colonias)
#--------------------------------------------------------------------------------------
@app.route("/terminos")
def terminos():
    return render_template("terminos.html")


@app.route("/privacidad")
def privacidad():
    return render_template("privacidad.html")

#-----------------------------------------------------------------------------------------
@app.route('/completar-registro')
def completar_registro():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT nombre FROM colonias")
    colonias = cursor.fetchall()

    conn.close()

    # datos de Google guardados en sesión
    nombre = session.get("nombre")
    correo = session.get("correo")

    return render_template(
        "completar_registro.html",
        colonias=colonias,
        nombre=nombre,
        correo=correo
    )


#------------------------------------------------------------------------------------------
@app.route('/guardar-usuario', methods=['POST'])
def guardar_usuario():

    nombre = request.form.get('nombre', '').strip()
    correo = request.form.get('correo', '').strip()
    municipio = "garcia"
    colonia = request.form.get('colonia', '').strip()

    # 🔒 Validar campos vacíos (PRIMERO)
    if not nombre or not correo or not colonia:
        flash("Todos los campos son obligatorios.", "danger")
        return redirect(url_for('completar_registro'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔒 Validar si ya existe el usuario
    cursor.execute("SELECT id FROM usuarios WHERE email=%s", (correo,))
    existe = cursor.fetchone()

    if existe:
        conn.close()
        flash("Este correo ya está registrado.", "warning")
        return redirect(url_for('login'))

    # 🔒 Validar colonia contra BD (SEGURIDAD)
    # 🔒 Validar colonia contra BD (MÁS ROBUSTO)
    cursor.execute("SELECT nombre FROM colonias WHERE LOWER(nombre)=LOWER(%s)", (colonia,))
    colonia_valida = cursor.fetchone()
        

    if not colonia_valida:
        conn.close()
        flash("Colonia inválida.", "danger")
        return redirect(url_for('completar_registro'))

    # 🔥 Insertar usuario
    password_dummy = generate_password_hash("google_user")

    cursor.execute("""
    INSERT INTO usuarios (nombre, email, password, municipio, colonia, verificado)
    VALUES (%s, %s, %s, %s, %s, 1)
    """, (nombre, correo, password_dummy, municipio, colonia))

    conn.commit()

    # 🔥 Obtener usuario recién creado
    cursor.execute("SELECT * FROM usuarios WHERE email=%s", (correo,))
    usuario = cursor.fetchone()

    conn.close()

    # 🔥 Crear sesión automática
    session['usuario_id'] = usuario["id"]
    session['usuario_nombre'] = usuario["nombre"]
    session['municipio'] = usuario["municipio"]
    session['usuario_colonia'] = usuario["colonia"]

    # 🧹 Limpiar datos de Google
    session.pop("nombre", None)
    session.pop("correo", None)

    return redirect(url_for('mapa'))

# VERIFICACIÓN --------------------------------------------------------------------------
@app.route("/verificar/<token>")
def verificar(token):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE token_verificacion = %s", (token,))
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        flash("Token inválido o expirado.", "danger")
        return redirect(url_for("login"))

    cursor.execute("""
        UPDATE usuarios
        SET verificado = 1,
            token_verificacion = NULL
       WHERE id = %s
""", (usuario["id"],))

    conn.commit()
    conn.close()

    flash("Cuenta verificada correctamente. Ahora puedes iniciar sesión.", "success")
    return redirect(url_for("login"))



# LOGIN -----------------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = escape(request.form.get('email', '').strip())
        password = request.form.get('password', '').strip()
        next_page = request.form.get("next")


        # Validar campos vacíos
        if not email or not password:
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("login"))


        # Validar formato email
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email) or len(email) > 100:
            flash("Correo inválido.", "danger")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        conn.close()


        # Verificar credenciales
        if not usuario or not check_password_hash(usuario["password"], password):
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect(url_for("login"))


        # Verificar cuenta confirmada
        if usuario["verificado"] == 0:
            flash("Debes verificar tu correo antes de iniciar sesión.", "warning")
            return redirect(url_for("login"))


        # Crear sesión
        session['usuario_id'] = usuario["id"]
        session['usuario_nombre'] = usuario["nombre"]
        session['municipio'] = usuario["municipio"]
        session['usuario_colonia'] = usuario["colonia"]
        session['rol'] = usuario.get("rol", "usuario")

        
        session['usuario_imagen'] = usuario.get("imagen")
       


        # Protección contra Open Redirect
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        return redirect(url_for("mapa"))

    return render_template("login.html")
#-----------------------------------------------------------------------------------------



# RECUPERAR CONTRASEÑA --------------------------------------------------------------------

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():

    if request.method == 'POST':

        email = escape(request.form.get('email', '').strip())


        # Validar campo vacío
        if not email:
            flash("Ingresa un correo válido.", "danger")
            return redirect(url_for('recuperar'))


        # Validar formato email
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email) or len(email) > 100:
            flash("Correo inválido.", "danger")
            return redirect(url_for('recuperar'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if usuario:
            token = secrets.token_urlsafe(32)
            expiracion = datetime.utcnow() + timedelta(minutes=30)

            cursor.execute("""
                UPDATE usuarios
                SET token_recuperacion = %s, expiracion_token = %s
               WHERE id = %s
                """, (token, expiracion, usuario["id"]))

            conn.commit()

            link = url_for('reset_password', token=token, _external=True)

            html = f"""
            <!DOCTYPE html>
            <html>
            <body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Arial, sans-serif;">

            <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
            <tr>
            <td align="center">

            <table width="600" cellpadding="0" cellspacing="0"
            style="background:white; padding:30px; border-radius:10px;">

                <!-- LOGO -->
                <tr>
                    <td align="center">
                        <img src="https://res.cloudinary.com/dcwdpn3oj/image/upload/v1771703112/logo_aaq5hv.jpg"
                            alt="BlueMap Logo"
                            width="120"
                            style="margin-bottom:20px;">
                    </td>
                </tr>

                <!-- TITULO -->
                <tr>
                    <td align="center">
                        <h2 style="color:#245b92; margin-bottom:10px;">
                            Recuperación de contraseña 💧
                        </h2>
                    </td>
                </tr>

                <!-- TEXTO -->
                <tr>
                    <td align="center" style="color:#555; font-size:16px;">
                        Recibimos una solicitud para restablecer tu contraseña.
                        <br><br>
                        Haz clic en el botón para continuar:
                    </td>
                </tr>

                <!-- BOTON -->
                <tr>
                    <td align="center" style="padding:25px;">
                        <a href="{link}"
                        style="background:#0d6efd;
                                color:white;
                                padding:14px 28px;
                                text-decoration:none;
                                border-radius:6px;
                                font-weight:bold;
                                display:inline-block;">
                            Restablecer contraseña
                        </a>
                    </td>
                </tr>

                <!-- AVISO -->
                <tr>
                    <td align="center" style="font-size:13px; color:#888;">
                        Si no solicitaste este cambio, puedes ignorar este mensaje.
                        <br><br>
                        El enlace expirará en 30 minutos.
                    </td>
                </tr>

                <!-- FOOTER -->
                <tr>
                    <td align="center" style="font-size:12px; color:#aaa; padding-top:15px;">
                        © 2026 BlueMap
                    </td>
                </tr>

            </table>

            </td>
            </tr>
            </table>

            </body>
            </html>
            """
            enviar_correo_sendgrid(
                email,
                "Recuperación de contraseña - BlueMap 💧",
                html
        )




        conn.close()



        flash("Si el correo existe, recibirás un enlace de recuperación.", "info")
        return redirect(url_for('login'))

    return render_template('recuperar.html')

        



# RESETEAR CONTRASEÑA----------------------------------------------------------------

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, expiracion_token 
        FROM usuarios 
        WHERE token_recuperacion =  %s
    """, (token,))
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        flash("Token inválido o expirado.", "danger")
        return redirect(url_for('login'))


    expiracion = usuario["expiracion_token"]

    if datetime.utcnow() > expiracion:
        conn.close()
        flash("El enlace ha expirado.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        nueva_password = request.form['password']

        if not validar_password(nueva_password):
            flash("La contraseña debe tener mínimo 8 caracteres, una mayúscula y un número.", "danger")
            return redirect(request.url)

        password_hash = generate_password_hash(nueva_password)

        cursor.execute("""
            UPDATE usuarios
            SET password = %s, token_recuperacion = NULL, expiracion_token = NULL
            WHERE id = %s
        """, (password_hash, usuario["id"]))

        conn.commit()
        conn.close()

        flash("Contraseña actualizada correctamente.", "success")
        return redirect(url_for('login'))

    conn.close()
    return render_template('reset.html')



# AGREGAR RUTAS DEL CLIENTE --------------------------------------------------------------------------
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)



@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')  # URL completa
    user_info = resp.json()

    email = user_info['email']
    nombre = user_info['name']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Revisar si ya existe el usuario
    cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        # 🔥 GUARDAR DATOS EN SESSION (NO EN BD TODAVÍA)
        session["nombre"] = nombre
        session["correo"] = email

        conn.close()

        # 🔥 REDIRIGIR AL FORMULARIO
        return redirect('/completar-registro')

    # Obtener usuario para sesión
    cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
    usuario = cursor.fetchone()
    conn.close()


    session['usuario_id'] = usuario["id"]
    session['usuario_nombre'] = usuario["nombre"]
    session['municipio'] = usuario["municipio"]
    session['usuario_colonia'] = usuario["colonia"]

    # manejar imagen de perfil (igual que login normal)
    session['usuario_imagen'] = usuario.get("imagen")

    return redirect(url_for('mapa'))


# CONTACTO FORMULARIO ----------------------------------------------------------------------
@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        mensaje = request.form.get('mensaje')

        # Validación simple
        if not nombre or not email or not mensaje:
            flash("Todos los campos son obligatorios", "danger")
            return redirect('/contacto')

        conn = get_db_connection()  
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contactos (nombre, email, mensaje)
            VALUES (%s, %s, %s)
        """, (nombre, email, mensaje))

        conn.commit()
        conn.close()

        flash("Mensaje enviado correctamente ✅", "success")
        return redirect('/contacto')

    return render_template('contacto.html')


# NOTIFICACIONES ----------------------------------------------------------------------
@app.route('/notificaciones')
def ver_notificaciones():
    if 'usuario_id' not in session:
        return redirect('/login')

    municipio = session.get('municipio', '').lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔔 TRAER NOTIFICACIONES + FECHA
    if session.get('rol') == 'admin':
        cursor.execute("""
            SELECT titulo, mensaje, STRING_AGG(colonia, ',') as colonias, MAX(fecha) as fecha
            FROM notificaciones
            GROUP BY titulo, mensaje
            ORDER BY fecha DESC
        """)
    else:
        cursor.execute("""
            SELECT titulo, mensaje, STRING_AGG(colonia, ',') as colonias, MAX(fecha) as fecha
            FROM notificaciones
            WHERE LOWER(municipio)=%s
            GROUP BY titulo, mensaje
            ORDER BY fecha DESC
        """, (municipio,))

    notificaciones = cursor.fetchall()

    # ✅ FORMATEAR FECHAS AQUÍ 👇
    notificaciones_formateadas = []

    colonia_usuario = session.get('usuario_colonia', '').lower().strip()

    for n in notificaciones:
        try:
            fecha_obj = datetime.fromisoformat(n['fecha'])
        except:
            fecha_obj = datetime.strptime(n['fecha'], "%Y-%m-%d %H:%M:%S.%f")

        fecha_formateada = fecha_obj.strftime("%d/%m/%Y %I:%M %p")

        # 🔥 convertir colonias a lista
        colonias_lista = n['colonias'].lower().split(",")

        # 🔥 verificar si coincide con el usuario
        coincide = colonia_usuario in colonias_lista

        notificaciones_formateadas.append({
            'titulo': n['titulo'],
            'mensaje': n['mensaje'],
            'colonias': n['colonias'],
            'fecha': fecha_formateada,
            'coincide': coincide
        })

    # 🔥 CONTADOR
    if session.get('rol') == 'admin':
        cursor.execute("""
            SELECT COUNT(DISTINCT titulo || mensaje)
            FROM notificaciones
        """)
    else:
        cursor.execute("""
            SELECT COUNT(DISTINCT titulo || mensaje)
            FROM notificaciones
            WHERE LOWER(municipio)=%s
        """, (municipio,))

    
    total_notificaciones = cursor.fetchone()["count"]

    conn.close()

    # ✅ MARCAR COMO VISTAS
    session['notificaciones_vistas'] = total_notificaciones

    # 🔁 IMPORTANTE: ahora mandamos las formateadas
    return render_template(
        'notificaciones.html',
        notificaciones=notificaciones_formateadas,
        total_notificaciones=total_notificaciones
    )
# SUBIR FOTO PERFIL ------------------------------------------------------------------------------

@app.route('/subir_foto', methods=['POST'])
def subir_foto():

    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if 'foto' not in request.files:
        flash("No se seleccionó imagen.", "warning")
        return redirect(url_for('perfil'))

    archivo = request.files['foto']

    if archivo.filename == '':
        flash("Archivo inválido.", "warning")
        return redirect(url_for('perfil'))


    # Validar extensión permitida
    extensiones_permitidas = ('.png', '.jpg', '.jpeg')
    if not archivo.filename.lower().endswith(extensiones_permitidas):
        flash("Formato de imagen no permitido. Solo PNG, JPG o JPEG.", "danger")
        return redirect(url_for('perfil'))


    #  Sanitizar nombre
    nombre_seguro = secure_filename(archivo.filename)
    extension = os.path.splitext(nombre_seguro)[1]


    # Guardar con nombre controlado por el sistema
    nombre_archivo = f"user_{session['usuario_id']}{extension}"
    ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)

    archivo.save(ruta)


    # Guardar en base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET imagen=%s WHERE id=%s",
        (nombre_archivo, session['usuario_id'])
    )
    conn.commit()
    conn.close()

    session['usuario_imagen'] = nombre_archivo
    flash("Foto actualizada correctamente.", "success")

    return redirect(url_for('perfil'))



# PERFIL --------------------------------------------------------------------------------
@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión.", "warning")
        return redirect(url_for('login'))

    return render_template('perfil.html')


# LOGOUT ---------------------------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))





#================================================================================================================================================
# ADMINISTRADOR  --------------------------------------------------------------------------------
@app.route('/admin')
def admin():
        if 'rol' not in session or session['rol'].lower().strip() != 'admin':
           return "Acceso restringido"
        return render_template('admin/dashboard.html')

# REGISTRO --------------------------------------------------------------------------------------

def crear_admin_si_no_existe():
    conn = get_db_connection()
    cursor = conn.cursor()

    correo = "bluemap561@gmail.com"

    cursor.execute("SELECT * FROM usuarios WHERE email=%s", (correo,))
    admin = cursor.fetchone()

    if not admin:
        password_hash = generate_password_hash("MapAD*1")

        cursor.execute("""
        INSERT INTO usuarios (nombre, email, password, municipio, colonia, verificado, rol)
        VALUES (%s, %s, %s, %s, %s, 1, 'admin')
        """, ("Admin", correo, password_hash, "García", "Centro"))

        conn.commit()
        print("✅ Admin creado automáticamente")

    conn.close()
# SESION ADMIN------------------------------------------------------------------------------------

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM usuarios 
            WHERE email=%s AND rol='admin'
        """, (correo,))

        admin = cursor.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session['rol'] = admin["rol"]
            session['usuario_id'] = admin["id"]
            session['usuario_nombre'] = admin["nombre"]

            return redirect('/admin')
        else:
            flash("Credenciales incorrectas", "danger")
            return redirect('/admin_login')

    # 🔥 ESTO FALTABA (GET)
    return render_template('admin/login.html')
# VER MENSAJES --------------------------------------------------------------------------------
@app.route('/admin/mensajes')
def admin_mensajes():
    if session.get('rol') != 'admin':
        return "Acceso restringido"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT nombre, email, mensaje, fecha FROM contactos ORDER BY id DESC")
    mensajes = cursor.fetchall()

    conn.close()

    return render_template('admin/mensajes.html', mensajes=mensajes)

# NOTIFICACIONES ADMIN ----------------------------------------------------------------
@app.route('/admin/notificaciones', methods=['GET', 'POST'])
def admin_notificaciones():
    if session.get('rol') != 'admin':
        return "Acceso restringido"

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔥 Obtener colonias SIEMPRE
    cursor.execute("SELECT id, nombre, lat, lon FROM colonias")
    colonias_db = cursor.fetchall()

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        mensaje = request.form.get('mensaje')
        mensaje = mensaje.replace("\n", "<br>")
        lat = request.form.get('lat')
        lng = request.form.get('lng')

        colonias = request.form.getlist('colonias[]')
        municipio = request.form.get('municipio', '').lower().strip()

        # 🚨 VALIDACIONES (ANTES DE INSERTAR)
        if not municipio:
            flash("Selecciona un municipio válido", "warning")
            return render_template('admin/notificaciones.html', colonias=colonias_db)

        if not colonias:
            flash("Selecciona al menos una colonia", "warning")
            return render_template('admin/notificaciones.html', colonias=colonias_db)

        # 🔥 Si selecciona "todas"
        if "todas" in colonias:
            cursor.execute("SELECT nombre FROM colonias")
            colonias = [c[0] for c in cursor.fetchall()]

        fecha = datetime.now()  # 🔥 AQUÍ SE CREA

        # 🔥 INSERT CORRECTO (UNO SOLO)
        for col in colonias:
            col = col.lower().strip()
            cursor.execute("""
            INSERT INTO notificaciones (titulo, mensaje, municipio, colonia, fecha, lat, lng)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (titulo, mensaje, municipio, col, fecha, lat, lng))

        conn.commit()
        flash("Notificación enviada ✅", "success")

        conn.close()
        return redirect(url_for('admin_notificaciones'))  
    
    cursor.execute("""
    SELECT id, titulo, mensaje, municipio, colonia, fecha, lat, lng
    FROM notificaciones 
    ORDER BY fecha DESC
    """)
    notificaciones = cursor.fetchall()

    conn.close()

    return render_template(
        'admin/notificaciones.html',
        colonias=colonias_db,
        notificaciones=notificaciones)



#--------------------------------------------------------------------------------------
@app.context_processor
def inject_notificaciones():
    if 'usuario_id' not in session:
        return dict(nuevas_notificaciones=0)

    municipio = session.get('municipio', '').lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(DISTINCT titulo || mensaje)
        FROM notificaciones
        WHERE LOWER(municipio)=%s
    """, (municipio,))

    total = cursor.fetchone()["count"]
    conn.close()

    vistas = session.get('notificaciones_vistas', 0)
    nuevas = total - vistas

    if nuevas < 0:
        nuevas = 0

    return dict(nuevas_notificaciones=nuevas)


# 🔥 BORRAR NOTIFICACIÓN-------------------------------------------------------------------------------------------------------------------------
@app.route('/admin/notificaciones/borrar/<int:id>', methods=['POST'])
def borrar_notificacion(id):

    if session.get('rol') != 'admin':
        return "Acceso restringido"

    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notificaciones WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    flash("Notificación eliminada 🗑️", "success")
    return redirect(url_for('admin_notificaciones'))
# EJECUCIÓN ------------------------------------------------------------------------------
with app.app_context():
    init_db()
    insertar_colonias()
    crear_admin_si_no_existe()

if __name__ == "__main__":
  
    app.run(host="0.0.0.0", port=5000, debug=True)

  