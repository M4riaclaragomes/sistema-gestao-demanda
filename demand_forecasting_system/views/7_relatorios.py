from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import services, ui

ui.hero(
    "Relatórios e laudos",
    "O sistema analisa o histórico, executa o backtesting de todos os modelos e redige um laudo gerencial "
    "automático — pronto para embasar reuniões de S&OP.",
    eyebrow="Módulo 10 · Gestão",
)
df = ui.require_data()
skus = sorted(df["sku"].unique())


def recomendacoes(classe: str, met: dict, modelo: str, total_real: float) -> list[str]:
    rec = []
    textos = {
        "Crescente": "O produto apresenta <b>tendência clara de crescimento</b>; revise níveis de estoque de segurança e capacidade de reposição.",
        "Decrescente": "O produto apresenta <b>tendência de queda</b>; avalie redução de compras e risco de obsolescência.",
        "Estável": "A demanda é <b>estável</b>; modelos de média móvel ou suavização simples tendem a performar muito bem.",
        "Intermitente": "Demanda <b>intermitente</b> (muitos períodos zerados); o método de Croston e o WAPE são os mais indicados.",
        "Irregular": "Demanda <b>irregular</b>, com picos; considere estoque de segurança maior e revisão frequente do plano.",
        "Sazonal/Variável": "Demanda com <b>variação moderada/sazonal</b>; antecipe a cobertura para os períodos de pico.",
    }
    if classe in textos:
        rec.append(textos[classe])
    bias_pct = met.get("Viés (Bias)", 0) / total_real * 100 if total_real else 0
    if bias_pct > 5:
        rec.append(f"⚠️ O modelo tende a <b>superestimar</b> a demanda ({ui.fmt_pct(bias_pct, signed=True)}) — risco de excesso de estoque.")
    elif bias_pct < -5:
        rec.append(f"⚠️ O modelo tende a <b>subestimar</b> a demanda ({ui.fmt_pct(bias_pct, signed=True)}) — risco de ruptura e venda perdida.")
    else:
        rec.append(f"O viés do modelo está <b>sob controle</b> ({ui.fmt_pct(bias_pct, signed=True)} do volume real no teste).")
    rec.append(f"🎯 Com base no backtesting, recomenda-se adotar o método <b>{modelo}</b> no planejamento.")
    return rec


tab1, tab2 = st.tabs([":material/description: Laudo por produto", ":material/inventory: Visão do portfólio"])

