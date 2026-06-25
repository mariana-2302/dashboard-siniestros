import pandas as pd
import streamlit as st
from utils.conexion_csv import load_table

# ── Helpers de filtro ────────────────────────────────────────
def _fil(df: pd.DataFrame, anio="Todos", departamento="Todos",
         col_anio="anio", col_depto="departamento") -> pd.DataFrame:
    if anio != "Todos" and col_anio in df.columns:
        df = df[df[col_anio].astype(str) == str(anio)]
    if departamento != "Todos" and col_depto in df.columns:
        df = df[df[col_depto] == departamento]
    return df

def _no_nulos(df: pd.DataFrame, col: str,
              excluir: list = None) -> pd.DataFrame:
    """Quita nulos y valores basura de una columna."""
    basura = {"", "null", "NULL", "None", "nan", "NaN"}
    if excluir:
        basura.update(excluir)
    df = df[df[col].notna()]
    df = df[~df[col].astype(str).str.strip().isin(basura)]
    return df

# ── Tablas base (se cachean una vez) ────────────────────────
@st.cache_data(ttl=3600)
def _fact_sin():  return load_table("FACT_SINIESTROS")
@st.cache_data(ttl=3600)
def _fact_per():  return load_table("FACT_PERSONAS")
@st.cache_data(ttl=3600)
def _fact_veh():  return load_table("FACT_VEHICULOS")
@st.cache_data(ttl=3600)
def _dim_fecha(): return load_table("DIM_FECHA")
@st.cache_data(ttl=3600)
def _dim_ubic():  return load_table("DIM_UBICACION")
@st.cache_data(ttl=3600)
def _dim_cau():   return load_table("DIM_CAUSA")
@st.cache_data(ttl=3600)
def _dim_cli():   return load_table("DIM_CLIMA")
@st.cache_data(ttl=3600)
def _dim_via():   return load_table("DIM_VIA")
@st.cache_data(ttl=3600)
def _dim_per():   return load_table("DIM_PERSONA")
@st.cache_data(ttl=3600)
def _dim_lic():   return load_table("DIM_LICENCIA")
@st.cache_data(ttl=3600)
def _dim_veh():   return load_table("DIM_VEHICULO")
@st.cache_data(ttl=3600)
def _dim_seg():   return load_table("DIM_SEGURIDAD_VEHICULO")
@st.cache_data(ttl=3600)
def _dim_grav():  return load_table("DIM_GRAVEDAD")

# ── Join base: FACT_SINIESTROS + DIM_FECHA + DIM_UBICACION ──
@st.cache_data(ttl=3600)
def _fs_fecha_ubic() -> pd.DataFrame:
    fs = _fact_sin()
    fd = _dim_fecha()[["id_fecha", "anio", "mes", "trimestre"]]
    fu = _dim_ubic()[["id_ubicacion", "departamento", "provincia",
                       "distrito", "codigo_carretera", "red_vial"]]
    return fs.merge(fd, on="id_fecha", how="left") \
             .merge(fu, on="id_ubicacion", how="left")

# ══════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def obtener_kpis(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = _fil(_fs_fecha_ubic(), anio, departamento)
    return pd.DataFrame([{
        "total_siniestros":  int(df["total_siniestros"].sum()),
        "total_fallecidos":  int(df["cantidad_fallecidos"].sum()),
        "total_lesionados":  int(df["cantidad_lesionados"].sum()),
    }])

@st.cache_data(ttl=3600)
def kpi_vehiculos(anio="Todos", departamento="Todos") -> pd.DataFrame:
    fv  = _fact_veh()[["codigo_siniestro", "total_vehiculos"]]
    fsu = _fs_fecha_ubic()[["codigo_siniestro", "anio", "departamento"]]
    df  = fv.merge(fsu, on="codigo_siniestro", how="left")
    df  = _fil(df, anio, departamento)
    return pd.DataFrame([{"total_vehiculos": int(df["total_vehiculos"].sum())}])

