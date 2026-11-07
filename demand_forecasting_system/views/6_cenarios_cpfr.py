import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import services, ui
from src.scenario_builder import ScenarioBuilder

ui.hero(
    "Cenários e CPFR",
    "Simule choques de mercado e promoções sobre a previsão base e construa o plano de consenso com "
    "clientes e fornecedores (Collaborative Planning, Forecasting and Replenishment).",
    eyebrow="Módulos 08 e 09 · Planejamento",
)
df = ui.require_data()
skus = sorted(df["sku"].unique())

tab1, tab2 = st.tabs([":material/tune: Simulação de cenários", ":material/handshake: CPFR · gestão colaborativa"])

# ======================================================================================
# Cenários
# ======================================================================================
with tab1:
    with st.container(border=True):
        c1, c2 = st.columns([2, 3], vertical_alignment="bottom")
        sku = c1.selectbox("Produto", skus, key="cen_sku")
        h = c2.slider("Semanas no futuro", 4, 52, 12, key="cen_h")
        series = services.series_for(df, sku, "W")
        resultados = services.run_models(series, h, 52)
        modelos = list(resultados)
        base_model = st.pills("Previsão base", modelos, default="Média Móvel" if "Média Móvel" in modelos else modelos[0], key="cen_model") or modelos[0]

        c4, c5, c6 = st.columns([3, 3, 2], vertical_alignment="bottom")
        choque = c4.slider("Choque de demanda global (%)", -50, 100, 0, step=5, key="cen_choque",
                           help="Efeito macro em todo o horizonte (ex.: recessão −15%, nova praça +20%).")
        if "cen_promo" in st.session_state:
            st.session_state["cen_promo"] = [w for w in st.session_state["cen_promo"] if w <= h]
        semanas = c5.multiselect("Semanas com promoção", list(range(1, h + 1)), default=[w for w in (4, 8) if w <= h],
                                 format_func=lambda i: f"Semana {i}", key="cen_promo", placeholder="Selecione semanas…")
        impacto = c6.number_input("Uplift da promoção (%)", 0, 300, 30, step=10, key="cen_uplift")

    base_fc = resultados[base_model]["forecast"]
    cen = ScenarioBuilder.aplicar_simulacao_linear(base_fc, choque)
    cen = ScenarioBuilder.aplicar_simulacao_promocao(cen, [s - 1 for s in semanas], impacto)
    datas = services.future_index(series, h, "W")

    vb, vc = base_fc.sum(), cen.sum()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Volume base", ui.fmt_int(vb))
    k2.metric("Volume do cenário", ui.fmt_int(vc), delta=ui.fmt_pct((vc - vb) / vb * 100 if vb else 0, signed=True))
    k3.metric("Unidades incrementais", ui.fmt_int(vc - vb), delta_color="off")
    k4.metric("Pico semanal", ui.fmt_int(cen.max()), help=f"Semana de {ui.fmt_date(datas[int(np.argmax(cen))])}")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=datas, y=cen - base_fc, name="Efeito do cenário", marker=dict(color=["#14B8A6" if v >= 0 else "#F87171" for v in cen - base_fc], cornerradius=4),
                         opacity=0.35, yaxis="y2", hovertemplate="%{y:+,.0f} un.<extra>Efeito</extra>"))
    fig.add_trace(go.Scatter(x=datas, y=base_fc, name=f"Base · {base_model}", mode="lines", line=dict(color="#94A3B8", dash="dash", width=2)))
    fig.add_trace(go.Scatter(x=datas, y=cen, name="Cenário simulado", mode="lines+markers", line=dict(color=ui.PRIMARY, width=3),
                             marker=dict(size=[11 if (i + 1) in semanas else 6 for i in range(h)], color=[ui.ACCENT if (i + 1) in semanas else ui.PRIMARY for i in range(h)],
                                         line=dict(color="#fff", width=1.5))))
    fig.update_layout(yaxis=dict(title="Quantidade semanal", rangemode="tozero"),
                      yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Efeito (un.)", rangemode="tozero",
                                  visible=bool(np.any(np.abs(cen - base_fc) > 0.5))), barmode="relative")
    ui.chart(fig, height=430)

    tabela = pd.DataFrame({"Semana": [f"Semana {i + 1}" for i in range(h)], "Data": datas, "Base": np.round(base_fc), "Cenário": np.round(cen),
                           "Promoção": [(i + 1) in semanas for i in range(h)]})
    tabela["Variação (%)"] = np.where(tabela["Base"] > 0, (tabela["Cenário"] - tabela["Base"]) / tabela["Base"] * 100, 0)
    with st.expander("Detalhamento semanal", icon=":material/table:"):
        st.dataframe(tabela, hide_index=True, width="stretch",
                     column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY"), "Promoção": st.column_config.CheckboxColumn(),
                                    "Variação (%)": st.column_config.NumberColumn(format="%+.1f%%")})
        st.download_button("Exportar cenário (Excel)", services.to_excel({"Cenario": tabela}), f"cenario_{sku}.xlsx", icon=":material/download:")