with tab1:
    with st.container(border=True):
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        sku = c1.selectbox("Produto para o laudo", skus, key="rel_sku")
        gerar = c2.button("Gerar laudo", type="primary", icon=":material/auto_awesome:", width="stretch")
    if gerar:
        st.session_state["rel_gerado"] = sku

    if st.session_state.get("rel_gerado") != sku:
        st.info("Selecione o produto e clique em **Gerar laudo**.", icon=":material/touch_app:")
    else:
        with st.status("Compilando laudo…", expanded=False) as status:
            st.write("Agregando histórico semanal…")
            series = services.series_for(df, sku, "W")
            ind, classe, motivo = services.profile(df, sku, "W")
            st.write("Executando backtesting de 7 modelos…")
            n = len(series)
            h_bt = min(max(int(n * 0.2), 3), 12)
            metricas, fcasts, train, test = services.backtest(series, h_bt, 52)
            melhor = metricas.iloc[0].to_dict() if not metricas.empty else {}
            modelo = melhor.get("Modelo", "—")
            st.write("Projetando as próximas 12 semanas…")
            proj = services.run_models(series, 12, 52).get(modelo, {}).get("forecast", np.zeros(12))
            status.update(label="Laudo pronto", state="complete")

        st.html(
            f'<div class="gd-report">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap">'
            f'<div><div class="gd-card-title">Laudo automático · {datetime.now():%d/%m/%Y %H:%M}</div>'
            f'<div style="font-size:1.4rem;font-weight:800;color:#0F172A;letter-spacing:-.02em">{ui._e(sku)}</div></div>'
            f'<div style="display:flex;gap:8px">{ui.badge_html("Perfil: " + classe, ui.PROFILE_TONE.get(classe, "slate"))}'
            f'{ui.badge_html("Modelo: " + str(modelo), "teal")}</div></div>'
            f'<h4 style="margin-top:1rem">Recomendações</h4><ul>{"".join(f"<li>{r}</li>" for r in recomendacoes(classe, melhor, modelo, float(test.sum())))}</ul></div>'
        )
        st.write("")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Volume total", ui.fmt_int(ind["total"]))
        k2.metric("Média semanal", ui.fmt_num(ind["media"]))
        k3.metric("CV", ui.fmt_num(ind["cv"], 2))
        k4.metric("Acurácia validada", ui.fmt_pct(100 - melhor.get("WAPE (%)", np.nan)), help="100% − WAPE no teste cego")
        k5.metric("Previsão 12 semanas", ui.fmt_int(proj.sum()))

        datas = services.future_index(series, 12, "W")
        hist = series.iloc[-52:]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Últimas 52 semanas", line=dict(color="#334155", width=2)))
        fig.add_trace(go.Scatter(x=[hist.index[-1], *datas], y=[hist.values[-1], *proj], name=f"Projeção · {modelo}", line=dict(color=ui.ACCENT, width=3)))
        ui.chart(fig, height=340)

        resumo = pd.DataFrame([
            {"Indicador": "SKU", "Valor": sku}, {"Indicador": "Perfil", "Valor": classe}, {"Indicador": "Motivo", "Valor": motivo},
            {"Indicador": "Volume total", "Valor": ind["total"]}, {"Indicador": "Média semanal", "Valor": round(ind["media"], 2)},
            {"Indicador": "Coef. variação", "Valor": round(ind["cv"], 3)}, {"Indicador": "Crescimento (%)", "Valor": round(ind["crescimento_pct"], 2)},
            {"Indicador": "Modelo recomendado", "Valor": modelo}, {"Indicador": "WAPE (%)", "Valor": round(melhor.get("WAPE (%)", np.nan), 2)},
        ])
        resumo["Valor"] = resumo["Valor"].astype(str)
        previsao = pd.DataFrame({"Semana": datas, "Previsão": np.round(proj)})
        c1, c2, c3 = st.columns(3)
        c1.download_button("Laudo completo (Excel)", services.to_excel({"Resumo": resumo, "Metricas": metricas, "Previsao": previsao, "Historico": series.reset_index()}),
                           f"laudo_{sku}.xlsx", icon=":material/download:", type="primary", width="stretch")
        c2.download_button("Histórico semanal (CSV)", series.reset_index().to_csv(index=False).encode("utf-8"), f"historico_{sku}.csv", "text/csv",
                           icon=":material/csv:", width="stretch")
        texto = f"LAUDO DE DEMANDA — {sku}\nGerado em {datetime.now():%d/%m/%Y %H:%M}\n\n" + "\n".join(
            "- " + r.replace("<b>", "").replace("</b>", "") for r in recomendacoes(classe, melhor, modelo, float(test.sum())))
        c3.download_button("Laudo em texto (TXT)", texto.encode("utf-8"), f"laudo_{sku}.txt", "text/plain", icon=":material/article:", width="stretch")

with tab2:
    st.markdown('<div class="gd-muted">Backtesting consolidado de todos os produtos (base semanal) com o modelo vencedor de cada um.</div>', unsafe_allow_html=True)
    rows = []
    prog = st.progress(0, text="Avaliando portfólio…")
    for i, s in enumerate(skus):
        serie = services.series_for(df, s, "W")
        _, classe, _ = services.profile(df, s, "W")
        modelo, met = services.best_model(serie, "W")
        top = met.iloc[0] if not met.empty else {}
        rows.append({"SKU": s, "Perfil": classe, "Modelo recomendado": modelo or "—",
                     "Acurácia (%)": float(100 - top["WAPE (%)"]) if len(top) else np.nan,
                     "Viés": float(top["Viés (Bias)"]) if len(top) else np.nan,
                     "Volume 52 sem.": float(serie.tail(52).sum()), "Tendência": serie.tail(52).tolist()})
        prog.progress((i + 1) / len(skus), text=f"Avaliando {s}…")
    prog.empty()
    port = pd.DataFrame(rows)
    st.dataframe(
        port, hide_index=True, width="stretch",
        column_config={
            "Acurácia (%)": st.column_config.ProgressColumn("Acurácia", min_value=0, max_value=100, format="%.1f%%"),
            "Viés": st.column_config.NumberColumn(format="%.0f"),
            "Volume 52 sem.": st.column_config.NumberColumn(format="localized"),
            "Tendência": st.column_config.LineChartColumn("Últimas 52 semanas", width="medium"),
        },
    )
    st.download_button("Exportar visão do portfólio (Excel)", services.to_excel({"Portfolio": port.drop(columns="Tendência")}), "portfolio.xlsx",
                       icon=":material/download:", type="primary")
