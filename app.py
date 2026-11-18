import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Suscripciones Autociel", layout="wide")

# URLs de exportación directa a CSV
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Juea0cEn3t7Emdtx0HexD7IpemaPNkHi2XoBTJ2mexc/export?format=csv&gid=2059629715"
URL_OBJETIVOS = "https://docs.google.com/spreadsheets/d/1Juea0cEn3t7Emdtx0HexD7IpemaPNkHi2XoBTJ2mexc/export?format=csv&gid=1392546647"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

def cargar_objetivos(url):
    try:
        df_obj = pd.read_csv(url, header=None)
        
        fila_header = df_obj[df_obj.apply(lambda x: x.astype(str).str.contains('AÑO', case=False).any(), axis=1)].index[0]
        
        df_obj.columns = df_obj.iloc[fila_header].astype(str).str.strip().str.upper()
        df_obj = df_obj.iloc[fila_header + 1:].copy()
        
        cols_marcas = [c for c in df_obj.columns if "PEUGEOT" in str(c) or "CITR" in str(c)]
        cols = ["AÑO", "MES"] + cols_marcas
        df_obj = df_obj[cols].copy()
        
        df_obj["AÑO"] = pd.to_numeric(df_obj["AÑO"], errors="coerce")
        df_obj["MES"] = pd.to_numeric(df_obj["MES"], errors="coerce")
        df_obj = df_obj.dropna(subset=["AÑO", "MES"])
        
        df_obj["AÑO"] = df_obj["AÑO"].astype(int).astype(str)
        df_obj["MES"] = df_obj["MES"].astype(int).astype(str).str.zfill(2)
        df_obj["Mes_Ingreso"] = df_obj["AÑO"] + "-" + df_obj["MES"]
        
        df_obj = df_obj.melt(id_vars=["Mes_Ingreso"], value_vars=cols_marcas, 
                             var_name="Marca", value_name="Objetivo")
        
        df_obj["Marca"] = df_obj["Marca"].astype(str).str.upper().str.strip()
        df_obj["Marca"] = df_obj["Marca"].replace({"CITRÖEN": "CITROËN", "CITROEN": "CITROËN"})
        
        df_obj["Objetivo"] = pd.to_numeric(df_obj["Objetivo"], errors="coerce").fillna(0)
        
        return df_obj, ""
    except Exception as e:
        return pd.DataFrame(columns=["Mes_Ingreso", "Marca", "Objetivo"]), str(e)

st.title("📊 Tablero de Suscripciones")
st.divider()

