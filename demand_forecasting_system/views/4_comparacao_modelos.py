import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src import services, ui

ui.hero(
    "Comparação de modelos",
    "Teste cego (out-of-sample): os modelos são treinados sem conhecer o final do histórico e avaliados "
    "contra a realidade escondida. Vence quem erra menos em dados que nunca viu.",
    eyebrow="Módulo 04 · Planejamento",
    chips=["MAE", "RMSE", "MAPE", "WAPE", "Viés", "Tracking Signal"],
)
df = ui.require_data()
skus = sorted(df["sku"].unique())

with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 3], vertical_alignment="bottom")
    sku = c1.selectbox("Produto (SKU)", skus, key="cmp_sku")
    freq_label = c2.segmented_control("Granularidade", list(services.FREQS), default="Mensal", key="cmp_freq") or "Mensal"
    freq = services.FREQS[freq_label]
    series = services.series_for(df, sku, freq)
    max_h = max(1, min(services.MAX_H[freq], len(series) - 4))
    h = c3.slider(f"Períodos de teste ({services.UNIT[freq]})", 1, max_h, min(services.DEFAULT_H[freq], max_h), key=f"cmp_h_{freq}")

if len(series) <= h + 3:
    st.error(f"Histórico insuficiente: a base tem {len(series)} períodos e o teste usa {h}. Reduza os períodos de teste.", icon=":material/error:")
    st.stop()

with st.spinner("Executando backtesting de todos os modelos…"):
    metricas, fcasts, train, test = services.backtest(series, h, services.SEASON[freq])

if metricas.empty:
    st.error("Nenhum modelo conseguiu calcular o horizonte selecionado.", icon=":material/error:")
    st.stop()

top = metricas.iloc[0]
naive = metricas.loc[metricas["Modelo"] == "Naive"]
ganho = ""
if not naive.empty and top["Modelo"] != "Naive" and naive["WAPE (%)"].iloc[0] > 0:
    g = (naive["WAPE (%)"].iloc[0] - top["WAPE (%)"]) / naive["WAPE (%)"].iloc[0] * 100
    ganho = f" · {ui.fmt_num(g, 0)}% menos erro que o Naive"

c1, c2 = st.columns([2, 3], gap="medium")
with c1:
    ui.winner("Modelo vencedor", f"🏆 {top['Modelo']}", f"WAPE de {ui.fmt_pct(top['WAPE (%)'])} em {h} {services.UNIT[freq]} de teste{ganho}")
    st.write("")
    m1, m2 = st.columns(2)
    m1.metric("MAE", ui.fmt_num(top["MAE"]), help="Erro médio absoluto, em unidades.")
    m2.metric("Viés", ui.fmt_num(top["Viés (Bias)"], 0), help="Soma (previsto − real). Positivo = superestima.")
    bias = top["Viés (Bias)"]
    if abs(top["Tracking Signal"]) > 4:
        ui.callout(f"Tracking signal de <b>{ui.fmt_num(top['Tracking Signal'])}</b> — o modelo apresenta viés sistemático; monitore.", "amber", "⚠️")
    else:
        ui.callout(f"Tracking signal de <b>{ui.fmt_num(top['Tracking Signal'])}</b> — dentro do controle (±4).", "green", "✅")
with c2, st.container(border=True, height="stretch"):
    st.markdown("**Ranking de erro (WAPE)** — quanto menor, melhor")
    rk = metricas.sort_values("WAPE (%)", ascending=True)
    cores = [ui.ACCENT if m == top["Modelo"] else "#C7D2FE" for m in rk["Modelo"]]
    fig = go.Figure(go.Bar(y=rk["Modelo"], x=rk["WAPE (%)"], orientation="h", marker=dict(color=cores, cornerradius=6),
                           text=[ui.fmt_pct(v) for v in rk["WAPE (%)"]], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(hovermode="closest", margin=dict(l=8, r=40, t=10, b=8), xaxis_title="WAPE (%)")
    ui.chart(fig, height=300)

ui.section("Visualização do teste cego", "Histórico de treino, realidade escondida e as 3 melhores previsões.")
fig = go.Figure()
trecho = train.iloc[-max(h * 3, 24):]
fig.add_trace(go.Scatter(x=trecho.index, y=trecho.values, name="Treino", line=dict(color="#334155", width=2)))
fig.add_trace(go.Scatter(x=test.index, y=test.values, name="Realidade (teste)", mode="lines+markers",
                         line=dict(color="#94A3B8", width=3), marker=dict(size=7)))
fig.add_vrect(x0=test.index[0], x1=test.index[-1], fillcolor="rgba(148,163,184,.10)", line_width=0,
              annotation_text="janela de teste", annotation_position="top left", annotation_font=dict(size=11, color=ui.MUTED))
for i, nome in enumerate(metricas.head(3)["Modelo"]):
    fig.add_trace(go.Scatter(x=test.index, y=fcasts[nome], name=f"{i + 1}º · {nome}", mode="lines",
                             line=dict(color=[ui.ACCENT, ui.PRIMARY, "#F59E0B"][i], width=3.2 if i == 0 else 2, dash="solid" if i == 0 else "dash")))
fig.update_layout(yaxis_title="Quantidade")
ui.chart(fig, height=430)

ui.section("Tabela completa de métricas")
st.dataframe(
    metricas[["Posição", "Modelo", "Acurácia (%)", "WAPE (%)", "MAE", "RMSE", "MAPE (%)", "Viés (Bias)", "Tracking Signal"]],
    hide_index=True,
    width="stretch",
    column_config={
        "Posição": st.column_config.NumberColumn("#", width="small"),
        "Acurácia (%)": st.column_config.ProgressColumn("Acurácia", min_value=0, max_value=100, format="%.1f%%"),
        "WAPE (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "MAE": st.column_config.NumberColumn(format="%.1f"),
        "RMSE": st.column_config.NumberColumn(format="%.1f"),
        "MAPE (%)": st.column_config.NumberColumn(format="%.1f%%", help="Ignora períodos com demanda zero."),
        "Viés (Bias)": st.column_config.NumberColumn(format="%.0f"),
        "Tracking Signal": st.column_config.NumberColumn(format="%.2f"),
    },
)
with st.expander("Como ler as métricas", icon=":material/school:"):
    st.markdown(
        "- **WAPE** — erro absoluto total ÷ demanda total. Robusto para itens com zeros; métrica principal do ranking.\n"
        "- **MAE / RMSE** — erro médio em unidades; o RMSE penaliza mais os grandes erros.\n"
        "- **MAPE** — erro percentual médio (ignora períodos zerados).\n"
        "- **Viés** — positivo indica superestimação (excesso de estoque); negativo, subestimação (ruptura).\n"
        "- **Tracking Signal** — viés acumulado ÷ MAE. Fora de ±4 indica modelo descalibrado."
    )
