import os
from dotenv import load_dotenv

import requests
import sqlite3
import time

load_dotenv()
API_KEY = os.getenv("GOOGLE_GEOCODING_KEY")
print("USANDO KEY:", API_KEY)

DB_PATH = "database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, nombre FROM colonias WHERE lat IS NULL")
colonias = cursor.fetchall()

for colonia in colonias:
    id_colonia = colonia[0]
    nombre = colonia[1]

    direccion = f"{nombre}, Garcia, Nuevo Leon, Mexico"

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={API_KEY}"

    response = requests.get(url)
    data = response.json()
    print(f"{nombre} → STATUS:", data.get("status"))
    print("RESPUESTA:", data)
    print("--------------")

    if respuesta["status"] == "OK":
        resultado = respuesta["results"][0]

        # ⚠ Validar si es coincidencia aproximada
        if resultado.get("partial_match"):
            print(f"⚠ {nombre} es aproximado, revisar")
            continue

        lat = resultado["geometry"]["location"]["lat"]
        lng = resultado["geometry"]["location"]["lng"]

        cursor.execute(
            "UPDATE colonias SET lat=?, lon=? WHERE id=?",
            (lat, lng, id_colonia)
        )
        conn.commit()

        print(f"✔ {nombre} actualizado")
else:
         print(f"❌ Error con {nombre}")



conn.close()