import streamlit as st
import plotly.graph_objects as go
import folium
from folium.plugins import FastMarkerCluster
from streamlit_folium import st_folium
from utils.estilos import aplicar_estilos
from utils.consultas_csv import (
    obtener_kpis, kpi_vehiculos, obtener_mapa,
    siniestros_por_anio, top_departamentos, top_distritos,
    top_causas, top_carreteras, siniestros_clima,
    siniestros_tipo_via, fallecidos_sexo, fallecidos_edad,
    licencia_conductor, tipo_vehiculo, vehiculos_soat,
    obtener_anios, obtener_departamentos
)

# ── Paleta azul-gris ─────────────────────────────────────────
C1 = "#0C447C"
C2 = "#185FA5"
C3 = "#378ADD"
C4 = "#85B7EB"
C5 = "#B5D4F4"
CG1 = "#5F5E5A"
CG2 = "#B4B2A9"
CG3 = "#D3D1C7"

SCALE_BLUE  = [[0.0, C5], [0.4, C3], [0.7, C2], [1.0, C1]]
COLORS_PIE  = [C2, C3, C4, C5, CG2, CG3]

LB = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=32, b=8, l=0, r=0),
    font=dict(size=11, family="DM Sans"),
)

def _t(txt):
    return dict(text=txt, font=dict(size=9, family="DM Sans", color="#5A7FA8"), x=0)

def _xax(**kw):
    d = dict(showgrid=False, tickfont=dict(size=10, family="DM Sans"))
    d.update(kw); return d

def _yax(**kw):
    d = dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)",
             tickfont=dict(size=10, family="DM Sans"))
    d.update(kw); return d

def bar_h(df, x_col, y_col, height=300, title="", tick_size=10):
    """Barras horizontales ordenadas de mayor a menor."""
    df = df.sort_values(x_col, ascending=True)   # plotly invierte el eje
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col], orientation="h",
        marker=dict(color=df[x_col], colorscale=SCALE_BLUE, line=dict(width=0)),
        hovertemplate=f"<b>%{{y}}</b>: %{{x:,}}<extra></extra>",
    ))
    fig.update_layout(**LB, height=height, title=_t(title))
    fig.update_xaxes(_xax())
    fig.update_yaxes(_yax(tickfont=dict(size=tick_size, family="DM Sans")))
    return fig

def bar_v(df, x_col, y_col, height=260, title=""):
    """Barras verticales con etiqueta, ordenadas de mayor a menor."""
    df = df.sort_values(y_col, ascending=False)
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col],
        marker=dict(color=df[y_col], colorscale=SCALE_BLUE, line=dict(width=0)),
        hovertemplate=f"<b>%{{x}}</b>: %{{y:,}}<extra></extra>",
        text=df[y_col], textposition="outside",
        textfont=dict(size=10, color=C2),
    ))
    fig.update_layout(**LB, height=height, title=_t(title),
                      uniformtext_minsize=8, uniformtext_mode="hide")
    fig.update_xaxes(_xax())
    fig.update_yaxes(_yax(showgrid=False))
    return fig

def donut(df, labels_col, values_col, height=260, title=""):
    """Donut con leyenda lateral."""
    df = df.sort_values(values_col, ascending=False)
    fig = go.Figure(go.Pie(
        labels=df[labels_col], values=df[values_col],
        hole=0.48, textfont_size=10,
        marker=dict(colors=COLORS_PIE),
        hovertemplate="<b>%{label}</b>: %{value:,} (%{percent})<extra></extra>",
    ))
    fig.update_layout(**LB, height=height, title=_t(title),
                      showlegend=True,
                      legend=dict(font=dict(size=9, family="DM Sans"),
                                  orientation="v", x=1.02, y=0.5))
    return fig

def kpi_html(label, valor, sub, bg, color_val, color_label, color_sub):
    return f"""
    <div style="background:{bg};border-radius:10px;padding:14px 16px;height:100%">
      <div style="font-size:10px;font-weight:600;text-transform:uppercase;
                  letter-spacing:.06em;margin-bottom:6px;color:{color_label}">{label}</div>
      <div style="font-size:26px;font-weight:500;color:{color_val};line-height:1;margin-bottom:3px">{valor}</div>
      <div style="font-size:10px;color:{color_sub}">{sub}</div>
    </div>"""

