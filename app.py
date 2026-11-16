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
    # Limpiamos espacios en blanco accidentales en los nombres de las columnas (al principio y al final)
    df.columns = df.columns.str.strip()
    return df

st.title("📊 Tablero de Suscripciones - Autociel")
st.divider()

# Cargamos los datos
try:
    df = cargar_datos(URL_DATOS)
    st.success("✅ Base de datos conectada exitosamente.")
    
    # ---------------- 1. FILTROS Y GRÁFICO DESPLEGABLE ----------------
    with st.expander("📊 Ver Gráfico Comparativo de Suscripciones (Aprobadas y con Ingreso)", expanded=True):
        
        # Hacemos una copia de los datos para no borrarle filas a la tabla de abajo
        df_grafico = df.copy()
        
        # Condición 1: TMK == "ok" (pasamos a minúscula y quitamos espacios para asegurar)
        df_grafico = df_grafico[df_grafico["TMK"].astype(str).str.lower().str.strip() == "ok"]
        
        # Condición 2: Estado == "aceptado"
