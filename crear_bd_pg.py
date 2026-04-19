from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import date

Base = declarative_base()

# 1. Tabla de Productos
class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True)
    nombre = Column(String(100), nullable=False)
    precio_unitario = Column(Float, nullable=False)

# 2. Tabla de Proformas
class Proforma(Base):
    __tablename__ = 'proformas'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), unique=True, nullable=False)
    cliente = Column(String(150), nullable=False)
    fecha = Column(Date, default=date.today)
    
    # Estados
    estado_trabajo = Column(String(20), default='Pendiente') 
    estado_pago = Column(String(20), default='Pendiente')    
    
    total = Column(Float, default=0.0)
    observaciones = Column(Text, nullable=True)
    
    detalles = relationship("DetalleProforma", back_populates="proforma", cascade="all, delete-orphan")

# 3. Tabla Detalle de la Proforma
class DetalleProforma(Base):
    __tablename__ = 'detalle_proforma'
    id = Column(Integer, primary_key=True)
    proforma_id = Column(Integer, ForeignKey('proformas.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer, nullable=False)
    precio_fijado = Column(Float, nullable=False)

    proforma = relationship("Proforma", back_populates="detalles")
    producto = relationship("Producto")

# --- CONEXIÓN A POSTGRESQL ---
# Formato: postgresql://usuario:contraseña@localhost:5432/nombre_bd
# Cambia 'postgres' y 'tu_contraseña_aqui' por tus datos reales de pgAdmin
USUARIO = "postgres" 
CONTRASENA = "12345"
SERVIDOR = "localhost"
PUERTO = "5432"
BASE_DE_DATOS = "sistema_proformas"

cadena_conexion = f"postgresql://{USUARIO}:{CONTRASENA}@{SERVIDOR}:{PUERTO}/{BASE_DE_DATOS}"
engine = create_engine(cadena_conexion)

# Esto crea las tablas en pgAdmin 4
Base.metadata.create_all(engine)

print("¡Tablas creadas con éxito en PostgreSQL!")