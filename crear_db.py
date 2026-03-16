import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ---------------- TABLA USUARIOS ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    municipio TEXT NOT NULL,
    colonia TEXT NOT NULL,
    verificado BOOLEAN DEFAULT 0,
    token_verificacion TEXT,
    token_recuperacion TEXT,
    expiracion_token DATETIME
)
""")

# Agregar columnas nuevas a la tabla usuarios
try:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN token_recuperacion TEXT")
except sqlite3.OperationalError:
    print("⚠️ La columna token_recuperacion ya existe")

try:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN expiracion_token DATETIME")
except sqlite3.OperationalError:
    print("⚠️ La columna expiracion_token ya existe")
try:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN imagen TEXT")
except sqlite3.OperationalError:
    print("⚠️ La columna imagen ya existe")






# ---------------- TABLA COLONIAS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS colonias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    lat REAL,
    lon REAL,
    horario TEXT
)
""")

# ---------------- TABLA PUNTOS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS puntos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    lat REAL,
    lon REAL
)
""")



# ---------------- LIMPIAR DATOS (OPCIONAL) ----------------
cursor.execute("DELETE FROM colonias")
cursor.execute("DELETE FROM puntos")

# ---------------- DATOS DE EJEMPLO ----------------
cursor.execute("""
INSERT INTO colonias (nombre, lat, lon, horario)
VALUES ('Colonia Centro', 25.809, -100.598, '8:00 - 18:00')
""")

cursor.execute("""
INSERT INTO puntos (tipo, lat, lon)
VALUES ('Tinaco comunitario', 25.810, -100.597)
""")

conn.commit()
conn.close()

print("✅ Base de datos creada correctamente en:", DB_PATH)

