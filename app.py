import streamlit as st
import pandas as pd
import plotly.express as px

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

@st.cache_data(ttl=60)
def cargar_objetivos(url):
    try:
        df_obj = pd.read_csv(url, header=None)
        
        # Buscamos en qué fila están los títulos (donde dice "AÑO")
        fila_header = df_obj[df_obj.apply(lambda x: x.astype(str).str.contains('AÑO', case=False).any(), axis=1)].index[0]
        
        # Seteamos esa fila como los nombres de las columnas reales
        df_obj.columns = df_obj.iloc[fila_header].astype(str).str.strip().str.upper()
        df_obj = df_obj.iloc[fila_header + 1:].copy()
        
        # Encontramos dinámicamente las columnas de marca 
        cols_marcas = [c for c in df_obj.columns if "PEUGEOT" in c or "CITR" in c]
        cols = ["AÑO", "MES"] + cols_marcas
        df_obj = df_obj[cols].copy()
        
        # LECTURA A PRUEBA DE BALAS: Convertimos a números obligando a descartar vacíos o texto basura
        df_obj["AÑO"] = pd.to_numeric(df_obj["AÑO"], errors="coerce")
        df_obj["MES"] = pd.to_numeric(df_obj["MES"], errors="coerce")
        df_obj = df_obj.dropna(subset=["AÑO", "MES"])
        
        # Formato final
        df_obj["AÑO"] = df_obj["AÑO"].astype(int).astype(str)
        df_obj["MES"] = df_obj["MES"].astype(int).astype(str).str.zfill(2)
        df_obj["Mes_Ingreso"] = df_obj["AÑO"] + "-" + df_obj["MES"]
        
        # Melt
        df_obj = df_obj.melt(id_vars=["Mes_Ingreso"], value_vars=cols_marcas, 
                             var_name="Marca", value_name="Objetivo")
        
        # Limpiamos nombres de marcas para cruce perfecto
        df_obj["Marca"] = df_obj["Marca"].astype(str).str.upper().str.strip()
        df_obj["Marca"] = df_obj["Marca"].replace({"CITRÖEN": "CITROËN", "CITROEN": "CITROËN"})
        
        df_obj["Objetivo"] = pd.to_numeric(df_obj["Objetivo"], errors="coerce").fillna(0)
        
        return df_obj
    except Exception as e:
        return pd.DataFrame(columns=["Mes_Ingreso", "Marca", "Objetivo"])

st.title("📊 Tablero de Suscripciones")
st.divider()

