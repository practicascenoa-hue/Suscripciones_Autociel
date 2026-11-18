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
                
                # LÓGICA DE APILADO (Base, Faltante, Excedente)
                df_marca["Base"] = df_marca.apply(lambda row: min(row["Cantidad"], row["Objetivo"]) if row["Objetivo"] > 0 else row["Cantidad"], axis=1)
                df_marca["Faltante"] = df_marca.apply(lambda row: max(0, row["Objetivo"] - row["Cantidad"]) if row["Objetivo"] > 0 else 0, axis=1)
                df_marca["Excedente"] = df_marca.apply(lambda row: max(0, row["Cantidad"] - row["Objetivo"]) if row["Objetivo"] > 0 else 0, axis=1)

                # Definimos los colores por marca
                color_peugeot_solido = "rgba(46, 134, 193, 1)"      
                color_peugeot_claro = "rgba(46, 134, 193, 0.25)"    
                color_citroen_solido = "rgba(231, 76, 60, 1)"       
                color_citroen_claro = "rgba(231, 76, 60, 0.25)"     

                df_marca["Color_Base"] = df_marca["Marca"].map({"PEUGEOT": color_peugeot_solido, "CITROËN": color_citroen_solido})
                df_marca["Color_Faltante"] = df_marca["Marca"].map({"PEUGEOT": color_peugeot_claro, "CITROËN": color_citroen_claro})

                # Generar etiqueta combinada: Cantidad (Porcentaje%)
                def generar_etiqueta(row):
                    if row["Cantidad"] == 0:
                        return ""
                    if row["Objetivo"] > 0:
                        pct = (row["Cantidad"] / row["Objetivo"]) * 100
                        return f"{int(row['Cantidad'])} ({pct:.0f}%)"
                    else:
                        return str(int(row["Cantidad"]))
                        
                df_marca["Etiqueta_Principal"] = df_marca.apply(generar_etiqueta, axis=1)

                fig_marca = go.Figure()
                eje_x_agrupado = [df_marca["Mes_Ingreso"], df_marca["Marca"]]

                # 1. Barra Sólida (Base Ejecutada)
                fig_marca.add_trace(go.Bar(
                    x=eje_x_agrupado,
                    y=df_marca["Base"],
                    name="Realizado",
                    marker_color=df_marca["Color_Base"],
                    # Muestra la etiqueta solo si no hay excedente
                    text=df_marca.apply(lambda row: row["Etiqueta_Principal"] if row["Excedente"] == 0 else "", axis=1),
                    textposition="auto", # <-- Plotly decide si va horizontal, vertical o afuera
                    insidetextfont=dict(color="white", size=14, weight="bold"),
                    outsidetextfont=dict(color="black", size=14, weight="bold"),
                    showlegend=False,
                    hoverinfo="y+name"
                ))

                # 2. Barra Clara (Faltante para llegar a la meta)
                fig_marca.add_trace(go.Bar(
                    x=eje_x_agrupado,
                    y=df_marca["Faltante"],
                    name="Faltante",
                    marker_color=df_marca["Color_Faltante"],
                    marker_line=dict(color=df_marca["Color_Base"], width=1.5),
                    text=[""] * len(df_marca),
                    textposition="inside",
                    showlegend=False,
                    hoverinfo="y+name"
                ))

                # 3. Barra Sólida (Sobre Ejecución) 
                fig_marca.add_trace(go.Bar(
                    x=eje_x_agrupado,
                    y=df_marca["Excedente"],
                    name="Sobre Ejecución",
                    marker_color=df_marca["Color_Base"],
                    # Muestra la etiqueta acá si superaron el objetivo
                    text=df_marca.apply(lambda row: row["Etiqueta_Principal"] if row["Excedente"] > 0 else "", axis=1),
                    textposition="auto", # <-- Plotly decide la mejor posición y rotación
                    insidetextfont=dict(color="white", size=14, weight="bold"),
                    outsidetextfont=dict(color="black", size=14, weight="bold"),
                    showlegend=False,
                    hoverinfo="y+name"
                ))

                # 4. Línea negra horizontal para la Meta (Sin texto)
                df_obj_validos = df_marca[df_marca["Objetivo"] > 0]
                if not df_obj_validos.empty:
                    fig_marca.add_trace(go.Scatter(
                        x=[df_obj_validos["Mes_Ingreso"], df_obj_validos["Marca"]],
                        y=df_obj_validos["Objetivo"],
                        mode="markers", 
                        name="Objetivo",
                        marker=dict(symbol="line-ew", size=45, line=dict(color="black", width=4)),
                        hoverinfo="skip",
                        showlegend=False
                    ))

                # 5. Trazos falsos (Dummy traces) EXCLUSIVAMENTE para crear una leyenda limpia explicativa
                fig_marca.add_trace(go.Bar(x=[None], y=[None], marker_color="rgba(128,128,128,1)", name="Realizado"))
                fig_marca.add_trace(go.Bar(x=[None], y=[None], marker_color="rgba(128,128,128,0.25)", marker_line=dict(color="rgba(128,128,128,1)", width=1.5), name="Faltante a la Meta"))
                fig_marca.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(symbol="line-ew", size=15, line=dict(color="black", width=3)), name="Objetivo"))

                # Configuramos el apilamiento y los márgenes 
                fig_marca.update_layout(
                    barmode="stack",
                    margin=dict(t=50),
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, title=""),
                    xaxis=dict(title="")
                )
                
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
                
                vendedor_seleccionado = None
                if seleccion and seleccion.get("selection") and seleccion["selection"].get("points"):
                    vendedor_seleccionado = seleccion["selection"]["points"][0]["y"]

        st.divider()

        # ---------------- TABLA DE DETALLES FINAL ----------------
        st.subheader("📋 Detalle de Operaciones")
        
        df_tabla = df_filtrado.copy()
        
        if vendedor_seleccionado:
            df_tabla = df_tabla[df_tabla["Vendedor_Limpio"] == vendedor_seleccionado]
            st.info(f"🔎 Filtrando tabla inferior por el vendedor seleccionado: **{vendedor_seleccionado}**. (Para ver todos, hacé clic en el espacio en blanco del gráfico de ranking).")
        
        columnas_deseadas = [
            "Marca", "Tipo de Solicitud", "Vendedor_Limpio", "FECHA CONFIRMACION CLIENTE", 
            "cliente", "localidad", "Fecha de TMK", "TMK", "Fecha  de Ingreso en CISA", "ESTADO"
        ]
        columnas_finales = [col for col in columnas_deseadas if col in df_tabla.columns]
        
        st.dataframe(df_tabla[columnas_finales].sort_values(by="Fecha  de Ingreso en CISA", ascending=False), use_container_width=True, hide_index=True)
        
    else:
        st.warning("Actualmente no hay registros en la base de datos que cumplan las condiciones estrictas (Aceptados y con fecha).")
        
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
