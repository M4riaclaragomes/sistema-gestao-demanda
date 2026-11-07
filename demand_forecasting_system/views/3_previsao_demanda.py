import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import services, ui

ui.hero(
    "Previsão de demanda",
    "Projete o futuro de cada produto com 7 modelos estatísticos. O sistema recomenda o método com melhor "
    "desempenho no backtesting e exibe faixas de confiança para apoiar decisões de estoque.",
    eyebrow="Módulo 03 · Planejamento",
)
df = ui.require_data()
skus = sorted(df["sku"].unique())

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([2, 2.2, 2.8, 1.4], vertical_alignment="bottom")
    sku = c1.selectbox("Produto (SKU)", skus, key="prev_sku")
    freq_label = c2.segmented_control("Granularidade", list(services.FREQS), default="Mensal", key="prev_freq") or "Mensal"
    freq = services.FREQS[freq_label]
    h = c3.slider(f"Horizonte ({services.UNIT[freq]})", 1, services.MAX_H[freq], services.DEFAULT_H[freq], key=f"prev_h_{freq}")
    conf = c4.segmented_control("Confiança", ["80%", "95%"], default="80%", key="prev_conf") or "80%"

series = services.series_for(df, sku, freq)
if len(series) < 6:
    st.error("Histórico insuficiente para previsões estatísticas (mínimo de 6 períodos nessa granularidade).", icon=":material/error:")
    st.stop()

with st.spinner("Ajustando modelos estatísticos…"):
    resultados = services.run_models(series, h, services.SEASON[freq])
    recomendado, ranking = services.best_model(series, freq)

modelos = list(resultados)
padrao = recomendado if recomendado in modelos else modelos[0]
opcoes = {m: (f"★ {m}" if m == recomendado else m) for m in modelos}
modelo = st.pills("Modelo estatístico", modelos, default=padrao, format_func=lambda m: opcoes[m], key=f"prev_model_{sku}_{freq}") or padrao
st.caption(f":material/info: {services.MODEL_INFO.get(modelo, '')}" + (" · **Recomendado pelo backtesting.**" if modelo == recomendado else ""))

r = resultados[modelo]
fc, sigma = r["forecast"], r["sigma"]
z = 1.2816 if conf == "80%" else 1.96
passos = np.sqrt(np.arange(1, h + 1))
inf = np.maximum(0, fc - z * sigma * np.minimum(passos, 3))
sup = fc + z * sigma * np.minimum(passos, 3)
datas = services.future_index(series, h, freq)

ultimo = series.iloc[-h:].sum() if len(series) >= h else np.nan
total = fc.sum()
var = (total - ultimo) / ultimo * 100 if ultimo else np.nan
wape = None
if not ranking.empty and modelo in set(ranking["Modelo"]):
    wape = float(ranking.loc[ranking["Modelo"] == modelo, "WAPE (%)"].iloc[0])

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Demanda prevista ({h} {services.UNIT[freq]})", ui.fmt_int(total), delta=ui.fmt_pct(var, signed=True) + " vs. período anterior" if not np.isnan(var) else None)
k2.metric(f"Média por {services.UNIT_SING[freq]}", ui.fmt_num(fc.mean()))
k3.metric(f"Faixa {conf} (total)", f"{ui.fmt_int(inf.sum())} – {ui.fmt_int(sup.sum())}")
k4.metric("Acurácia no backtest", ui.fmt_pct(100 - wape, 1) if wape is not None and not np.isnan(wape) else "—",
          help="100% − WAPE medido em teste cego sobre o final do histórico.")

# ---------- Gráfico ----------
hist = series.iloc[-max(h * 4, 24):]
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(datas) + list(datas[::-1]), y=list(sup) + list(inf[::-1]), fill="toself", fillcolor="rgba(20,184,166,.14)",
                         mode="lines", line=dict(width=0), name=f"Intervalo {conf}", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Histórico", mode="lines", line=dict(color="#334155", width=2)))
if r["fit"] is not None:
    fit = r["fit"].loc[hist.index]
    fig.add_trace(go.Scatter(x=fit.index, y=fit.values, name="Ajuste do modelo", mode="lines", line=dict(color="#F59E0B", width=1.6, dash="dot"), visible="legendonly"))
fig.add_trace(go.Scatter(x=[hist.index[-1], *datas], y=[hist.values[-1], *fc], name=f"Previsão · {modelo}", mode="lines+markers",
                         line=dict(color=ui.ACCENT, width=3), marker=dict(size=6, line=dict(color="#fff", width=1.5))))
fig.add_vline(x=hist.index[-1], line=dict(color="#CBD5E1", width=1, dash="dash"))
fig.add_annotation(x=hist.index[-1], y=1, yref="paper", text="início da previsão", showarrow=False, xanchor="left", xshift=6, font=dict(size=11, color=ui.MUTED))
fig.update_layout(yaxis_title="Quantidade")
ui.chart(fig, height=460)

# ---------- Tabela e exportação ----------
tab_df = pd.DataFrame({"Período": datas, "Previsão": np.round(fc, 0), f"Limite inferior ({conf})": np.round(inf, 0), f"Limite superior ({conf})": np.round(sup, 0)})
c1, c2 = st.columns([3, 1], gap="medium")
with c1:
    with st.expander("Tabela da previsão", icon=":material/table:", expanded=False):
        st.dataframe(tab_df, hide_index=True, width="stretch",
                     column_config={"Período": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                    "Previsão": st.column_config.NumberColumn(format="localized")})
with c2:
    st.download_button("Exportar Excel", services.to_excel({"Previsao": tab_df}), f"previsao_{sku}_{freq_label.lower()}.xlsx",
                       icon=":material/download:", type="primary", width="stretch")
    st.download_button("Exportar CSV", tab_df.to_csv(index=False).encode("utf-8"), f"previsao_{sku}.csv", "text/csv", icon=":material/csv:", width="stretch")

with st.expander("Comparar todos os modelos neste horizonte", icon=":material/stacked_line_chart:"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Histórico", line=dict(color="#334155", width=2)))
    for i, (nome, res) in enumerate(resultados.items()):
        fig.add_trace(go.Scatter(x=datas, y=res["forecast"], name=nome, mode="lines",
                                 line=dict(width=3 if nome == modelo else 1.6, color=ui.PALETTE[i % len(ui.PALETTE)])))
    ui.chart(fig, height=380, key="prev_all")

with st.expander("Entenda os modelos", icon=":material/school:"):
    for nome, desc in services.MODEL_INFO.items():
        st.markdown(f"- **{nome}** — {desc}")
    st.caption("As faixas de confiança são estimadas a partir do desvio-padrão dos resíduos do ajuste no histórico.")