# Cargamos los datos
try:
    df = cargar_datos(URL_DATOS)
    df_objetivos = cargar_objetivos(URL_OBJETIVOS)
    
    # ---------------- LIMPIEZA Y TRANSFORMACIÓN (BACKEND INVISIBLE) ----------------
    
    # Limpiamos columna Marca principal para cruce exacto
    df["Marca"] = df["Marca"].astype(str).str.upper().str.strip()
    df["Marca"] = df["Marca"].replace({"CITROEN": "CITROËN"})
    
    # 1. Filtro estricto: Solo Aceptadas
    df = df[df["ESTADO"].astype(str).str.lower().str.strip().isin(["aceptado", "aceptada"])]
    
    # 2. Filtro de Fechas Inválidas
    df = df[df["Fecha  de Ingreso en CISA"].notna()]
    filtro_textos_invalidos = ["pendiente", "renunciado", "none", "nan", ""]
    df = df[~df["Fecha  de Ingreso en CISA"].astype(str).str.lower().str.strip().isin(filtro_textos_invalidos)]
    
    # 3. Traductor de meses y formato de fecha
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
        # ---------------- FILTROS GLOBALES ----------------
        st.subheader("🔍 Filtros Globales")
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            años_disponibles = sorted(df["Año"].unique().tolist())
            años_sel = st.multiselect("📅 Seleccionar Año (dejá en blanco para todos):", años_disponibles)
            
        with col_filtro2:
            meses_disponibles = sorted(df["Mes"].unique().tolist())
            meses_sel = st.multiselect("📆 Seleccionar Mes (dejá en blanco para todos):", meses_disponibles)

        # Aplicamos filtros
        df_filtrado = df.copy()
        if años_sel:
            df_filtrado = df_filtrado[df_filtrado["Año"].isin(años_sel)]
        if meses_sel:
            df_filtrado = df_filtrado[df_filtrado["Mes"].isin(meses_sel)]
            
        st.success(f"✅ Mostrando {len(df_filtrado)} operaciones aprobadas y con fecha válida.")
        st.divider()
        
        # ---------------- GRÁFICOS ----------------
        if not df_filtrado.empty:
            col_graf1, col_graf2 = st.columns(2)
            
            # --- GRÁFICO 1: COMPARATIVO POR MARCA CON OBJETIVOS ---
            with col_graf1:
                st.markdown("### 🏢 Evolución vs. Objetivos")
                
                df_marca = df_filtrado.groupby(["Mes_Ingreso", "Marca"]).size().reset_index(name="Cantidad")
                
                # Cruzamos con tabla de objetivos
                if not df_objetivos.empty:
                    df_marca = df_marca.merge(df_objetivos, on=["Mes_Ingreso", "Marca"], how="left")
                    df_marca["Objetivo"] = df_marca["Objetivo"].fillna(0)
                else:
                    df_marca["Objetivo"] = 0
                
                # Porcentajes del mix
                totales_mes = df_marca.groupby("Mes_Ingreso")["Cantidad"].transform("sum")
                df_marca["Porcentaje"] = (df_marca["Cantidad"] / totales_mes) * 100
                
                # Etiqueta enriquecida
                def armar_etiqueta(row):
                    txt = f"{row['Cantidad']} ({row['Porcentaje']:.1f}%)"
                    if row['Objetivo'] > 0:
                        txt += f"<br>🎯 Obj: {int(row['Objetivo'])}"
                    return txt
                df_marca["Etiqueta"] = df_marca.apply(armar_etiqueta, axis=1)
                
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
                
                # Agregamos líneas de objetivos y CORREGIMOS EL EJE X
                colores_lineas = {"PEUGEOT": "#1A5276", "CITROËN": "#78281F"}
                
                for marca in df_marca["Marca"].unique():
                    df_linea = df_marca[df_marca["Marca"] == marca].sort_values("Mes_Ingreso")
                    if df_linea["Objetivo"].sum() > 0:
                        fig_marca.add_scatter(
                            x=df_linea["Mes_Ingreso"],
                            y=df_linea["Objetivo"],
                            mode='lines+markers',
                            name=f'🎯 Meta {marca}',
                            line=dict(color=colores_lineas.get(marca, "black"), width=3, dash='dot'),
                            marker=dict(size=10, symbol="diamond")
                        )

                # Fix crítico para que el eje X no invente horas
                fig_marca.update_xaxes(type='category')
                fig_marca.update_layout(margin=dict(t=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                
                st.plotly_chart(fig_marca, use_container_width=True)

            # --- GRÁFICO 2: RANKING DE VENDEDORES ---
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
                fig_ranking.update_layout(margin=dict(t=20))
                
                st.plotly_chart(fig_ranking, use_container_width=True)
        else:
            st.warning("No hay operaciones para la combinación de filtros seleccionada.")

        st.divider()

        # ---------------- TABLA DE DETALLES FINAL ----------------
        st.subheader("📋 Detalle de Operaciones")
        
        columnas_deseadas = [
            "Marca", "Tipo de Solicitud", "Vendedor_Limpio", "FECHA CONFIRMACION CLIENTE", 
            "cliente", "localidad", "Fecha de TMK", "TMK", "Fecha  de Ingreso en CISA", "ESTADO"
        ]
        columnas_finales = [col for col in columnas_deseadas if col in df_filtrado.columns]
        
        st.dataframe(df_filtrado[columnas_finales].sort_values(by="Fecha  de Ingreso en CISA", ascending=False), use_container_width=True, hide_index=True)
        
    else:
        st.warning("Actualmente no hay registros en la base de datos que cumplan las condiciones estrictas (Aceptados y con fecha).")
        
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
