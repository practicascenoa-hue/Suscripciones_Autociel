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
    
    # ---------------- FILTRO GLOBAL DE VENDEDOR ----------------
    # Extraemos la lista de vendedores únicos, quitamos vacíos y ordenamos alfabéticamente
    lista_vendedores = sorted(df["Vendedor"].dropna().astype(str).unique().tolist())
    
    # Creamos un selector múltiple. Si lo dejan vacío, muestra todos.
    vendedores_seleccionados = st.multiselect(
        "👤 Filtrar por Vendedor (dejá en blanco para ver a todos):", 
        options=lista_vendedores
    )
    
    # Aplicamos el filtro a los datos base
    if vendedores_seleccionados:
        df_filtrado = df[df["Vendedor"].isin(vendedores_seleccionados)]
    else:
        df_filtrado = df

    st.success(f"✅ Mostrando datos de {len(df_filtrado)} registros en total.")
    
    # ---------------- 1. GRÁFICO DESPLEGABLE ----------------
    with st.expander("📊 Gráfico Comparativo por Marca (Solo Aceptadas por Fecha CISA)", expanded=True):
        
        # Usamos los datos filtrados por el vendedor
        df_grafico = df_filtrado.copy()
        
        # Condición estricta: Estado == "aceptado"
        df_grafico = df_grafico[df_grafico["ESTADO"].astype(str).str.lower().str.strip() == "aceptado"]
        
        # Descartamos filas sin fecha de ingreso a CISA
        df_grafico = df_grafico[df_grafico["Fecha  de Ingreso en CISA"].notna()]
        df_grafico = df_grafico[df_grafico["Fecha  de Ingreso en CISA"].astype(str).str.strip() != ""]

        if not df_grafico.empty:
            # Convertimos la fecha a formato Mes-Año
            df_grafico["Mes_Ingreso"] = pd.to_datetime(df_grafico["Fecha  de Ingreso en CISA"], errors="coerce").dt.strftime("%Y-%m")
            df_grafico = df_grafico.dropna(subset=["Mes_Ingreso"])
            
            if not df_grafico.empty:
                # Agrupamos para contar la cantidad
                df_agrupado = df_grafico.groupby(["Mes_Ingreso", "Marca"]).size().reset_index(name="Cantidad")
                
                # Calculamos el porcentaje sobre el total de cada mes
                totales_por_mes = df_agrupado.groupby("Mes_Ingreso")["Cantidad"].transform("sum")
                df_agrupado["Porcentaje"] = (df_agrupado["Cantidad"] / totales_por_mes) * 100
                
                # Creamos el texto de la etiqueta (Ej: "45 (60.5%)")
                df_agrupado["Etiqueta"] = df_agrupado["Cantidad"].astype(str) + " (" + df_agrupado["Porcentaje"].round(1).astype(str) + "%)"
                
                # Dibujamos el gráfico
                fig = px.bar(
                    df_agrupado, 
                    x="Mes_Ingreso", 
                    y="Cantidad", 
                    color="Marca", 
                    barmode="group",
                    text="Etiqueta",
                    color_discrete_map={"PEUGEOT": "#2E86C1", "CITROËN": "#E74C3C"},
                    labels={"Mes_Ingreso": "Mes de Ingreso a CISA", "Cantidad": "Volumen Aprobado"}
                )
                
                fig.update_traces(textposition='outside')
                # Damos un margen arriba para que el porcentaje no se corte
                fig.update_layout(margin=dict(t=40))
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay fechas válidas para graficar.")
        else:
            st.warning("No hay operaciones con estado 'Aceptado' y fecha de ingreso para el vendedor/es seleccionado/s.")

    st.divider()

    # ---------------- 2. TABLA DE DETALLES FINAL ----------------
    st.subheader("📋 Detalle de Suscripciones")

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
    
    # Mostramos la tabla con el df_filtrado (para que también reaccione al filtro de vendedor)
    st.dataframe(df_filtrado[columnas_finales], use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
