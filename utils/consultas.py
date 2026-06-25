import pandas as pd
import streamlit as st
from utils.conexion import get_connection

# ── helper interno ───────────────────────────────────────────
def _query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()

# ── Filtro WHERE reutilizable ────────────────────────────────
def _where_fecha_ubic(anio="Todos", departamento="Todos",
                      alias_fecha="d", alias_ubic="u"):
    """
    Devuelve (where_sql, params) para filtrar por año y/o departamento.
    Asume que ya se hace JOIN con DIM_FECHA y DIM_UBICACION.
    """
    parts, params = [], []
    if anio != "Todos":
        parts.append(f"{alias_fecha}.anio = ?")
        params.append(int(anio))
    if departamento != "Todos":
        parts.append(f"{alias_ubic}.departamento = ?")
        params.append(departamento)
    where = ("WHERE " + " AND ".join(parts)) if parts else ""
    return where, tuple(params)

def _where_fecha(anio="Todos", alias="d"):
    parts, params = [], []
    if anio != "Todos":
        parts.append(f"{alias}.anio = ?")
        params.append(int(anio))
    where = ("WHERE " + " AND ".join(parts)) if parts else ""
    return where, tuple(params)

# ══════════════════════════════════════════════════════════════
# KPIs — se filtran por año Y departamento
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def obtener_kpis(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT
            SUM(f.total_siniestros)    total_siniestros,
            SUM(f.cantidad_fallecidos) total_fallecidos,
            SUM(f.cantidad_lesionados) total_lesionados
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
        {where}
    """, params)

@st.cache_data(ttl=3600)
def kpi_vehiculos(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT SUM(fv.total_vehiculos) total_vehiculos
        FROM FACT_VEHICULOS fv
        INNER JOIN FACT_SINIESTROS f ON fv.codigo_siniestro = f.codigo_siniestro
        INNER JOIN DIM_FECHA       d ON f.id_fecha           = d.id_fecha
        INNER JOIN DIM_UBICACION   u ON f.id_ubicacion       = u.id_ubicacion
        {where}
    """, params)

# ══════════════════════════════════════════════════════════════
# MAPA
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def obtener_mapa(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    parts = [
        "TRY_CAST([COORDENADAS LATITUD]  AS FLOAT) IS NOT NULL",
        "TRY_CAST([COORDENADAS LONGITUD] AS FLOAT) IS NOT NULL",
        "[DEPARTAMENTO] IS NOT NULL",
    ]
    params = []
    if anio != "Todos":
        parts.append("YEAR([FECHA SINIESTRO]) = ?")
        params.append(int(anio))
    if departamento != "Todos":
        parts.append("[DEPARTAMENTO] = ?")
        params.append(departamento)

    return _query(f"""
        SELECT
            [CÓDIGO SINIESTRO],
            TRY_CAST([COORDENADAS LATITUD]  AS FLOAT) AS latitud,
            TRY_CAST([COORDENADAS LONGITUD] AS FLOAT) AS longitud,
            [DEPARTAMENTO], [PROVINCIA], [DISTRITO],
            [TIPO DE VÍA], [CONDICIÓN CLIMÁTICA],
            [CAUSA FACTOR PRINCIPAL],
            [CANTIDAD DE FALLECIDOS],
            [CANTIDAD DE LESIONADOS]
        FROM siniestros
        WHERE {" AND ".join(parts)}
    """, tuple(params))

# ══════════════════════════════════════════════════════════════
# SERIES TEMPORALES
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def siniestros_por_anio(departamento: str = "Todos") -> pd.DataFrame:
    """Evolución histórica — filtra por departamento si se selecciona."""
    if departamento != "Todos":
        return _query("""
            SELECT d.anio, SUM(f.total_siniestros) total
            FROM FACT_SINIESTROS f
            INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
            INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
            WHERE u.departamento = ?
            GROUP BY d.anio
            ORDER BY d.anio
        """, (departamento,))
    return _query("""
        SELECT d.anio, SUM(f.total_siniestros) total
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_FECHA d ON f.id_fecha = d.id_fecha
        GROUP BY d.anio
        ORDER BY d.anio
    """)

# ══════════════════════════════════════════════════════════════
# GEOGRAFÍA
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def top_departamentos(anio: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha(anio)
    return _query(f"""
        SELECT TOP 10
            u.departamento,
            SUM(f.total_siniestros) total
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
        INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
        {where}
        GROUP BY u.departamento
        ORDER BY total DESC
    """, params)

@st.cache_data(ttl=3600)
def top_distritos(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT TOP 10
            u.distrito,
            SUM(f.total_siniestros) total
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
        INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
        {where}
        GROUP BY u.distrito
        ORDER BY total DESC
    """, params)

@st.cache_data(ttl=3600)
def top_carreteras(anio: str = "Todos") -> pd.DataFrame:
    extra = "AND d.anio = ?" if anio != "Todos" else ""
    params = (int(anio),) if anio != "Todos" else ()
    return _query(f"""
        SELECT TOP 10
            u.codigo_carretera,
            SUM(f.total_siniestros) total
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
        INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
        WHERE u.codigo_carretera IS NOT NULL
          AND u.codigo_carretera NOT IN ('NO CORRESPONDE','SIN CLASIFICAR','')
          {extra}
        GROUP BY u.codigo_carretera
        ORDER BY total DESC
    """, params)

# ══════════════════════════════════════════════════════════════
# FACTORES
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def top_causas(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT TOP 10
            c.causa_principal causa,
            SUM(f.total_siniestros) total
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_CAUSA     c ON f.id_causa     = c.id_causa
        INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} c.causa_principal IS NOT NULL
          AND c.causa_principal NOT IN ('','EN PROCESO DE INVESTIGACIÓN')
        GROUP BY c.causa_principal
        ORDER BY total DESC
    """, params)

@st.cache_data(ttl=3600)
def siniestros_clima(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT
            c.condicion_climatica,
            SUM(f.total_siniestros) total
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_CLIMA     c ON f.id_clima     = c.id_clima
        INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} c.condicion_climatica IS NOT NULL
          AND c.condicion_climatica != ''
        GROUP BY c.condicion_climatica
        ORDER BY total DESC
    """, params)

@st.cache_data(ttl=3600)
def siniestros_tipo_via(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT
            v.tipo_via,
            SUM(f.total_siniestros) total
        FROM FACT_SINIESTROS f
        INNER JOIN DIM_VIA       v ON f.id_via       = v.id_via
        INNER JOIN DIM_FECHA     d ON f.id_fecha     = d.id_fecha
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} v.tipo_via IS NOT NULL
          AND v.tipo_via != ''
        GROUP BY v.tipo_via
        ORDER BY total DESC
    """, params)

# ══════════════════════════════════════════════════════════════
# VÍCTIMAS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def fallecidos_sexo(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT
            p.sexo,
            SUM(fp.fallecido) total
        FROM FACT_PERSONAS fp
        INNER JOIN DIM_PERSONA   p ON fp.id_persona_dim  = p.id_persona_dim
        INNER JOIN FACT_SINIESTROS f ON fp.codigo_siniestro = f.codigo_siniestro
        INNER JOIN DIM_FECHA     d ON f.id_fecha           = d.id_fecha
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion       = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} p.sexo IS NOT NULL
          AND p.sexo NOT IN ('','null','NULL')
        GROUP BY p.sexo
        ORDER BY total DESC
    """, params)

@st.cache_data(ttl=3600)
def fallecidos_edad(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT
            p.rango_edad,
            SUM(fp.fallecido) total
        FROM FACT_PERSONAS fp
        INNER JOIN DIM_PERSONA   p ON fp.id_persona_dim  = p.id_persona_dim
        INNER JOIN FACT_SINIESTROS f ON fp.codigo_siniestro = f.codigo_siniestro
        INNER JOIN DIM_FECHA     d ON f.id_fecha           = d.id_fecha
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion       = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} p.rango_edad IS NOT NULL
          AND p.rango_edad NOT IN ('','null','NULL')
        GROUP BY p.rango_edad
        ORDER BY total DESC
    """, params)