# ── Página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Siniestralidad Vial — Perú",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown(aplicar_estilos(), unsafe_allow_html=True)

# ── Datos para filtros ───────────────────────────────────────
anios_raw  = obtener_anios()["anio"].astype(str).tolist()
deptos_raw = obtener_departamentos()["departamento"].tolist()

# ── Encabezado + filtros en la misma fila ────────────────────
h_col, f1, f2, f3 = st.columns([4, 1.5, 1.5, 0.8])

with h_col:
    st.markdown(f"""
    <div style="padding:4px 0 12px 0">
      <div style="font-size:10px;font-weight:600;letter-spacing:.10em;text-transform:uppercase;
                  color:{C3};margin-bottom:6px">MTC · Plataforma BI de Siniestralidad Vial</div>
      <div style="font-size:24px;font-weight:500;color:{C1};line-height:1.2;margin-bottom:4px">
        Siniestralidad vial en el Perú
      </div>
      <div style="font-size:12px;color:#999">
        Monitoreo de siniestros, víctimas y vehículos involucrados · Período {anios_raw[0] if anios_raw else '—'}–{anios_raw[-1] if anios_raw else '—'}
      </div>
    </div>
    """, unsafe_allow_html=True)

with f1:
    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
    anio_sel = st.selectbox("Año", ["Todos"] + anios_raw, label_visibility="visible")

with f2:
    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
    depto_sel = st.selectbox("Departamento", ["Todos"] + deptos_raw, label_visibility="visible")

with f3:
    st.markdown("<div style='margin-top:42px'></div>", unsafe_allow_html=True)
    if st.button("Limpiar", use_container_width=True):
        st.rerun()

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────────
kpis_df   = obtener_kpis(anio=anio_sel, departamento=depto_sel)
veh_df    = kpi_vehiculos(anio=anio_sel, departamento=depto_sel)

total_sin = int(kpis_df["total_siniestros"][0]  or 0)
total_fal = int(kpis_df["total_fallecidos"][0]   or 0)
total_les = int(kpis_df["total_lesionados"][0]   or 0)
total_veh = int(veh_df["total_vehiculos"][0]     or 0)