# Cargamos los datos
try:
    df = cargar_datos(URL_DATOS)
    df_objetivos, error_obj = cargar_objetivos(URL_OBJETIVOS)
    
    # ---------------- LIMPIEZA Y TRANSFORMACIÓN ----------------
    df["Marca"] = df["Marca"].astype(str).str.upper().str.strip()
    df["Marca"] = df["Marca"].replace({"CITROEN": "CITROËN"})
    
    df = df[df["ESTADO"].astype(str).str.lower().str.strip().isin(["aceptado", "aceptada"])]
    
    df = df[df["Fecha  de Ingreso en CISA"].notna()]
    filtro_textos_invalidos = ["pendiente", "renunciado", "none", "nan", ""]
    df = df[~df["Fecha  de Ingreso en CISA"].astype(str).str.lower().str.strip().isin(filtro_textos_invalidos)]
    
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
    
    df["Año"] = df["Fecha_Real"].dt.year.astype(str)
    df["Mes"] = df["Fecha_Real"].dt.month.astype(str).str.zfill(2)
    df["Mes_Ingreso"] = df["Fecha_Real"].dt.strftime("%Y-%m")
    
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
        if error_obj:
            st.warning(f"⚠️ No se pudieron cargar los objetivos. Error detectado: {error_obj}")
            
        st.subheader("🔍 Filtros Globales")
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            años_disponibles = sorted(df["Año"].unique().tolist())
            años_sel = st.multiselect("📅 Seleccionar Año (dejá en blanco para todos):", años_disponibles)
            
        with col_filtro2:
            meses_disponibles = sorted(df["Mes"].unique().tolist())
            meses_sel = st.multiselect("📆 Seleccionar Mes (dejá en blanco para todos):", meses_disponibles)

        df_filtrado = df.copy()
        if años_sel:
            df_filtrado = df_filtrado[df_filtrado["Año"].isin(años_sel)]
        if meses_sel:
            df_filtrado = df_filtrado[df_filtrado["Mes"].isin(meses_sel)]
            
        st.success(f"✅ Mostrando {len(df_filtrado)} operaciones aprobadas en el período seleccionado.")
        st.divider()
        
        if not df_filtrado.empty:
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                st.markdown("### 🏢 Cumplimiento vs Meta")
                
                df_marca = df_filtrado.groupby(["Mes_Ingreso", "Marca"]).size().reset_index(name="Cantidad")
                
                if not df_objetivos.empty:
                    df_marca = df_marca.merge(df_objetivos, on=["Mes_Ingreso", "Marca"], how="left")
                    df_marca["Objetivo"] = df_marca["Objetivo"].fillna(0)
                else:
                    df_marca["Objetivo"] = 0
                
                totales_mes = df_marca.groupby("Mes_Ingreso")["Cantidad"].transform("sum")
                df_marca["Porcentaje"] = (df_marca["Cantidad"] / totales_mes) * 100
                
                df_marca["Etiqueta"] = df_marca["Cantidad"].astype(str) + " (" + df_marca["Porcentaje"].round(1).astype(str) + "%)"
                
                # Gráfico de barras original por Marca (Rojo Citroën, Azul Peugeot)
                fig_marca = px.bar(
                    df_marca, 
                    x="Mes_Ingreso", 
                    y="Cantidad", 
                    color="Marca", 
                    barmode="group",
                    text="Etiqueta",
                    color_discrete_map={"PEUGEOT": "#0078D7", "CITROËN": "#E81123"}, # Tonos vibrantes como en el dibujo
                    labels={"Mes_Ingreso": "Mes", "Cantidad": "Suscripciones"}
                )
                
                # Ubicamos el texto adentro para que no choque con la línea de la meta
                fig_marca.update_traces(textposition='inside', insidetextfont=dict(color="white", size=13, weight="bold"))
                
                # --- Línea negra para el objetivo sobre cada barra respectiva ---
                df_obj_validos = df_marca[df_marca["Objetivo"] > 0]
                
                if not df_obj_validos.empty:
                    for marca in df_obj_validos["Marca"].unique():
                        df_obj_marca = df_obj_validos[df_obj_validos["Marca"] == marca]
                        
                        fig_marca.add_trace(
                            go.Scatter(
                                x=df_obj_marca["Mes_Ingreso"],
                                y=df_obj_marca["Objetivo"],
                                mode='markers+text',
                                name=f"Meta {marca}",
                                offsetgroup=marca, # Centra la línea exactamente sobre su barra
                                text=["Meta: " + str(int(obj)) for obj in df_obj_marca["Objetivo"]],
                                textposition="top center",
                                marker=dict(
                                    symbol="line-ew", 
                                    size=45, # Ancho de la línea negra
                                    color="black",
                                    line=dict(color="black", width=4) # Grosor de la línea
                                ),
                                textfont=dict(color="black", size=13, weight="bold"),
                                showlegend=False,
                                hoverinfo="skip"
                            )
                        )

                fig_marca.update_xaxes(type='category')
                fig_marca.update_layout(margin=dict(t=30), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                
                st.plotly_chart(fig_marca, use_container_width=True)

            with col_graf2:
                st.markdown("### 🏆 Ranking de Ventas")
                df_ranking = df_filtrado.groupby("Vendedor_Limpio").size().reset_index(name="Cantidad")
                
                df_ranking = df_ranking.sort_values(by="Cantidad", ascending=True)
                df_ranking["Etiqueta_Barra"] = df_ranking["Vendedor_Limpio"] + " (" + df_ranking["Cantidad"].astype(str) + ")"

                fig_ranking = px.bar(
                    df_ranking, 
                    x="Cantidad", 
                    y="Vendedor_Limpio", 
                    orientation='h',
                    text="Etiqueta_Barra",
                    labels={"Cantidad": "Volumen Aprobado", "Vendedor_Limpio": ""},
                    color_discrete_sequence=["#27AE60"]
                )
                
                fig_ranking.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(color="white", size=14))
                fig_ranking.update_yaxes(showticklabels=False)
                fig_ranking.update_layout(
                    margin=dict(t=30),
                    clickmode='event+select'
                )
                
                seleccion = st.plotly_chart(fig_ranking, use_container_width=True, on_select="rerun")
                
                vendedor_seleccionado
