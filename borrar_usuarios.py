import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM usuarios")
conn.commit()

print("Usuarios eliminados correctamente")
