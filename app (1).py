#importar las libreiras
import streamlit as st
from pymongo import MongoClient
from  bson.objectid import ObjectId
import pandas as pd
from datetime import datetime

#conexion a la base de datos
URI = st.secrets["MONGO_URI"]
@st.cache_resource
def init_connection():
  return MongoClient(URI)
try:
  cliente = init_connection()
  #definimos los datos de la base
  db = cliente["papeleria"]
  #colecciones
  productos = db["Productos"]
  ventas = db["Ventas"]
  proveedores = db["Proveedores"]
except Exception as e:
  st.error("Error al conectar la Base de Datos : ", e)

#Configuracion de la interfaz del menu
st.set_page_config(page_title="Papeleria - Panel Productos", layout="centered")
st.title("Inventario de productos 📦")
st.write("Esta area es la administracion del almacen de la papeleria")

#crear las pestañas del menu (tabs)
tab_dashboard, tab_ver, tab_agregar, tab_editar, tab_eliminar = st.tabs([
    "📊 Dashboard",
    "🔍 Ver Productos",
    "➕ Agregar Producto",
    "✏️ Editar Producto",
    "❌ Eliminar Producto"
])

with tab_dashboard:
    st.subheader("Dashboard de Inventario")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Productos",
            productos.count_documents({})
        )
    with col2:
        total_stock = sum(
            p["Stock"]
            for p in productos.find(
                {},
                {"Stock": 1}
            )
        )
        st.metric(
            "Stock Total",
            total_stock
        )
    datos = list(
        productos.find(
            {},
            {
                "_id": 0,
                "Nombre": 1,
                "Stock": 1
            }
        )
    )
    df = pd.DataFrame(datos)

    st.bar_chart(
        df.set_index("Nombre")["Stock"]
    )
with tab_ver:
    st.subheader("Lista de productos")
    try:
        datos = list(
            productos.find(
                {},
                {"_id": 0}
            )
        )
        df = pd.DataFrame(datos)
        st.dataframe(
            df,
            use_container_width=True
        )
    except Exception as e:
        st.error(
            f"Error al consultar productos: {e}"
        )

with tab_agregar:
    st.subheader("Agregar nuevo producto")
    with st.form("form_agregar"):
        id_producto = st.number_input(
            "ID",
            min_value=1,
            step=1
        )
        nombre = st.text_input("Nombre")
        descripcion = st.text_area("Descripción")
        categoria = st.text_input("Categoría")
        marca = st.text_input("Marca")
        precio = st.number_input(
            "Precio de Venta",
            min_value=0.0,
            step=0.50
        )
        stock = st.number_input(
            "Stock",
            min_value=0,
            step=1
        )
        proveedor = st.text_input("Proveedor")
        guardar = st.form_submit_button("Guardar Producto")
    if guardar:
        existe = productos.find_one({"Id": id_producto})
        if existe:
            st.error("Ya existe un producto con ese ID")
        else:
            nuevo_producto = {
                "Id": id_producto,
                "Nombre": nombre,
                "Descripcion": descripcion,
                "categoria": categoria,
                "Marca": marca,
                "PrecioVenta": precio,
                "Stock": stock,
                "Proveedor": proveedor
            }
            productos.insert_one(nuevo_producto)
            st.success("producto agregado correctamente")

def obtener_lista_productos():
    return list(
        productos.find(
            {},
            {"_id": 0, "Id": 1, "Nombre": 1}
        )
    )
lista_productos = obtener_lista_productos()

with tab_editar:
    if lista_productos:
        opciones = {
            f"{p['Id']} - {p['Nombre']}": p["Id"]
            for p in lista_productos
        }
        producto_seleccionado = st.selectbox(
            "Seleccione un producto",
            opciones.keys()
        )
        id_producto = opciones[producto_seleccionado]
        producto = productos.find_one({"Id": id_producto})
        nombre = st.text_input(
            "Nombre",
            value=producto.get("Nombre", "")
        )
        descripcion = st.text_area(
            "Descripción",
            value=producto.get("Descripcion", "")
        )
        categoria = st.text_input(
            "Categoría",
            value=producto.get("categoria", "")
        )
        marca = st.text_input(
            "Marca",
            value=producto.get("Marca", "")
        )
        precio = st.number_input(
            "Precio",
            value=float(producto.get("PrecioVenta", 0))
        )
        stock = st.number_input(
            "Stock",
            value=int(producto.get("Stock", 0))
        )
        proveedor = st.text_input(
            "Proveedor",
            value=producto.get("Proveedor", "")
        )
        if st.button("Actualizar Producto"):
            productos.update_one(
                {"Id": id_producto},
                {
                    "$set": {
                        "Nombre": nombre,
                        "Descripcion": descripcion,
                        "categoria": categoria,
                        "Marca": marca,
                        "PrecioVenta": precio,
                        "Stock": stock,
                        "Proveedor": proveedor
                    }
                }
            )
            st.success("Producto actualizado correctamente")
            st.rerun()
    else:
        st.warning("No existen productos registrados")

with tab_eliminar:
    st.subheader("Eliminar Producto")
    if lista_productos:
        opciones = {
            f"{p['Id']} - {p['Nombre']}": p["Id"]
            for p in lista_productos
        }
        producto_seleccionado = st.selectbox(
            "Seleccione el producto a eliminar",
            opciones.keys()
        )
        id_producto = opciones[producto_seleccionado]
        producto = productos.find_one({"Id": id_producto})
        st.warning("Esta acción no se puede deshacer.")
        st.write(f"ID: {producto['Id']}")
        st.write(f"Nombre: {producto['Nombre']}")
        st.write(f"Stock: {producto['Stock']}")
        confirmar = st.checkbox(
            "Confirmo que deseo eliminar este producto"
        )
        if st.button("🗑️ Eliminar Producto"):
            if confirmar:
                resultado = productos.delete_one(
                    {"Id": id_producto}
                )
                if resultado.deleted_count > 0:
                    st.success(
                        "Producto eliminado correctamente."
                    )
                    st.rerun()
                else:
                    st.error(
                        "No se encontró el producto."
                    )
            else:
                st.error(
                    "Debe confirmar la eliminación."
                )
    else:
        st.info("No existen productos registrados.")