@st.cache_data(ttl=3600)
def licencia_conductor(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT
            l.posee_licencia,
            COUNT(*) total
        FROM FACT_PERSONAS fp
        INNER JOIN DIM_LICENCIA  l ON fp.id_licencia    = l.id_licencia
        INNER JOIN FACT_SINIESTROS f ON fp.codigo_siniestro = f.codigo_siniestro
        INNER JOIN DIM_FECHA     d ON f.id_fecha           = d.id_fecha
        INNER JOIN DIM_UBICACION u ON f.id_ubicacion       = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} l.posee_licencia IS NOT NULL
          AND l.posee_licencia NOT IN ('','null','NULL')
        GROUP BY l.posee_licencia
        ORDER BY total DESC
    """, params)

# ══════════════════════════════════════════════════════════════
# VEHÍCULOS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def tipo_vehiculo(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT TOP 15
            v.vehiculo,
            SUM(fv.total_vehiculos) total
        FROM FACT_VEHICULOS fv
        INNER JOIN DIM_VEHICULO    v ON fv.id_vehiculo_dim  = v.id_vehiculo_dim
        INNER JOIN FACT_SINIESTROS f ON fv.codigo_siniestro = f.codigo_siniestro
        INNER JOIN DIM_FECHA       d ON f.id_fecha           = d.id_fecha
        INNER JOIN DIM_UBICACION   u ON f.id_ubicacion       = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} v.vehiculo IS NOT NULL
          AND v.vehiculo NOT IN ('','null','NULL','NO IDENTIFICADO')
        GROUP BY v.vehiculo
        ORDER BY total DESC
    """, params)

@st.cache_data(ttl=3600)
def vehiculos_soat(anio: str = "Todos", departamento: str = "Todos") -> pd.DataFrame:
    where, params = _where_fecha_ubic(anio, departamento)
    return _query(f"""
        SELECT
            s.posee_seguro,
            COUNT(*) total
        FROM FACT_VEHICULOS fv
        INNER JOIN DIM_SEGURIDAD_VEHICULO s ON fv.id_seguridad_vehiculo = s.id_seguridad_vehiculo
        INNER JOIN FACT_SINIESTROS f ON fv.codigo_siniestro = f.codigo_siniestro
        INNER JOIN DIM_FECHA       d ON f.id_fecha           = d.id_fecha
        INNER JOIN DIM_UBICACION   u ON f.id_ubicacion       = u.id_ubicacion
        {where}
          {'AND' if where else 'WHERE'} s.posee_seguro IS NOT NULL
          AND s.posee_seguro NOT IN ('','null','NULL')
        GROUP BY s.posee_seguro
        ORDER BY total DESC
    """, params)

# ══════════════════════════════════════════════════════════════
# LISTAS PARA FILTROS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400)
def obtener_anios() -> pd.DataFrame:
    return _query("SELECT DISTINCT anio FROM DIM_FECHA ORDER BY anio")

@st.cache_data(ttl=86400)
def obtener_departamentos() -> pd.DataFrame:
    return _query("SELECT DISTINCT departamento FROM DIM_UBICACION ORDER BY departamento")