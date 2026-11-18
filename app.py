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