# ======================================================================================
# CPFR
# ======================================================================================
with tab2:
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 2], vertical_alignment="bottom")
        sku_c = c1.selectbox("Produto para consenso", skus, key="cpfr_sku")
        hc = c2.slider("Horizonte (semanas)", 4, 16, 8, key="cpfr_h")
        tol = c3.slider("Tolerância de divergência (%)", 5, 50, 20, step=5, key="cpfr_tol")

    serie_c = services.series_for(df, sku_c, "W")
    _, fc_c = services.ForecastEngine.simple_moving_average(serie_c, hc, window=4)
    datas_c = services.future_index(serie_c, hc, "W")
    base_tbl = pd.DataFrame({"Semana": datas_c.date, "Estatística (sistema)": np.round(fc_c).astype(int), "Plano do parceiro": np.round(fc_c).astype(int)})

    ui.callout("Edite a coluna <b>Plano do parceiro</b> com as projeções recebidas do cliente/fornecedor. "
               "A análise de consenso é atualizada instantaneamente.", "indigo", "✍️")
    edit = st.data_editor(
        base_tbl,
        key=f"cpfr_editor_{sku_c}_{hc}",
        hide_index=True,
        width="stretch",
        column_config={
            "Semana": st.column_config.DateColumn(format="DD/MM/YYYY", disabled=True),
            "Estatística (sistema)": st.column_config.NumberColumn(disabled=True, format="localized"),
            "Plano do parceiro": st.column_config.NumberColumn(min_value=0, step=1, format="localized", help="Clique duas vezes para editar"),
        },
    )
    edit = edit.copy()
    edit["Divergência (%)"] = np.where(edit["Estatística (sistema)"] > 0,
                                       (edit["Plano do parceiro"] - edit["Estatística (sistema)"]) / edit["Estatística (sistema)"] * 100, 0)

    def _status(v):
        if abs(v) < tol:
            return "✅ Alinhado"
        return "🔺 Risco de ruptura" if v > 0 else "🔻 Risco de excesso"

    edit["Status"] = edit["Divergência (%)"].apply(_status)
    criticos = edit[edit["Divergência (%)"].abs() >= tol]
    alinh = (1 - len(criticos) / len(edit)) * 100

    ui.section("Análise de consenso")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Semanas alinhadas", f"{len(edit) - len(criticos)}/{len(edit)}", delta=f"{ui.fmt_num(alinh, 0)}% de aderência", delta_color="off", delta_arrow="off")
    k2.metric("Plano do parceiro", ui.fmt_int(edit["Plano do parceiro"].sum()))
    k3.metric("Estatística", ui.fmt_int(edit["Estatística (sistema)"].sum()))
    div_total = (edit["Plano do parceiro"].sum() - edit["Estatística (sistema)"].sum()) / max(edit["Estatística (sistema)"].sum(), 1) * 100
    k4.metric("Divergência total", ui.fmt_pct(div_total, signed=True), delta_color="off")

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1, st.container(border=True):
        fig = go.Figure()
        fig.add_trace(go.Bar(x=edit["Semana"], y=edit["Estatística (sistema)"], name="Estatística", marker=dict(color="#C7D2FE", cornerradius=4)))
        fig.add_trace(go.Bar(x=edit["Semana"], y=edit["Plano do parceiro"], name="Parceiro",
                             marker=dict(color=[("#F59E0B" if abs(v) >= tol else ui.ACCENT) for v in edit["Divergência (%)"]], cornerradius=4)))
        fig.update_layout(barmode="group", yaxis_title="Quantidade", bargap=0.25)
        ui.chart(fig, height=320)
    with c2:
        if criticos.empty:
            ui.callout(f"<b>Plano em consenso.</b> Todas as semanas estão dentro da margem de ±{tol}%.", "green", "✅")
        else:
            ui.callout(f"<b>{len(criticos)} semana(s) com desvio crítico.</b> Recomenda-se reunião de alinhamento tático com o parceiro.", "red", "⚠️")
            for _, row in criticos.iterrows():
                acima = row["Divergência (%)"] > 0
                st.html(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 2px;border-bottom:1px solid #EEF1F6">'
                    f'<span style="font-weight:600;color:#0F172A">{row["Semana"]:%d/%m/%Y}</span>'
                    f'{ui.badge_html(ui.fmt_pct(row["Divergência (%)"], signed=True) + (" · ruptura" if acima else " · excesso"), "amber" if acima else "red")}</div>'
                )

    st.dataframe(edit, hide_index=True, width="stretch",
                 column_config={"Semana": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                "Divergência (%)": st.column_config.NumberColumn(format="%+.1f%%")})
    st.download_button("Exportar plano de consenso (Excel)", services.to_excel({"CPFR": edit}), f"cpfr_{sku_c}.xlsx", icon=":material/download:", type="primary")
