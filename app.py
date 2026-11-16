import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Suscripciones Autociel", layout="wide")

# URL de exportación directa a CSV
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Juea0cEn3t7Emdtx0HexD7IpemaPNkHi2XoBTJ2mexc/export?format=csv&gid=2059629715"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(url)
    # Limpiamos espacios en blanco accidentales en los nombres de las columnas
    df.columns = df.columns.str.strip()
    return df

st.title("📊 Tablero de Suscripciones - Autociel")
st.divider()

# Cargamos los datos
try:
    df = cargar_datos(URL_DATOS)
    st.success("✅ Base de datos conectada exitosamente.")
    
    # ---------------- 3. TABLA DE DETALLES FINAL ----------------
    st.subheader(f"📋 Detalle de Suscripciones ({len(df)} registros)")

    # Lista con los nombres EXACTOS sacados de tu Google Sheets
    columnas_deseadas = [
        "Marca", 
        "Tipo de Solicitud", 
        "Vendedor", 
        "FECHA CONFIRMACION CLIENTE", 
        "cliente", 
        "localidad", 
        "Fecha de TMK", 
        "TMK", 
        "Fecha  de Ingreso en CISA", 
        "ESTADO"
    ]

    # Filtramos las columnas que existen en la base
    columnas_finales = [col for col in columnas_deseadas if col in df.columns]

    # Mostramos la tabla en la interfaz
    st.dataframe(df[columnas_finales], use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
