import os
os.environ["PGCLIENTENCODING"] = "utf-8"

import textwrap
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from fpdf import FPDF
from datetime import date

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
cadena_conexion = "postgresql://neondb_owner:npg_Qa5DLvoJw4AP@ep-sweet-bonus-ammr3vxr.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(cadena_conexion)
Base = declarative_base()

# --- 2. TABLAS (MODELOS) ---
class Cliente(Base):
    __tablename__ = 'clientes'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    empresa = Column(String(150), nullable=False)
    contacto = Column(String(150))
    telefono = Column(String(20))
    correo = Column(String(100))

class Producto(Base):
    __tablename__ = 'productos'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True)
    nombre = Column(String(200), nullable=False)
    precio_unitario = Column(Float, nullable=False)

class Proforma(Base):
    __tablename__ = 'proformas'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    fecha = Column(Date, default=date.today)
    total = Column(Float, default=0.0)
    
    # --- NUEVAS COLUMNAS PARA LAS NOTAS PERSONALIZABLES ---
    validez_dias = Column(Integer, default=8)
    forma_pago = Column(String(150), default="CREDITO 30 DIAS")
    garantia = Column(String(150), default="1 Meses por defectos de fabricación")
    tiempo_entrega = Column(String(150), default="22 Dia(s) después de aprobada la cotización")
    
    cliente = relationship("Cliente")
    detalles = relationship("DetalleProforma", back_populates="proforma", cascade="all, delete-orphan")