anio_min = anios_raw[0]  if anios_raw else "—"
anio_max = anios_raw[-1] if anios_raw else "—"
periodo  = anio_sel if anio_sel != "Todos" else f"{anio_min}–{anio_max}"

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_html(
        "Siniestros", f"{total_sin:,}", periodo,
        bg=C1, color_val="#FFFFFF", color_label="rgba(255,255,255,0.6)", color_sub="rgba(255,255,255,0.45)"
    ), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_html(
        "Fallecidos", f"{total_fal:,}", "período selec.",
        bg=C2, color_val="#FFFFFF", color_label="rgba(255,255,255,0.6)", color_sub="rgba(255,255,255,0.45)"
    ), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_html(
        "Lesionados", f"{total_les:,}", "período selec.",
        bg=C3, color_val="#FFFFFF", color_label="rgba(255,255,255,0.6)", color_sub="rgba(255,255,255,0.45)"
    ), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_html(
        "Vehículos involucrados", f"{total_veh:,}", "período selec.",
        bg=C4, color_val=C1, color_label="rgba(12,68,124,0.55)", color_sub="rgba(12,68,124,0.4)"
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── Pestañas ─────────────────────────────────────────────────
tab_res, tab_geo, tab_fac, tab_vic, tab_veh = st.tabs([
    "Resumen", "Geografía", "Factores", "Víctimas", "Vehículos"
])

# ══════════════════════════════════════════════════════════════
# RESUMEN
# ══════════════════════════════════════════════════════════════
with tab_res:

    df_anio = siniestros_por_anio(departamento=depto_sel)
    fig = go.Figure(go.Scatter(
        x=df_anio["anio"], y=df_anio["total"],
        mode="lines+markers",
        line=dict(color=C2, width=2.5),
        marker=dict(size=7, color="#fff", line=dict(color=C2, width=2)),
        fill="tozeroy", fillcolor="rgba(24,95,165,0.07)",
        hovertemplate="<b>%{x}</b>: %{y:,} siniestros<extra></extra>",
    ))
    fig.update_layout(**LB, height=200, title=_t("Evolución de siniestros por año"))
    fig.update_xaxes(_xax(dtick=1, tickformat="d"))
    fig.update_yaxes(_yax())
    st.plotly_chart(fig, use_container_width=True, key="res_evol")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(
            bar_h(top_departamentos(anio=anio_sel),
                  "total", "departamento", 300, "Top 10 departamentos"),
            use_container_width=True, key="res_dep")
    with c2:
        st.plotly_chart(
            bar_h(top_causas(anio=anio_sel, departamento=depto_sel),
                  "total", "causa", 300, "Top 10 causas", tick_size=9),
            use_container_width=True, key="res_cau")
    with c3:
        st.plotly_chart(
            bar_h(tipo_vehiculo(anio=anio_sel, departamento=depto_sel),
                  "total", "vehiculo", 300, "Tipo de vehículo", tick_size=9),
            use_container_width=True, key="res_veh")

# ══════════════════════════════════════════════════════════════
# GEOGRAFÍA
# ══════════════════════════════════════════════════════════════
with tab_geo:

    # Mapa
    df_mapa = obtener_mapa(anio=anio_sel, departamento=depto_sel)
    m = folium.Map(location=[-9.19, -75.01], zoom_start=5, tiles="CartoDB positron")
    coords = df_mapa[["latitud", "longitud"]].dropna().values.tolist()
    if coords:
        FastMarkerCluster(coords).add_to(m)
    for _, row in df_mapa.head(1000).iterrows():
        try:
            folium.CircleMarker(
                location=[row["latitud"], row["longitud"]],
                radius=4, color=C2, fill=True,
                fill_color=C2, fill_opacity=0.55,
                popup=folium.Popup(
                    f"<b>{row.get('DEPARTAMENTO','—')}</b> · {row.get('DISTRITO','—')}<br>"
                    f"Clase: {row.get('CLASE SINIESTRO','—')}<br>"
                    f"Vía: {row.get('TIPO DE VÍA','—')} · {row.get('ZONA','—')}<br>"
                    f"Clima: {row.get('CONDICIÓN CLIMÁTICA','—')}<br>"
                    f"Causa: {row.get('CAUSA FACTOR PRINCIPAL','—')}<br>"
                    f"Causa específica: {row.get('CAUSA ESPECÍFICA','—')}<br>"
                    f"Fallecidos: {row.get('CANTIDAD DE FALLECIDOS',0)} · "
                    f"Lesionados: {row.get('CANTIDAD DE LESIONADOS',0)}",
                    max_width=280
                )
            ).add_to(m)
        except Exception:
            pass
    st_folium(m, width="100%", height=420, returned_objects=[])

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(
            bar_h(top_departamentos(anio=anio_sel),
                  "total", "departamento", 300, "Top 10 departamentos"),
            use_container_width=True, key="geo_dep")
    with g2:
        st.plotly_chart(
            bar_h(top_distritos(anio=anio_sel, departamento=depto_sel),
                  "total", "distrito", 300, "Top 10 distritos"),
            use_container_width=True, key="geo_dis")

    df_car = top_carreteras(anio=anio_sel)
    st.plotly_chart(
        bar_v(df_car, "codigo_carretera", "total", 240,
              "Top 10 carreteras con más siniestros"),
        use_container_width=True, key="geo_car")

# ══════════════════════════════════════════════════════════════
# FACTORES
# ══════════════════════════════════════════════════════════════
with tab_fac:

    f1, f2, f3 = st.columns(3)
    with f1:
        st.plotly_chart(
            donut(siniestros_clima(anio=anio_sel, departamento=depto_sel),
                  "condicion_climatica", "total", 280, "Condición climática"),
            use_container_width=True, key="fac_cli")
    with f2:
        st.plotly_chart(
            bar_v(siniestros_tipo_via(anio=anio_sel, departamento=depto_sel),
                  "tipo_via", "total", 280, "Tipo de vía"),
            use_container_width=True, key="fac_via")
    with f3:
        st.plotly_chart(
            donut(vehiculos_soat(anio=anio_sel, departamento=depto_sel),
                  "posee_seguro", "total", 280, "Posee SOAT"),
            use_container_width=True, key="fac_soat")

    st.plotly_chart(
        bar_h(top_causas(anio=anio_sel, departamento=depto_sel),
              "total", "causa", 300, "Top 10 causas de siniestros", tick_size=10),
        use_container_width=True, key="fac_cau")

# ══════════════════════════════════════════════════════════════
# VÍCTIMAS
# ══════════════════════════════════════════════════════════════
with tab_vic:

    v1, v2 = st.columns(2)
    with v1:
        # Barra apilada horizontal — sexo
        df_sex = fallecidos_sexo(anio=anio_sel, departamento=depto_sel)
        df_sex = df_sex.sort_values("total", ascending=False)
        colors_sex = [C2, C4, CG2, CG3]
        fig = go.Figure()
        for i, (_, row) in enumerate(df_sex.iterrows()):
            fig.add_trace(go.Bar(
                name=str(row["sexo"]),
                x=[row["total"]], y=["Fallecidos"],
                orientation="h",
                marker=dict(color=colors_sex[i % len(colors_sex)],
                            line=dict(width=0)),
                hovertemplate=f"<b>{row['sexo']}</b>: {row['total']:,}<extra></extra>",
            ))
        fig.update_layout(**LB, height=140, title=_t("Fallecidos por sexo"),
                          barmode="stack", showlegend=True,
                          legend=dict(font=dict(size=10, family="DM Sans"),
                                      orientation="h", y=-0.5))
        fig.update_xaxes(_xax())
        fig.update_yaxes(_yax(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, key="vic_sex")

    with v2:
        st.plotly_chart(
            bar_v(fallecidos_edad(anio=anio_sel, departamento=depto_sel),
                  "rango_edad", "total", 260, "Fallecidos por rango de edad"),
            use_container_width=True, key="vic_edad")

    st.plotly_chart(
        donut(licencia_conductor(anio=anio_sel, departamento=depto_sel),
              "posee_licencia", "total", 280, "Posee licencia de conducir"),
        use_container_width=True, key="vic_lic")

# ══════════════════════════════════════════════════════════════
# VEHÍCULOS
# ══════════════════════════════════════════════════════════════
with tab_veh:

    st.plotly_chart(
        bar_h(tipo_vehiculo(anio=anio_sel, departamento=depto_sel),
              "total", "vehiculo", 380, "Tipo de vehículo involucrado", tick_size=10),
        use_container_width=True, key="veh_tipo")

    vh1, vh2 = st.columns(2)
    with vh1:
        st.plotly_chart(
            donut(vehiculos_soat(anio=anio_sel, departamento=depto_sel),
                  "posee_seguro", "total", 280, "Posee SOAT"),
            use_container_width=True, key="veh_soat")
    with vh2:
        df_top5 = tipo_vehiculo(anio=anio_sel, departamento=depto_sel).head(5)
        fig = go.Figure(go.Pie(
            labels=df_top5["vehiculo"], values=df_top5["total"],
            hole=0.48, textfont_size=10,
            marker=dict(colors=[C1, C2, C3, C4, C5]),
            hovertemplate="<b>%{label}</b>: %{value:,} (%{percent})<extra></extra>",
        ))
        fig.update_layout(**LB, height=280, title=_t("Distribución top 5 vehículos"),
                          showlegend=True,
                          legend=dict(font=dict(size=9, family="DM Sans"),
                                      orientation="v", x=1.02, y=0.5))
        st.plotly_chart(fig, use_container_width=True, key="veh_top5")

# ── Footer ────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Plataforma BI de Siniestralidad Vial · Perú · Ministerio de Transportes y Comunicaciones
</div>""", unsafe_allow_html=True)