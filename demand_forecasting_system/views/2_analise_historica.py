import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import services, ui

ui.hero(
    "Análise histórica",
    "Entenda o comportamento de cada produto antes de prever: volume, variabilidade, tendência, "
    "sazonalidade e classificação automática do perfil de demanda.",
    eyebrow="Módulo 02 · Dados",
)
df = ui.require_data()

skus = sorted(df["sku"].unique())
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 3], vertical_alignment="bottom")
    sku = c1.selectbox("Produto (SKU)", skus, key="hist_sku")
    freq_label = c2.segmented_control("Granularidade", list(services.FREQS), default="Semanal", key="hist_freq") or "Semanal"
    freq = services.FREQS[freq_label]
    full = services.series_for(df, sku, freq)
    dmin, dmax = full.index.min().date(), full.index.max().date()
    periodo = c3.slider("Janela de análise", min_value=dmin, max_value=dmax, value=(dmin, dmax), format="MM/YYYY", key=f"hist_win_{sku}_{freq}")

serie = full.loc[str(periodo[0]):str(periodo[1])]
ind, classe, motivo = services.profile(df, sku, "W")

# ---------- Perfil ----------
st.html(
    f'<div style="display:flex;align-items:center;gap:12px;margin:.6rem 0 .9rem 0;flex-wrap:wrap">'
    f'<span style="font-size:1.25rem;font-weight:800;color:#0F172A;letter-spacing:-.01em">{ui._e(sku)}</span>'
    f'{ui.badge_html("Perfil: " + classe, ui.PROFILE_TONE.get(classe, "slate"))}'
    f'<span class="gd-muted">{ui._e(motivo)} · classificação sobre a série semanal completa</span></div>'
)

media = serie.mean()
cv = serie.std() / media if media > 0 else 0
meio = len(serie) // 2
m1, m2 = serie.iloc[:meio].mean(), serie.iloc[meio:].mean()
cresc = (m2 - m1) / m1 * 100 if m1 > 0 else 0
zerados = (serie == 0).mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Volume no período", ui.fmt_int(serie.sum()), chart_data=serie.tail(52).tolist(), chart_type="area")
k2.metric(f"Média por {services.UNIT_SING[freq]}", ui.fmt_num(media))
k3.metric("Pico", ui.fmt_int(serie.max()), help=f"Em {ui.fmt_date(serie.idxmax())}")
k4.metric("Variabilidade (CV)", ui.fmt_num(cv, 2), help="Desvio-padrão ÷ média. < 0,2 estável · > 0,5 irregular.")
k5.metric("Crescimento", ui.fmt_pct(cresc, signed=True), delta=f"{ui.fmt_num(zerados, 0)}% períodos zerados", delta_color="off", delta_arrow="off",
          help="Média da 2ª metade da janela vs. 1ª metade.")

tab1, tab2, tab3, tab4 = st.tabs([":material/show_chart: Série temporal", ":material/calendar_month: Sazonalidade", ":material/bar_chart: Distribuição", ":material/compare: Comparar SKUs"])

with tab1:
    janela = {"D": 28, "W": 8, "ME": 3}[freq]
    mm = serie.rolling(janela, min_periods=1).mean()
    x = np.arange(len(serie))
    tendencia = np.poly1d(np.polyfit(x, serie.values, 1))(x) if len(serie) > 1 else serie.values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie.index, y=serie.values, name="Demanda real", mode="lines",
                             line=dict(color=ui.PRIMARY, width=1.6)))
    fig.add_trace(go.Scatter(x=serie.index, y=mm, name=f"Média móvel ({janela})", mode="lines", line=dict(color=ui.ACCENT, width=2.6)))
    fig.add_trace(go.Scatter(x=serie.index, y=tendencia, name="Tendência linear", mode="lines", line=dict(color="#F59E0B", width=2, dash="dash")))
    fig.add_hline(y=media, line=dict(color="#94A3B8", width=1, dash="dot"), annotation_text=f"média {ui.fmt_num(media)}", annotation_position="top left",
                  annotation_font=dict(size=11, color=ui.MUTED))
    fig.update_layout(yaxis_title="Quantidade")
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.06, bgcolor="#F1F5F9"))
    ui.chart(fig, height=440)

