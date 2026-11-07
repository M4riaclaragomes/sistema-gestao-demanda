import streamlit as st

from src import services, ui

df = st.session_state.get("df_dados")

ui.hero(
    "Planeje a demanda com precisão estatística",
    "Do histórico de vendas ao plano consensado: importe sua base, entenda o comportamento de cada produto, "
    "gere previsões com 7 modelos estatísticos, valide com backtesting e alinhe o plano com parceiros via CPFR.",
    eyebrow="Demanda+ · Central de planejamento",
    chips=["7 modelos de previsão", "Backtesting out-of-sample", "Simulação de cenários", "CPFR colaborativo", "Laudos automáticos"],
)

if df is None:
    with st.container(border=True):
        c1, c2 = st.columns([3, 2], vertical_alignment="center")
        with c1:
            st.markdown("#### Comece em segundos")
            st.markdown(
                '<div class="gd-muted">Carregue a base de demonstração com 5 produtos de perfis distintos '
                "(estável, crescente, sazonal, irregular e intermitente) ou importe sua própria planilha CSV/Excel "
                "com as colunas <b>sku</b>, <b>data</b> e <b>quantidade_vendida</b>.</div>",
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("Explorar com dados de demonstração", type="primary", icon=":material/bolt:", width="stretch"):
                services.load_demo_into_state()
                st.rerun()
            st.page_link("views/1_importacao.py", label="Importar minha base", icon=":material/upload_file:")
else:
    s = services.dataset_summary(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Volume histórico", ui.fmt_int(s["volume"]), help="Soma de todas as unidades vendidas na base.")
    c2.metric("Produtos (SKUs)", s["skus"])
    c3.metric("Registros", ui.fmt_int(s["registros"]))
    c4.metric("Cobertura", f"{(s['fim'] - s['inicio']).days // 30} meses", help=f"{ui.fmt_date(s['inicio'])} a {ui.fmt_date(s['fim'])}")

    ui.section("Portfólio em um relance", "Perfil de demanda identificado automaticamente para cada SKU (base semanal).")
    port = services.portfolio_table(df)
    st.dataframe(
        port,
        hide_index=True,
        width="stretch",
        column_config={
            "SKU": st.column_config.TextColumn(width="medium"),
            "Perfil": st.column_config.TextColumn(),
            "Volume total": st.column_config.NumberColumn(format="localized"),
            "Média semanal": st.column_config.NumberColumn(format="%.1f"),
            "CV": st.column_config.ProgressColumn("Variabilidade (CV)", min_value=0, max_value=max(1.0, float(port["CV"].max())), format="%.2f"),
            "Crescimento (%)": st.column_config.NumberColumn(format="%+.1f%%"),
            "Tendência (52 sem.)": st.column_config.AreaChartColumn("Últimas 52 semanas", width="medium"),
        },
    )

ui.section("Fluxo de trabalho", "Siga as etapas na ordem ou vá direto ao módulo que precisa.")

steps = [
    ("1", "Importação de dados", "Carregue CSV/Excel, mapeie colunas e valide a qualidade da base.", "views/1_importacao.py", ":material/upload_file:"),
    ("2", "Análise histórica", "Indicadores, perfil de demanda, sazonalidade e distribuição.", "views/2_analise_historica.py", ":material/query_stats:"),
    ("3", "Previsão de demanda", "Projeções com intervalos de confiança e exportação.", "views/3_previsao_demanda.py", ":material/trending_up:"),
    ("4", "Comparação de modelos", "Teste cego (out-of-sample) para eleger o melhor método.", "views/4_comparacao_modelos.py", ":material/leaderboard:"),
    ("5", "Cenários e CPFR", "Simule choques e promoções; alinhe o plano com parceiros.", "views/6_cenarios_cpfr.py", ":material/tune:"),
    ("6", "Dashboard e laudos", "Visão executiva do portfólio e relatórios prontos para S&OP.", "views/5_dashboard_gerencial.py", ":material/monitoring:"),
]
for row in (steps[:3], steps[3:]):
    cols = st.columns(3)
    for col, (n, t, d, page, icon) in zip(cols, row):
        with col, st.container(border=True, height="stretch"):
            ui.step(n, t, d)
            st.page_link(page, label="Abrir módulo", icon=icon)
