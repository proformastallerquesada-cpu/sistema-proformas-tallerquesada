import os
os.environ["PGCLIENTENCODING"] = "utf-8"
from sqlalchemy import create_engine, text

# Conexión a tu base de datos
USUARIO = "postgres" 
CONTRASENA = "12345" 
SERVIDOR = "localhost"
PUERTO = "5432"
BASE_DE_DATOS = "sistema_proformas"

cadena_conexion = f"postgresql://{USUARIO}:{CONTRASENA}@{SERVIDOR}:{PUERTO}/{BASE_DE_DATOS}?client_encoding=utf8"
engine = create_engine(cadena_conexion)

# Borrar las tablas viejas
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS detalle_proforma CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS proformas CASCADE;"))
    conn.commit()

print("✅ ¡Tablas viejas borradas con éxito! Ya puedes volver a correr tu app.py")