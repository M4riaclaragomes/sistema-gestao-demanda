import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import services, ui  # noqa: E402

st.set_page_config(
    page_title="Demanda+ · Gestão de Demanda",
    page_icon=str(ROOT / "assets" / "icon.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "**Demanda+** — sistema de previsão e gestão de demanda (S&OP / CPFR)."},
)
ui.setup()
st.logo(str(ROOT / "assets" / "logo.svg"), size="large", icon_image=str(ROOT / "assets" / "icon.svg"))

pages = {
    "Início": [
        st.Page("views/0_inicio.py", title="Visão geral", icon=":material/home:", default=True),
    ],
    "Dados": [
        st.Page("views/1_importacao.py", title="Importação de dados", icon=":material/upload_file:"),
        st.Page("views/2_analise_historica.py", title="Análise histórica", icon=":material/query_stats:"),
    ],
    "Planejamento": [
        st.Page("views/3_previsao_demanda.py", title="Previsão de demanda", icon=":material/trending_up:"),
        st.Page("views/4_comparacao_modelos.py", title="Comparação de modelos", icon=":material/leaderboard:"),
        st.Page("views/6_cenarios_cpfr.py", title="Cenários e CPFR", icon=":material/tune:"),
    ],
    "Gestão": [
        st.Page("views/5_dashboard_gerencial.py", title="Dashboard gerencial", icon=":material/monitoring:"),
        st.Page("views/7_relatorios.py", title="Relatórios e laudos", icon=":material/description:"),
    ],
}
pg = st.navigation(pages)

# ---------- Sidebar: status da base ----------
with st.sidebar:
    df = st.session_state.get("df_dados")
    if df is not None:
        s = services.dataset_summary(df)
        st.html(
            f"""<div class="gd-side">
                <div class="k"><span class="live"></span>Base ativa</div>
                <div class="v">{ui._e(st.session_state.get('origem', 'Base carregada'))}</div>
                <div class="row"><span>SKUs</span><b>{s['skus']}</b></div>
                <div class="row"><span>Registros</span><b>{ui.fmt_int(s['registros'])}</b></div>
                <div class="row"><span>Período</span><b>{s['inicio']:%m/%Y} – {s['fim']:%m/%Y}</b></div>
            </div>"""
        )
        if st.button("Trocar base", icon=":material/swap_horiz:", width="stretch", key="side_clear"):
            services.clear_dataset()
            st.switch_page("views/1_importacao.py")
    else:
        st.html(
            """<div class="gd-side empty">
                <div class="k"><span class="live"></span>Sem base ativa</div>
                <div class="v">Carregue dados para começar</div>
            </div>"""
        )
        if st.button("Carregar demonstração", icon=":material/bolt:", type="primary", width="stretch", key="side_demo"):
            services.load_demo_into_state()
            st.rerun()
    st.html('<div class="gd-foot">Demanda+ · v2.0 — Previsão estatística, backtesting e colaboração CPFR.</div>')

pg.run()