with tab2:
    daily = df.loc[(df["sku"] == sku)].set_index("data")["quantidade_vendida"].loc[str(periodo[0]):str(periodo[1])]
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        piv = daily.resample("ME").sum().to_frame("q")
        piv["ano"], piv["mes"] = piv.index.year, piv.index.month
        mat = piv.pivot_table(index="ano", columns="mes", values="q", aggfunc="sum").reindex(columns=range(1, 13))
        fig = go.Figure(go.Heatmap(z=mat.values, x=meses, y=[str(a) for a in mat.index], colorscale=[[0, "#EEF2FF"], [0.5, "#818CF8"], [1, "#312E81"]],
                                   hovertemplate="%{y} · %{x}<br>%{z:,.0f} un.<extra></extra>", xgap=3, ygap=3,
                                   colorbar=dict(thickness=10, outlinewidth=0)))
        fig.update_layout(title=dict(text="Mapa de calor · volume mensal por ano", font=dict(size=14)), hovermode="closest")
        fig.update_yaxes(autorange="reversed", type="category")
        ui.chart(fig, height=360)
    with c2:
        dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        dow = daily.groupby(daily.index.dayofweek).mean().reindex(range(7))
        idx = dow / dow.mean() * 100 if dow.mean() else dow
        fig = go.Figure(go.Bar(x=dias, y=idx.values, marker=dict(color=[ui.ACCENT if v >= 100 else "#CBD5E1" for v in idx.values], cornerradius=6),
                               hovertemplate="%{x}: índice %{y:.0f}<extra></extra>"))
        fig.add_hline(y=100, line=dict(color="#94A3B8", dash="dot", width=1))
        fig.update_layout(title=dict(text="Índice por dia da semana (100 = média)", font=dict(size=14)), hovermode="closest")
        ui.chart(fig, height=360)

with tab3:
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        fig = px.histogram(serie.to_frame("q"), x="q", nbins=30, color_discrete_sequence=[ui.PRIMARY])
        fig.update_traces(marker=dict(cornerradius=4))
        fig.update_layout(title=dict(text=f"Histograma de demanda ({freq_label.lower()})", font=dict(size=14)), xaxis_title="Quantidade", yaxis_title="Frequência", hovermode="closest")
        ui.chart(fig, height=360)
    with c2:
        trimestres = serie.to_frame("q")
        trimestres["Trimestre"] = "T" + trimestres.index.quarter.astype(str)
        fig = px.box(trimestres, x="Trimestre", y="q", color="Trimestre", color_discrete_sequence=ui.PALETTE, category_orders={"Trimestre": ["T1", "T2", "T3", "T4"]})
        fig.update_layout(title=dict(text="Dispersão por trimestre", font=dict(size=14)), showlegend=False, yaxis_title="Quantidade", hovermode="closest")
        ui.chart(fig, height=360)

with tab4:
    escolhidos = st.multiselect("SKUs para comparar", skus, default=skus[: min(3, len(skus))], key="hist_cmp")
    normalizar = st.toggle("Normalizar (índice base 100)", value=True, help="Facilita comparar produtos com escalas diferentes.")
    fig = go.Figure()
    for i, s in enumerate(escolhidos):
        y = services.series_for(df, s, freq).loc[str(periodo[0]):str(periodo[1])]
        if normalizar and y.mean() > 0:
            y = y / y.mean() * 100
        fig.add_trace(go.Scatter(x=y.index, y=y.values, name=s, mode="lines", line=dict(width=2, color=ui.PALETTE[i % len(ui.PALETTE)])))
    fig.update_layout(yaxis_title="Índice (100 = média)" if normalizar else "Quantidade")
    ui.chart(fig, height=420)
