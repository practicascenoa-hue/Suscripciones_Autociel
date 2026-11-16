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
    df.columns = df.columns.str.strip()
    return df

st.title("📊 Tablero de Suscripciones - Autociel")
st.divider()

# Cargamos los datos
try:
    df = cargar_datos(URL_DATOS)
    
    st.success(f"✅ Base de datos conectada exitosamente. Total de registros: {len(df)}")
    
    # ---------------- 1. GRÁFICOS Y MÉTRICAS ----------------
    with st.expander("📊 Gráficos Mensuales de Suscripciones (Solo Aceptadas por Fecha CISA)", expanded=True):
        
        # Filtramos la base principal una sola vez para ambos gráficos
        df_graficos = df.copy()
        
        # Filtro 1: Estado aceptado/aceptada
        df_graficos = df_graficos[df_graficos["ESTADO"].astype(str).str.lower().str.strip().isin(["aceptado", "aceptada"])]
        
        # Filtro 2: Fechas válidas
        df_graficos = df_graficos[df_graficos["Fecha  de Ingreso en CISA"].notna()]
        filtro_textos_invalidos = ["pendiente", "renunciado", "none", "nan", ""]
        df_graficos = df_graficos[~df_graficos["Fecha  de Ingreso en CISA"].astype(str).str.lower().str.strip().isin(filtro_textos_invalidos)]

        if not df_graficos.empty:
            # Convertimos la fecha a Mes-Año
            df_graficos["Mes_Ingreso"] = pd.to_datetime(df_graficos["Fecha  de Ingreso en CISA"], errors="coerce").dt.strftime("%Y-%m")
            df_graficos = df_graficos.dropna(subset=["Mes_Ingreso"])
            
            if not df_graficos.empty:
                
                # Creamos las pestañas para organizar los gráficos
                tab1, tab2 = st.tabs(["🏢 Comparativo por Marca", "👤 Comparativo por Vendedor"])
                
                # --- PESTAÑA 1: POR MARCA ---
                with tab1:
                    df_marca = df_graficos.groupby(["Mes_Ingreso", "Marca"]).size().reset_index(name="Cantidad")
                    totales_mes_marca = df_marca.groupby("Mes_Ingreso")["Cantidad"].transform("sum")
                    df_marca["Porcentaje"] = (df_marca["Cantidad"] / totales_mes_marca) * 100
                    df_marca["Etiqueta"] = df_marca["Cantidad"].astype(str) + " (" + df_marca["Porcentaje"].round(1).astype(str) + "%)"
                    
                    fig_marca = px.bar(
                        df_marca, 
                        x="Mes_Ingreso", 
                        y="Cantidad", 
                        color="Marca", 
                        barmode="group",
                        text="Etiqueta",
                        color_discrete_map={"PEUGEOT": "#2E86C1", "CITROËN": "#E74C3C"},
                        labels={"Mes_Ingreso": "Mes de Ingreso a CISA", "Cantidad": "Volumen Aprobado"}
                    )
                    fig_marca.update_traces(textposition='outside')
                    fig_marca.update_layout(margin=dict(t=40))
                    st.plotly_chart(fig_marca, use_container_width=True)
                
                # --- PESTAÑA 2: POR VENDEDOR ---
                with tab2:
                    # Agrupamos por mes y por vendedor
                    df_vendedor = df_graficos.groupby(["Mes_Ingreso", "Vendedor"]).size().reset_index(name="Cantidad")
                    
                    fig_vendedor = px.bar(
                        df_vendedor, 
                        x="Mes_Ingreso", 
                        y="Cantidad", 
                        color="Vendedor", 
                        barmode="group", # Muestra las barras de los vendedores una al lado de la otra
                        text="Cantidad",
                        labels={"Mes_Ingreso": "Mes de Ingreso a CISA", "Cantidad": "Volumen Aprobado", "Vendedor": "Asesor Comercial"}
                    )
                    fig_vendedor.update_traces(textposition='outside')
                    fig_vendedor.update_layout(margin=dict(t=40))
                    st.plotly_chart(fig_vendedor, use_container_width=True)
                    
            else:
                st.warning("Hay operaciones 'Aceptadas', pero sus fechas de CISA tienen un formato no válido.")
        else:
            st.warning("No hay operaciones con estado 'Aceptada' que ya tengan una fecha cargada en CISA.")

    st.divider()

    # ---------------- 2. TABLA DE DETALLES FINAL ----------------
    st.subheader("📋 Detalle de Suscripciones (Todas las operaciones)")

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
