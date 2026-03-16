-- SQLite
UPDATE usuarios
SET fecha_registro = CURRENT_TIMESTAMP
WHERE fecha_registro IS NULL;