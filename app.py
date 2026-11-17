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

st.title("📊 Tablero Ejecutivo - Autociel")
st.divider()

# Cargamos los datos
try:
    df = cargar_datos(URL_DATOS)
    
    # ---------------- LIMPIEZA Y TRANSFORMACIÓN (BACKEND INVISIBLE) ----------------
    
    # 1. Filtro estricto: Solo Aceptadas
    df = df[df["ESTADO"].astype(str).str.lower().str.strip().isin(["aceptado", "aceptada"])]
    
    # 2. Filtro de Fechas Inválidas
    df = df[df["Fecha  de Ingreso en CISA"].notna()]
    filtro_textos_invalidos = ["pendiente", "renunciado", "none", "nan", ""]
    df = df[~df["Fecha  de Ingreso en CISA"].astype(str).str.lower().str.strip().isin(filtro_textos_invalidos)]
    
    # 3. Traductor de meses y formato de fecha (Solución "6-ene" y "10/1")
    df["fecha_limpia"] = df["Fecha  de Ingreso en CISA"].astype(str).str.lower().str.strip()
    meses = {
        "ene": "01", "feb": "02", "mar": "03", "abr": "04", 
        "may": "05", "jun": "06", "jul": "07", "ago": "08", 
        "sep": "09", "oct": "10", "nov": "11", "dic": "12"
    }
    for letra, num in meses.items():
        df["fecha_limpia"] = df["fecha_limpia"].str.replace(letra, num, regex=False)
        
    df["Fecha_Real"] = pd.to_datetime(df["fecha_limpia"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Fecha_Real"])
    
    # Columnas matemáticas ocultas para los filtros
    df["Año"] = df["Fecha_Real"].dt.year.astype(str)
    df["Mes"] = df["Fecha_Real"].dt.month.astype(str).str.zfill(2) # zfill le pone un 0 adelante: "01", "02"
    df["Mes_Ingreso"] = df["Fecha_Real"].dt.strftime("%Y-%m")
    
    # 4. Unificación de Nombres de Vendedores
    reemplazos_vendedores = {
        "P. PORTAL": "PORTAL", "P.PORTAL": "PORTAL", "PABLO PORTAL": "PORTAL", "M. PORTAL": "PORTAL",
        "LUIS JAVIER": "JAVIER LUIS", "LUIS": "JAVIER LUIS",
        "CALVO": "CALVÓ", "CALVÓ BRENDA": "CALVÓ",
        "CHANGO": "CHANGO CAR", "2CHANGO CAR": "CHANGO CAR",
        "MARIQUE": "MANRIQUE",
        "ARENA": "AROZARENA",
        "AIMARETO": "AIMARETTO"
    }
    df["Vendedor_Limpio"] = df["Vendedor"].astype(str).str.upper().str.strip()
    df["Vendedor_Limpio"] = df["Vendedor_Limpio"].replace(reemplazos_vendedores)
    
    # -------------------------------------------------------------------------------

    if not df.empty:
        # ---------------- FILTROS GLOBALES (FRONTEND) ----------------
        st.subheader("🔍 Filtros Globales")
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            años_disponibles = ["Todos"] + sorted(df["Año"].unique().tolist())
            año_sel = st.selectbox("📅 Seleccionar Año:", años_disponibles)
            
        with col_filtro2:
            meses_disponibles = ["Todos"] + sorted(df["Mes"].unique().tolist())
            mes_sel = st.selectbox("📆 Seleccionar Mes:", meses_disponibles)

        # Aplicamos los filtros a la base de datos
        df_filtrado = df.copy()
        if año_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Año"] == año_sel]
        if mes_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Mes"] == mes_sel]
            
        st.success(f"✅ Mostrando {len(df_filtrado)} operaciones aprobadas y con fecha válida.")
        st.divider()
        
        # ---------------- GRÁFICOS ----------------
        if not df_filtrado.empty:
            col_graf1, col_graf2 = st.columns(2) # Partimos la pantalla a la mitad
            
            # --- GRÁFICO 1: COMPARATIVO POR MARCA ---
            with col_graf1:
                st.markdown("### 🏢 Evolución por Marca")
                df_marca = df_filtrado.groupby(["Mes_Ingreso", "Marca"]).size().reset_index(name="Cantidad")
                totales_mes = df_marca.groupby("Mes_Ingreso")["Cantidad"].transform("sum")
                df_marca["Porcentaje"] = (df_marca["Cantidad"] / totales_mes) * 100
                df_marca["Etiqueta"] = df_marca["Cantidad"].astype(str) + " (" + df_marca["Porcentaje"].round(1).astype(str) + "%)"
                
                fig_marca = px.bar(
                    df_marca, 
                    x="Mes_Ingreso", 
                    y="Cantidad", 
                    color="Marca", 
                    barmode="group",
                    text="Etiqueta",
                    color_discrete_map={"PEUGEOT": "#2E86C1", "CITROËN": "#E74C3C"},
                    labels={"Mes_Ingreso": "Mes", "Cantidad": "Suscripciones"}
                )
                fig_marca.update_traces(textposition='outside')
                fig_marca.update_layout(margin=dict(t=20))
                st.plotly_chart(fig_marca, use_container_width=True)

            # --- GRÁFICO 2: RANKING DE VENDEDORES ---
            with col_graf2:
                st.markdown("### 🏆 Ranking de Ventas")
                df_ranking = df_filtrado.groupby("Vendedor_Limpio").size().reset_index(name="Cantidad")
                
                # Ordenamos de menor a mayor para que en barras horizontales el líder quede arriba
                df_ranking = df_ranking.sort_values(by="Cantidad", ascending=True)
                
                # Creamos la etiqueta combinada para meter adentro de la barra (Ej: "PORTAL (15)")
                df_ranking["Etiqueta_Barra"] = df_ranking["Vendedor_Limpio"] + " (" + df_ranking["Cantidad"].astype(str) + ")"

                fig_ranking = px.bar(
                    df_ranking, 
                    x="Cantidad", 
                    y="Vendedor_Limpio", 
                    orientation='h',
                    text="Etiqueta_Barra",
                    labels={"Cantidad": "Volumen Aprobado", "Vendedor_Limpio": ""},
                    color_discrete_sequence=["#27AE60"] # Verde corporativo para el ranking
                )
                
                # Configuramos el texto al medio y ocultamos el eje Y lateral
                fig_ranking.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(color="white", size=14))
                fig_ranking.update_yaxes(showticklabels=False)
                fig_ranking.update_layout(margin=dict(t=20))
                
                st.plotly_chart(fig_ranking, use_container_width=True)
        else:
            st.warning("No hay operaciones para el año y mes seleccionados en los filtros.")

        st.divider()

        # ---------------- TABLA DE DETALLES FINAL ----------------
        st.subheader("📋 Detalle de Operaciones")
        
        # Mostramos la columna "Vendedor_Limpio" para que la tabla también tenga los nombres unificados
        columnas_deseadas = [
            "Marca", "Tipo de Solicitud", "Vendedor_Limpio", "FECHA CONFIRMACION CLIENTE", 
            "cliente", "localidad", "Fecha de TMK", "TMK", "Fecha  de Ingreso en CISA", "ESTADO"
        ]

        columnas_finales = [col for col in columnas_deseadas if col in df_filtrado.columns]
        
        # Mostramos la tabla, ordenada desde la fecha más reciente hacia atrás
        st.dataframe(df_filtrado[columnas_finales].sort_values(by="Fecha  de Ingreso en CISA", ascending=False), use_container_width=True, hide_index=True)
        
    else:
        st.warning("Actualmente no hay registros en la base de datos que cumplan las condiciones estrictas (Aceptados y con fecha).")
        
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