class DetalleProforma(Base):
    __tablename__ = 'detalle_proforma'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    proforma_id = Column(Integer, ForeignKey('proformas.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Float, nullable=False) 
    precio_fijado = Column(Float, nullable=False)
    
    proforma = relationship("Proforma", back_populates="detalles")
    producto = relationship("Producto")

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- 3. MEMORIA TEMPORAL ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'editando_proforma_id' not in st.session_state:
    st.session_state.editando_proforma_id = None

# Valores por defecto de las notas para que no tengas que escribirlas de cero siempre
if 'notas_default' not in st.session_state:
    st.session_state.notas_default = {
        "validez": 8,
        "pago": "CREDITO 30 DIAS",
        "garantia": "1 Meses por defectos de fabricación",
        "entrega": "22 Dia(s) después de aprobada la cotización"
    }

# --- 4. FUNCIÓN DEL PDF ---
def generar_pdf(cliente_obj, carrito, total_proforma, id_proforma, validez, pago, garantia, entrega):
    pdf = FPDF()
    pdf.add_page()
    
    # --- ENCABEZADO Y LOGO ---
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=30)
    
    pdf.set_font("Helvetica", style="B", size=32)
    pdf.set_text_color(0, 130, 200)
    pdf.set_xy(40, 10)
    pdf.cell(0, 10, "TALLER QUESADA", align="C")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(40, 22)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, "RS. Sergio Monge Quesada Ced. 3-02670436", align="C", ln=1)
    
    pdf.set_xy(40, 26)
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 5, "TELEFAX:(506)2552-8338 CEL: 8382-1645", align="C", ln=1)
    
    pdf.set_xy(40, 31)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, "E-MAIL: tallerquesada3@gmail.com", align="C", ln=1)
    
    # --- FECHA ---
    meses = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    hoy = date.today()
    
    pdf.set_xy(10, 42)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(15, 5, "FECHA:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(80, 5, f"{hoy.day} de {meses[hoy.month - 1]} del {hoy.year}")
    
    # --- CAJA DEL CLIENTE ---
    y_caja = 50
    pdf.rect(15, y_caja, 180, 25) 
    
    pdf.set_xy(17, y_caja + 2)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(25, 6, "ATENCIÓN:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(140, 6, cliente_obj.contacto if cliente_obj.contacto else "")
    
    pdf.set_xy(17, y_caja + 8)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(25, 6, "EMPRESA:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(140, 6, cliente_obj.empresa)
    
    pdf.set_xy(17, y_caja + 14)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(25, 6, "TELEFONO:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(80, 6, cliente_obj.telefono if cliente_obj.telefono else "")
    
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(12, 6, "FAX:")
    
    pdf.set_xy(17, y_caja + 20)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(25, 6, "E-MAIL:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(140, 6, cliente_obj.correo if cliente_obj.correo else "")
    
    # --- SALUDO ---
    pdf.set_xy(10, y_caja + 30)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 6, "Estimado(a) Señor(a):", ln=1)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, "Por medio de la presente, me permito saludarle y a la vez ofrecer la cotización solicitada:", ln=1)
    
    pdf.ln(4)
    
    # --- TABLA DE PRODUCTOS ---
    y_tabla = pdf.get_y()
    pdf.line(10, y_tabla, 200, y_tabla) 
    
    pdf.set_xy(10, y_tabla + 1)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(15, 6, "CANT.", align="C")
    pdf.cell(120, 6, "DESCRIPCION")
    pdf.cell(30, 6, "PRECIO", align="C")
    pdf.cell(25, 6, "TOTAL", align="R")
    
    pdf.line(10, y_tabla + 7, 200, y_tabla + 7) 
    
    pdf.set_xy(10, y_tabla + 8)
    pdf.set_font("Helvetica", size=8)
    for item in carrito:
        desc_lines = textwrap.wrap(item['nombre'], width=85)
        if not desc_lines:
            desc_lines = [""]
            
        pdf.cell(15, 5, f"{item['cantidad']:.2f}", align="C")
        pdf.cell(120, 5, desc_lines[0])
        pdf.cell(30, 5, f"{item['precio']:,.2f}", align="C")
        pdf.cell(25, 5, f"{item['subtotal']:,.2f}", align="R", ln=1)
        
        if len(desc_lines) > 1:
            for line in desc_lines[1:]:
                pdf.cell(15, 4, "")
                pdf.cell(120, 4, line, ln=1)
        pdf.ln(1)
    
    pdf.ln(5)
    
    # --- PIE DE PÁGINA ---
    y_footer = pdf.get_y()
    if y_footer > 240: 
        pdf.add_page()
        y_footer = pdf.get_y()
        
    pdf.line(10, y_footer, 200, y_footer) 
    
    # --- BLOQUE DERECHO (Totales) ---
    pdf.set_xy(135, y_footer + 2)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(30, 5, "SUBTOTAL", align="R")
    pdf.cell(30, 5, f"{total_proforma:,.2f}", align="R", ln=1)
    
    pdf.set_x(135)
    pdf.cell(30, 5, "DESC.", align="R")
    pdf.cell(30, 5, "0.00", align="R", ln=1)
    
    pdf.set_x(135)
    pdf.cell(30, 5, "IMP.", align="R")
    pdf.cell(30, 5, "0.00", align="R", ln=1)
    
    pdf.set_x(135)
    pdf.cell(30, 5, "TOTAL", align="R")
    pdf.cell(30, 5, f"{total_proforma:,.2f}", align="R", ln=1)
    
    pdf.set_x(135)
    pdf.cell(30, 5, "MONEDA", align="R")
    pdf.cell(30, 5, "Colones", align="R", ln=1)
    
    # --- BLOQUE IZQUIERDO (Firma y Notas Personalizadas) ---
    pdf.set_xy(30, y_footer + 8)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(60, 5, "ATENTAMENTE,", align="C", ln=1)
    
    y_firma = pdf.get_y()
    if os.path.exists("firma.png"):
        pdf.image("firma.png", x=40, y=y_firma, w=40)
    
    pdf.set_xy(30, y_firma + 15)
    pdf.cell(60, 5, "____________________________________", align="C", ln=1)
    pdf.set_x(30)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(60, 4, "Sergio Monge Quesada", align="C", ln=1)
    pdf.set_x(30)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(60, 4, "TEL: 83-82-1645 / 2552-8338", align="C", ln=1)
    pdf.set_x(30)
    pdf.cell(60, 4, "E-MAIL:tallerquesada@costarricense.cr", align="C", ln=1)
    
    # AQUI SE IMPRIMEN LAS NOTAS DINAMICAS
    pdf.set_xy(10, pdf.get_y() + 5)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(0, 5, "NOTAS", ln=1)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 4, f"Esta proforma tiene una validez de: {validez} Días", ln=1)
    pdf.cell(0, 4, f"Forma de pago: {pago}", ln=1)
    pdf.cell(0, 4, f"Garantía: {garantia}", ln=1)
    pdf.cell(0, 4, f"Tiempo de entrega: {entrega}", ln=1)
    
    pdf.set_xy(120, pdf.get_y() - 10)
    pdf.cell(70, 5, "________________________________________", align="C", ln=1)
    pdf.set_x(120)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(70, 5, "APROBADO POR EL CLIENTE", align="C", ln=1)
    
    return pdf.output()

# --- 5. INTERFAZ GRÁFICA ---
st.title("💼 Sistema Profesional de Proformas")
tab_proforma, tab_inventario, tab_clientes, tab_historial = st.tabs(["📝 Crear/Editar Proforma", "📦 Inventario", "👥 Clientes", "🗄️ Historial"])

# ==========================================
# PESTAÑA: INVENTARIO 
# ==========================================
with tab_inventario:
    st.subheader("Buscador y Editor de Productos")
    busqueda = st.text_input("🔍 Buscar por Código o Descripción:")
    query = session.query(Producto)
    if busqueda:
        query = query.filter((Producto.codigo.ilike(f"%{busqueda}%")) | (Producto.nombre.ilike(f"%{busqueda}%")))
    productos_bd = query.all()
    
    if productos_bd:
        st.write("✏️ *Haz doble clic en Nombre o Precio para modificarlos y presiona el botón abajo para guardar:*")
        lista = [{"ID": p.id, "Código": p.codigo, "Nombre": p.nombre, "Precio": p.precio_unitario} for p in productos_bd]
        df_edit = st.data_editor(pd.DataFrame(lista), hide_index=True, disabled=["ID", "Código"], use_container_width=True)
        
        if st.button("💾 Guardar Cambios Editados"):
            for index, fila in df_edit.iterrows():
                prod = session.query(Producto).get(fila["ID"])
                prod.nombre = fila["Nombre"]
                prod.precio_unitario = fila["Precio"]
            session.commit()
            st.success("¡Base de datos actualizada!")
    else:
        st.info("No hay productos registrados o no coincide la búsqueda.")
        
    st.divider()
    st.subheader("Agregar Nuevo Producto")
    conteo = session.query(Producto).count()
    codigo_sugerido = f"ART-{conteo + 1:04d}"
    
    with st.form("form_nuevo_prod", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        codigo_nuevo = col1.text_input("Código", value=codigo_sugerido)
        nombre_nuevo = col2.text_input("Descripción del Producto")
        precio_nuevo = st.number_input("Precio Unitario (₡)", min_value=0.0)
        
        if st.form_submit_button("Crear Artículo"):
            nuevo_p = Producto(codigo=codigo_nuevo, nombre=nombre_nuevo, precio_unitario=precio_nuevo)
            session.add(nuevo_p)
            session.commit()
            st.success("¡Artículo creado!")
            st.rerun()

# ==========================================
# PESTAÑA: CREAR / EDITAR PROFORMA 
# ==========================================
with tab_proforma:
    if st.session_state.editando_proforma_id:
        st.warning(f"✏️ **MODO EDICIÓN ACTIVADO:** Estás modificando la Proforma N° {st.session_state.editando_proforma_id}")
        if st.button("❌ Cancelar Edición"):
            st.session_state.editando_proforma_id = None
            st.session_state.carrito = []
            # Restaurar notas por defecto
            st.session_state.notas_default = {"validez": 8, "pago": "CREDITO 30 DIAS", "garantia": "1 Meses por defectos de fabricación", "entrega": "22 Dia(s) después de aprobada la cotización"}
            st.rerun()

    clientes_bd = session.query(Cliente).all()
    productos_bd = session.query(Producto).all()
    
    if clientes_bd and productos_bd:
        col_select, col_cart = st.columns([1, 2])
        
        with col_select:
            st.subheader("1. Construir Proforma")
            dict_clientes = {c.empresa: c for c in clientes_bd}
            cliente_sel = st.selectbox("Seleccionar Cliente:", list(dict_clientes.keys()))
            
            st.divider()
            dict_prod = {f"{p.codigo} | {p.nombre}": p for p in productos_bd}
            prod_sel = st.selectbox("Buscar Artículo:", list(dict_prod.keys()))
            cant_sel = st.number_input("Cantidad:", min_value=0.1, value=1.0, step=1.0)
            
            if st.button("➕ Agregar a Proforma"):
                p_obj = dict_prod[prod_sel]
                st.session_state.carrito.append({
                    "id_prod": p_obj.id,
                    "codigo": p_obj.codigo,
                    "nombre": p_obj.nombre,
                    "cantidad": cant_sel,
                    "precio": p_obj.precio_unitario,
                    "subtotal": cant_sel * p_obj.precio_unitario
                })
                st.rerun()
                
            st.divider()
            st.subheader("2. Condiciones (Notas)")
            # Nuevos campos para modificar las notas
            input_validez = st.number_input("Validez (Días)", min_value=1, value=st.session_state.notas_default["validez"])
            input_pago = st.text_input("Forma de pago (Ej. CONTADO, CREDITO 15 DIAS...)", value=st.session_state.notas_default["pago"])
            input_garantia = st.text_input("Garantía", value=st.session_state.notas_default["garantia"])
            input_entrega = st.text_input("Tiempo de entrega", value=st.session_state.notas_default["entrega"])
                
        with col_cart:
            st.subheader("🛒 Elementos Agregados")
            if len(st.session_state.carrito) > 0:
                df_carrito = pd.DataFrame(st.session_state.carrito)
                st.dataframe(df_carrito[["cantidad", "codigo", "nombre", "subtotal"]], hide_index=True, use_container_width=True)
                
                total_proforma = sum(item['subtotal'] for item in st.session_state.carrito)
                st.markdown(f"### Gran Total: ₡ {total_proforma:,.2f}")
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("🗑️ Vaciar Proforma"):
                    st.session_state.carrito = []
                    st.rerun()
                    
                if col_btn2.button("💾 Guardar y Generar PDF"):
                    c_obj = dict_clientes[cliente_sel]
                    
                    if st.session_state.editando_proforma_id:
                        prof_actual = session.query(Proforma).get(st.session_state.editando_proforma_id)
                        prof_actual.cliente_id = c_obj.id
                        prof_actual.total = total_proforma
                        # Actualizar notas
                        prof_actual.validez_dias = input_validez
                        prof_actual.forma_pago = input_pago
                        prof_actual.garantia = input_garantia
                        prof_actual.tiempo_entrega = input_entrega
                        
                        session.query(DetalleProforma).filter_by(proforma_id=prof_actual.id).delete()
                        for item in st.session_state.carrito:
                            det = DetalleProforma(proforma_id=prof_actual.id, producto_id=item['id_prod'], cantidad=item['cantidad'], precio_fijado=item['precio'])
                            session.add(det)
                            
                        id_final = prof_actual.id
                        st.success("¡Proforma actualizada correctamente!")
                    else:
                        nueva_prof = Proforma(cliente_id=c_obj.id, total=total_proforma, validez_dias=input_validez, forma_pago=input_pago, garantia=input_garantia, tiempo_entrega=input_entrega)
                        session.add(nueva_prof)
                        session.flush() 
                        
                        for item in st.session_state.carrito:
                            det = DetalleProforma(proforma_id=nueva_prof.id, producto_id=item['id_prod'], cantidad=item['cantidad'], precio_fijado=item['precio'])
                            session.add(det)
                            
                        id_final = nueva_prof.id
                        st.success("¡Proforma guardada en el Historial!")

                    session.commit()
                    
                    archivo_pdf = generar_pdf(c_obj, st.session_state.carrito, total_proforma, id_final, input_validez, input_pago, input_garantia, input_entrega)
                    st.download_button(
                        label="🖨️ Descargar PDF Generado",
                        data=bytes(archivo_pdf),
                        file_name=f"Proforma_{id_final}_{c_obj.empresa}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.session_state.editando_proforma_id = None
                    st.session_state.carrito = []
                    st.session_state.notas_default = {"validez": 8, "pago": "CREDITO 30 DIAS", "garantia": "1 Meses por defectos de fabricación", "entrega": "22 Dia(s) después de aprobada la cotización"}
            else:
                st.info("Tu proforma está vacía. Selecciona artículos a la izquierda.")
    else:
        st.warning("⚠️ Registra al menos un cliente y un producto primero.")

# ==========================================
# PESTAÑA: CLIENTES 
# ==========================================
with tab_clientes:
    with st.form("form_cliente", clear_on_submit=True):
        st.write("Agregar Cliente")
        e = st.text_input("Empresa")
        c = st.text_input("Contacto")
        t = st.text_input("Teléfono")
        cor = st.text_input("Correo")
        if st.form_submit_button("Guardar") and e:
            session.add(Cliente(empresa=e, contacto=c, telefono=t, correo=cor))
            session.commit()
            st.success("Cliente guardado exitosamente.")
            st.rerun()

# ==========================================
# PESTAÑA: HISTORIAL (CON EDICIÓN)
# ==========================================
with tab_historial:
    st.subheader("Proformas Guardadas")
    historial = session.query(Proforma).order_by(Proforma.id.desc()).all()
    
    if historial:
        for prof in historial:
            with st.expander(f"Proforma N° {prof.id} - Cliente: {prof.cliente.empresa} - Fecha: {prof.fecha} - Total: ₡ {prof.total:,.2f}"):
                detalles = session.query(DetalleProforma).filter_by(proforma_id=prof.id).all()
                for d in detalles:
                    st.write(f"- {d.cantidad}x {d.producto.nombre} (₡ {d.precio_fijado:,.2f} c/u)")
                
                if st.button(f"✏️ Editar Proforma N° {prof.id}", key=f"btn_edit_{prof.id}"):
                    st.session_state.editando_proforma_id = prof.id
                    st.session_state.carrito = []
                    for d in detalles:
                        st.session_state.carrito.append({
                            "id_prod": d.producto_id,
                            "codigo": d.producto.codigo,
                            "nombre": d.producto.nombre,
                            "cantidad": d.cantidad,
                            "precio": d.precio_fijado,
                            "subtotal": d.cantidad * d.precio_fijado
                        })
                    # Cargar las notas de esta proforma para editarlas
                    st.session_state.notas_default = {
                        "validez": prof.validez_dias,
                        "pago": prof.forma_pago,
                        "garantia": prof.garantia,
                        "entrega": prof.tiempo_entrega
                    }
                    st.success("¡Cargada! Ve a la primera pestaña '📝 Crear/Editar Proforma' para modificarla.")
    else:
        st.info("Aún no has guardado ninguna proforma.")