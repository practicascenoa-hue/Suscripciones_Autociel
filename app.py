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
    
    # ---------------- 1. FILTROS Y GRÁFICO DESPLEGABLE ----------------
    with st.expander("📊 Ver Gráfico Comparativo de Suscripciones (Aprobadas y con Ingreso)", expanded=True):
        
        # Hacemos una copia de los datos
        df_grafico = df.copy()
        
        # Condición 1: TMK == "ok" 
        df_grafico = df_grafico[df_grafico["TMK"].astype(str).str.lower().str.strip() == "ok"]
        
        # Condición 2: Estado == "aceptado"
        df_grafico = df_grafico[df_grafico["ESTADO"].astype(str).str.lower().str.strip() == "aceptado"]
        
        # Condición 3: Fecha de Ingreso en CISA no debe estar vacía
        df_grafico = df_grafico[df_grafico["Fecha  de Ingreso en CISA"].notna()]
        df_grafico = df_grafico[df_grafico["Fecha  de Ingreso en CISA"].astype(str).str.strip() != ""]
        df_grafico = df_grafico[df_grafico["Fecha  de Ingreso en CISA"].astype(str).str.lower() != "nan"]

        if not df_grafico.empty:
            # Convertimos la fecha a formato Mes-Año (Ej: 2026-10)
            df_grafico["Mes_Ingreso"] = pd.to_datetime(df_grafico["Fecha  de Ingreso en CISA"], errors="coerce").dt.strftime("%Y-%m")
            
            # Agrupamos sumando cuántas hay por Mes y por Marca
            df_agrupado = df_grafico.groupby(["Mes_Ingreso", "Marca"]).size().reset_index(name="Cantidad")
            
            # Dibujamos el gráfico
            fig = px.bar(
                df_agrupado, 
                x="Mes_Ingreso", 
                y="Cantidad", 
                color="Marca", 
                barmode="group",
                text="Cantidad",
                color_discrete_map={"PEUGEOT": "#2E86C1", "CITROËN": "#E74C3C"},
                labels={"Mes_Ingreso": "Mes de Ingreso a SISA", "Cantidad": "Volumen de Suscripciones"}
            )
            
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Actualmente no hay registros que cumplan las 3 condiciones estrictas a la vez (TMK ok, Aceptado y con Fecha de Ingreso).")

    st.divider()

    # ---------------- 2. TABLA DE DETALLES FINAL ----------------
    st.subheader(f"📋 Detalle de Suscripciones ({len(df)} registros totales)")

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

    columnas_finales = [col for col in columnas_deseadas if col in df.columns]
    st.dataframe(df[columnas_finales], use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
