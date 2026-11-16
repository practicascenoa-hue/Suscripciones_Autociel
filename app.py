import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Suscripciones Autociel", layout="wide")

# URL de exportación directa a CSV
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Juea0cEn3t7Emdtx0HexD7IpemaPNkHi2XoBTJ2mexc/export?format=csv&gid=2059629715"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

st.title("📊 Tablero de Suscripciones - Autociel")
st.divider()

# Cargamos los datos
try:
    df = cargar_datos(URL_DATOS)
    st.success(f"✅ Base de datos conectada exitosamente. Total de registros cargados: {len(df)}")
    
    # Mostramos los primeros registros para conocer las columnas
    st.subheader("Vista previa de la base de datos")
    st.dataframe(df, use_container_width=True)
    
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