# ══════════════════════════════════════════════════════════════
# MAPA
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
@st.cache_data(ttl=3600)
def obtener_mapa(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = load_table("siniestros")
    df["latitud"]  = pd.to_numeric(df["COORDENADAS LATITUD"],  errors="coerce")
    df["longitud"] = pd.to_numeric(df["COORDENADAS LONGITUD"], errors="coerce")
    df = df.dropna(subset=["latitud", "longitud"])
    if anio != "Todos":
        df = df[df["FECHA SINIESTRO"].astype(str).str[:4] == str(anio)]
    if departamento != "Todos":
        df = df[df["DEPARTAMENTO"] == departamento]
    return df

def _csv_exists(nombre: str) -> bool:
    import os
    return os.path.exists(f"data/{nombre}.csv")

def _sin_desde_facts() -> pd.DataFrame:
    """Fallback si no existe siniestros.csv — construye un df mínimo."""
    fsu = _fs_fecha_ubic()
    fsu = fsu.rename(columns={
        "departamento": "DEPARTAMENTO",
        "provincia":    "PROVINCIA",
        "distrito":     "DISTRITO",
        "cantidad_fallecidos": "CANTIDAD DE FALLECIDOS",
        "cantidad_lesionados": "CANTIDAD DE LESIONADOS",
    })
    fsu["latitud"]  = None
    fsu["longitud"] = None
    return fsu

# ══════════════════════════════════════════════════════════════
# SERIES TEMPORALES
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def siniestros_por_anio(departamento="Todos") -> pd.DataFrame:
    df = _fil(_fs_fecha_ubic(), departamento=departamento)
    return df.groupby("anio")["total_siniestros"].sum() \
             .reset_index().rename(columns={"total_siniestros": "total"}) \
             .sort_values("anio")

# ══════════════════════════════════════════════════════════════
# GEOGRAFÍA
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def top_departamentos(anio="Todos") -> pd.DataFrame:
    df = _fil(_fs_fecha_ubic(), anio=anio)
    return df.groupby("departamento")["total_siniestros"].sum() \
             .reset_index().rename(columns={"total_siniestros": "total",
                                            "departamento": "departamento"}) \
             .sort_values("total", ascending=False).head(10)

@st.cache_data(ttl=3600)
def top_distritos(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = _fil(_fs_fecha_ubic(), anio, departamento)
    return df.groupby("distrito")["total_siniestros"].sum() \
             .reset_index().rename(columns={"total_siniestros": "total"}) \
             .sort_values("total", ascending=False).head(10)

@st.cache_data(ttl=3600)
def top_carreteras(anio="Todos") -> pd.DataFrame:
    df = _fil(_fs_fecha_ubic(), anio=anio)
    excluir = {"NO CORRESPONDE", "SIN CLASIFICAR", ""}
    df = _no_nulos(df, "codigo_carretera", list(excluir))
    return df.groupby("codigo_carretera")["total_siniestros"].sum() \
             .reset_index().rename(columns={"total_siniestros": "total"}) \
             .sort_values("total", ascending=False).head(10)

# ══════════════════════════════════════════════════════════════
# FACTORES
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def top_causas(anio="Todos", departamento="Todos") -> pd.DataFrame:
    fsu = _fil(_fs_fecha_ubic(), anio, departamento)
    dc  = _dim_cau()[["id_causa", "causa_principal"]]
    df  = fsu.merge(dc, on="id_causa", how="left")
    df  = _no_nulos(df, "causa_principal",
                    ["EN PROCESO DE INVESTIGACIÓN", "SIN CLASIFICAR"])
    return df.groupby("causa_principal")["total_siniestros"].sum() \
             .reset_index().rename(columns={"causa_principal": "causa",
                                            "total_siniestros": "total"}) \
             .sort_values("total", ascending=False).head(10)

@st.cache_data(ttl=3600)
def siniestros_clima(anio="Todos", departamento="Todos") -> pd.DataFrame:
    fsu = _fil(_fs_fecha_ubic(), anio, departamento)
    dc  = _dim_cli()[["id_clima", "condicion_climatica"]]
    df  = fsu.merge(dc, on="id_clima", how="left")
    df  = _no_nulos(df, "condicion_climatica")
    return df.groupby("condicion_climatica")["total_siniestros"].sum() \
             .reset_index().rename(columns={"total_siniestros": "total"}) \
             .sort_values("total", ascending=False)

@st.cache_data(ttl=3600)
def siniestros_tipo_via(anio="Todos", departamento="Todos") -> pd.DataFrame:
    fsu = _fil(_fs_fecha_ubic(), anio, departamento)
    dv  = _dim_via()[["id_via", "tipo_via"]]
    df  = fsu.merge(dv, on="id_via", how="left")
    df  = _no_nulos(df, "tipo_via")
    return df.groupby("tipo_via")["total_siniestros"].sum() \
             .reset_index().rename(columns={"total_siniestros": "total"}) \
             .sort_values("total", ascending=False)

# ══════════════════════════════════════════════════════════════
# VÍCTIMAS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fp_fecha_ubic() -> pd.DataFrame:
    """FACT_PERSONAS + fecha + ubicacion via FACT_SINIESTROS."""
    fp  = _fact_per()
    fsu = _fs_fecha_ubic()[["codigo_siniestro", "anio", "departamento"]]
    return fp.merge(fsu, on="codigo_siniestro", how="left")

@st.cache_data(ttl=3600)
def fallecidos_sexo(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = _fil(_fp_fecha_ubic(), anio, departamento)
    dp = _dim_per()[["id_persona_dim", "sexo"]]
    df = df.merge(dp, on="id_persona_dim", how="left")
    df = _no_nulos(df, "sexo")
    return df.groupby("sexo")["fallecido"].sum() \
             .reset_index().rename(columns={"fallecido": "total"}) \
             .sort_values("total", ascending=False)

@st.cache_data(ttl=3600)
def fallecidos_edad(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = _fil(_fp_fecha_ubic(), anio, departamento)
    dp = _dim_per()[["id_persona_dim", "rango_edad"]]
    df = df.merge(dp, on="id_persona_dim", how="left")
    df = _no_nulos(df, "rango_edad")
    return df.groupby("rango_edad")["fallecido"].sum() \
             .reset_index().rename(columns={"fallecido": "total"}) \
             .sort_values("total", ascending=False)

@st.cache_data(ttl=3600)
def licencia_conductor(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = _fil(_fp_fecha_ubic(), anio, departamento)
    dl = _dim_lic()[["id_licencia", "posee_licencia"]]
    df = df.merge(dl, on="id_licencia", how="left")
    df = _no_nulos(df, "posee_licencia")
    return df.groupby("posee_licencia").size() \
             .reset_index(name="total") \
             .sort_values("total", ascending=False)

# ══════════════════════════════════════════════════════════════
# VEHÍCULOS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fv_fecha_ubic() -> pd.DataFrame:
    fv  = _fact_veh()
    fsu = _fs_fecha_ubic()[["codigo_siniestro", "anio", "departamento"]]
    return fv.merge(fsu, on="codigo_siniestro", how="left")

@st.cache_data(ttl=3600)
def tipo_vehiculo(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = _fil(_fv_fecha_ubic(), anio, departamento)
    dv = _dim_veh()[["id_vehiculo_dim", "vehiculo"]]
    df = df.merge(dv, on="id_vehiculo_dim", how="left")
    df = _no_nulos(df, "vehiculo", ["NO IDENTIFICADO"])
    return df.groupby("vehiculo")["total_vehiculos"].sum() \
             .reset_index().rename(columns={"total_vehiculos": "total"}) \
             .sort_values("total", ascending=False).head(15)

@st.cache_data(ttl=3600)
def vehiculos_soat(anio="Todos", departamento="Todos") -> pd.DataFrame:
    df = _fil(_fv_fecha_ubic(), anio, departamento)
    ds = _dim_seg()[["id_seguridad_vehiculo", "posee_seguro"]]
    df = df.merge(ds, on="id_seguridad_vehiculo", how="left")
    df = _no_nulos(df, "posee_seguro")
    return df.groupby("posee_seguro").size() \
             .reset_index(name="total") \
             .sort_values("total", ascending=False)

# ══════════════════════════════════════════════════════════════
# LISTAS PARA FILTROS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400)
def obtener_anios() -> pd.DataFrame:
    return _dim_fecha()[["anio"]].drop_duplicates().sort_values("anio")

@st.cache_data(ttl=86400)
def obtener_departamentos() -> pd.DataFrame:
    return _dim_ubic()[["departamento"]].drop_duplicates() \
                                        .sort_values("departamento")