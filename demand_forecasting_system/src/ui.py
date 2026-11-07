"""Camada visual compartilhada: tema, CSS, componentes e template de gráficos."""
from __future__ import annotations

import html
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --------------------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------------------
PRIMARY = "#4F46E5"
PRIMARY_SOFT = "#EEF2FF"
ACCENT = "#14B8A6"
INK = "#0F172A"
MUTED = "#64748B"
BORDER = "#E5E7EF"
GRID = "#EEF1F6"

PALETTE = ["#4F46E5", "#14B8A6", "#F59E0B", "#EC4899", "#0EA5E9", "#8B5CF6", "#EF4444", "#22C55E"]

TONES = {
    "indigo": ("#EEF2FF", "#4338CA"),
    "teal": ("#E6FAF7", "#0F766E"),
    "green": ("#ECFDF3", "#15803D"),
    "amber": ("#FFF7E6", "#B45309"),
    "red": ("#FEF2F2", "#B91C1C"),
    "slate": ("#F1F5F9", "#334155"),
    "pink": ("#FDF2F8", "#BE185D"),
}

PROFILE_TONE = {
    "Estável": "green",
    "Crescente": "indigo",
    "Decrescente": "red",
    "Irregular": "amber",
    "Intermitente": "pink",
    "Sazonal/Variável": "teal",
    "Sem Dados": "slate",
}


# --------------------------------------------------------------------------------------
# Plotly template
# --------------------------------------------------------------------------------------
def _register_plotly_template() -> None:
    if "demanda" in pio.templates:
        return
    axis_title = dict(font=dict(size=12, color=MUTED))
    tpl = go.layout.Template()
    tpl.layout = go.Layout(
        font=dict(family="Inter, system-ui, sans-serif", size=12.5, color="#334155"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE,
        xaxis=dict(showgrid=False, linecolor=BORDER, tickcolor=BORDER, zeroline=False, title=axis_title, ticks="outside", ticklen=4),
        yaxis=dict(gridcolor=GRID, zeroline=False, showline=False, title=axis_title, separatethousands=True),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(family="Inter, sans-serif", color=INK, size=12.5)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        margin=dict(l=8, r=8, t=40, b=8),
        hovermode="x unified",
        separators=",.",
        bargap=0.28,
    )
    pio.templates["demanda"] = tpl
    pio.templates.default = "plotly_white+demanda"


def chart(fig: go.Figure, height: int = 380, key: str | None = None) -> None:
    """Renderiza um gráfico Plotly com o template da aplicação."""
    fig.update_layout(height=height)
    st.plotly_chart(fig, theme=None, key=key, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


# --------------------------------------------------------------------------------------
# CSS global
# --------------------------------------------------------------------------------------
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, button, input, textarea, select { font-family: 'Inter', system-ui, sans-serif; }

.block-container { padding-top: 3.6rem !important; padding-bottom: 4rem !important; max-width: 1360px; }
header[data-testid="stHeader"] { background: rgba(246,247,251,.75); backdrop-filter: blur(8px); }

/* ---------- Metric cards ---------- */
[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E5E7EF !important; border-radius: 16px; padding: 16px 18px 14px 18px;
    box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 4px 16px -8px rgba(15,23,42,.08);
    transition: transform .15s ease, box-shadow .15s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 2px 4px rgba(15,23,42,.05), 0 12px 24px -12px rgba(79,70,229,.25); }
[data-testid="stMetricLabel"] p { font-size: .72rem !important; text-transform: uppercase; letter-spacing: .07em; color: #64748B; font-weight: 600; }
[data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 750; color: #0F172A; letter-spacing: -.02em; }
[data-testid="stMetricDelta"] { font-weight: 600; }

/* ---------- Bordered containers as cards ---------- */
.stMainBlockContainer [data-testid="stVerticalBlockBorderWrapper"],
.stMainBlockContainer [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][style*="border"] {
    background: #FFFFFF;
    box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 6px 20px -12px rgba(15,23,42,.10);
}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { font-weight: 600; border-radius: 10px; transition: all .15s ease; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%); border: 0; box-shadow: 0 6px 16px -6px rgba(79,70,229,.6);
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover { filter: brightness(1.06); transform: translateY(-1px); }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #E5E7EF; }
.stTabs [data-baseweb="tab"] { padding: 10px 16px; font-weight: 600; color: #64748B; border-radius: 10px 10px 0 0; }
.stTabs [aria-selected="true"] { color: #4F46E5 !important; background: #EEF2FF; }

/* ---------- Expander ---------- */
[data-testid="stExpander"] details { background: #FFFFFF; border-radius: 14px; }
[data-testid="stExpander"] summary p { font-weight: 600; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,.06); }
[data-testid="stSidebarNav"] [data-testid="stNavSectionHeader"] { font-size: .68rem; letter-spacing: .12em; text-transform: uppercase; opacity: .55; font-weight: 700; }
[data-testid="stSidebarNavLink"] { border-radius: 10px; margin: 1px 0; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background: linear-gradient(90deg, rgba(99,102,241,.35), rgba(99,102,241,.08)) !important; }

/* ---------- Dataframes ---------- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border-radius: 12px; overflow: hidden; }

/* ---------- Custom components ---------- */
.gd-hero {
    position: relative; overflow: hidden; border-radius: 22px; padding: 30px 34px 28px 34px; margin-bottom: 1.4rem; color: #fff;
    background:
      radial-gradient(900px 260px at 100% -20%, rgba(45,212,191,.45), transparent 60%),
      radial-gradient(600px 240px at -10% 120%, rgba(236,72,153,.28), transparent 60%),
      linear-gradient(135deg, #1E1B4B 0%, #312E81 48%, #4338CA 100%);
    box-shadow: 0 20px 40px -24px rgba(49,46,129,.7);
}
.gd-hero::after {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background-image: linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px);
    background-size: 28px 28px; mask-image: linear-gradient(90deg, transparent 35%, #000 100%); -webkit-mask-image: linear-gradient(90deg, transparent 35%, #000 100%);
}
.gd-hero .eyebrow { display: inline-flex; gap: 8px; align-items: center; font-size: .7rem; letter-spacing: .16em; text-transform: uppercase; font-weight: 700; color: #C7D2FE; }
.gd-hero .eyebrow .dot { width: 7px; height: 7px; border-radius: 99px; background: #2DD4BF; box-shadow: 0 0 0 4px rgba(45,212,191,.25); }
.gd-hero .title { font-size: 2rem; line-height: 1.15; font-weight: 800; letter-spacing: -.025em; margin: .5rem 0 .45rem 0; color: #fff; }
.gd-hero .subtitle { color: rgba(255,255,255,.82); max-width: 780px; font-size: .98rem; line-height: 1.6; margin: 0; }
.gd-hero .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; position: relative; z-index: 1; }
.gd-hero .chip { font-size: .76rem; font-weight: 600; padding: 5px 11px; border-radius: 999px; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.18); color: #fff; }

.gd-section { margin: 1.6rem 0 .7rem 0; }
.gd-section .t { font-size: 1.08rem; font-weight: 750; color: #0F172A; letter-spacing: -.01em; display: flex; align-items: center; gap: 10px; }
.gd-section .t .bar { width: 4px; height: 18px; border-radius: 4px; background: linear-gradient(#4F46E5, #14B8A6); }
.gd-section .s { color: #64748B; font-size: .86rem; margin-top: 2px; padding-left: 14px; }

.gd-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: .76rem; font-weight: 650; white-space: nowrap; }
.gd-badge .d { width: 6px; height: 6px; border-radius: 99px; background: currentColor; }

.gd-callout { border-radius: 14px; padding: 14px 16px; border: 1px solid; display: flex; gap: 12px; align-items: flex-start; font-size: .92rem; line-height: 1.55; margin: .25rem 0 .75rem 0; }
.gd-callout .ic { font-size: 1.1rem; line-height: 1.4; }
.gd-callout b { font-weight: 700; }

.gd-card-title { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; color: #64748B; font-weight: 700; margin-bottom: 4px; }
.gd-big { font-size: 1.5rem; font-weight: 800; color: #0F172A; letter-spacing: -.02em; }
.gd-muted { color: #64748B; font-size: .86rem; line-height: 1.55; }

.gd-step { display: flex; gap: 14px; align-items: flex-start; }
.gd-step .n { flex: 0 0 auto; width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; font-weight: 800; color: #4F46E5; background: #EEF2FF; font-size: .9rem; }
.gd-step .tt { font-weight: 700; color: #0F172A; font-size: .98rem; }
.gd-step .dd { color: #64748B; font-size: .85rem; line-height: 1.5; margin-top: 2px; }

.gd-winner { border-radius: 18px; padding: 20px 22px; color: #fff; background: linear-gradient(135deg, #0F766E 0%, #14B8A6 100%); box-shadow: 0 16px 32px -20px rgba(15,118,110,.8); }
.gd-winner .k { font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; opacity: .8; font-weight: 700; }
.gd-winner .v { font-size: 1.7rem; font-weight: 800; letter-spacing: -.02em; margin: 4px 0 2px; }
.gd-winner .m { font-size: .88rem; opacity: .9; }

.gd-report { background: #FFFFFF; border: 1px solid #E5E7EF; border-radius: 18px; padding: 24px 26px; box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px -16px rgba(15,23,42,.15); }
.gd-report h4 { margin: 0 0 .6rem 0; font-size: 1.05rem; font-weight: 750; color: #0F172A; }
.gd-report ul { margin: .25rem 0 0 1.1rem; padding: 0; }
.gd-report li { margin: .35rem 0; color: #334155; line-height: 1.55; }

/* Sidebar status card */
.gd-side { border-radius: 14px; padding: 14px 14px 12px 14px; background: linear-gradient(160deg, rgba(99,102,241,.22), rgba(20,184,166,.10)); border: 1px solid rgba(255,255,255,.08); margin-top: .4rem; }
.gd-side .k { font-size: .66rem; letter-spacing: .12em; text-transform: uppercase; color: #A5B4FC; font-weight: 700; }
.gd-side .v { font-size: .92rem; font-weight: 650; color: #F8FAFC; margin-top: 2px; }
.gd-side .row { display: flex; justify-content: space-between; font-size: .78rem; color: #CBD5E1; margin-top: 8px; }
.gd-side .row b { color: #F8FAFC; font-weight: 650; }
.gd-side .live { display: inline-block; width: 7px; height: 7px; border-radius: 99px; background: #2DD4BF; margin-right: 6px; box-shadow: 0 0 0 3px rgba(45,212,191,.25); }
.gd-side.empty { background: rgba(255,255,255,.04); }
.gd-side.empty .live { background: #F59E0B; box-shadow: 0 0 0 3px rgba(245,158,11,.25); }
.gd-foot { font-size: .7rem; color: #64748B; margin-top: 1rem; opacity: .9; }
</style>
"""


def _patch_metric() -> None:
    """Faz todos os cards de métrica de uma linha terem a mesma altura (height='stretch')."""
    from streamlit.delta_generator import DeltaGenerator

    if getattr(DeltaGenerator.metric, "_gd_patched", False):
        return
    original = DeltaGenerator.metric

    def metric(self, *args, **kwargs):
        kwargs.setdefault("height", "stretch")
        return original(self, *args, **kwargs)

    metric._gd_patched = True
    DeltaGenerator.metric = metric


def setup() -> None:
    _register_plotly_template()
    _patch_metric()
    st.html(_CSS)


# --------------------------------------------------------------------------------------
# Componentes
# --------------------------------------------------------------------------------------
def _e(text) -> str:
    return html.escape(str(text))


def hero(title: str, subtitle: str, eyebrow: str = "", chips: Iterable[str] = ()) -> None:
    chips_html = "".join(f'<span class="chip">{_e(c)}</span>' for c in chips)
    st.html(
        f"""<div class="gd-hero">
            <div class="eyebrow"><span class="dot"></span>{_e(eyebrow)}</div>
            <div class="title">{_e(title)}</div>
            <p class="subtitle">{subtitle}</p>
            {f'<div class="chips">{chips_html}</div>' if chips_html else ''}
        </div>"""
    )


def section(title: str, subtitle: str = "") -> None:
    st.html(
        f"""<div class="gd-section"><div class="t"><span class="bar"></span>{_e(title)}</div>
        {f'<div class="s">{subtitle}</div>' if subtitle else ''}</div>"""
    )


def badge_html(text: str, tone: str = "indigo") -> str:
    bg, fg = TONES.get(tone, TONES["slate"])
    return f'<span class="gd-badge" style="background:{bg};color:{fg}"><span class="d"></span>{_e(text)}</span>'


def badge(text: str, tone: str = "indigo") -> None:
    st.html(badge_html(text, tone))


def callout(text: str, tone: str = "indigo", icon: str = "💡") -> None:
    bg, fg = TONES.get(tone, TONES["slate"])
    st.html(
        f'<div class="gd-callout" style="background:{bg};border-color:{fg}22;color:{fg}">'
        f'<span class="ic">{icon}</span><div>{text}</div></div>'
    )


def step(n: int | str, title: str, desc: str) -> None:
    st.html(
        f'<div class="gd-step"><div class="n">{_e(n)}</div><div><div class="tt">{_e(title)}</div>'
        f'<div class="dd">{desc}</div></div></div>'
    )


def winner(label: str, value: str, meta: str) -> None:
    st.html(f'<div class="gd-winner"><div class="k">{_e(label)}</div><div class="v">{_e(value)}</div><div class="m">{meta}</div></div>')


# --------------------------------------------------------------------------------------
# Formatação (padrão pt-BR)
# --------------------------------------------------------------------------------------
def fmt_int(x) -> str:
    try:
        return f"{float(x):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def fmt_num(x, dec: int = 1) -> str:
    try:
        s = f"{float(x):,.{dec}f}"
    except (TypeError, ValueError):
        return "—"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(x, dec: int = 1, signed: bool = False) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "—"
    if pd.isna(v):
        return "—"
    sign = "+" if signed and v > 0 else ""
    return f"{sign}{fmt_num(v, dec)}%"


def fmt_date(d) -> str:
    return pd.Timestamp(d).strftime("%d/%m/%Y")


# --------------------------------------------------------------------------------------
# Guarda de dados
# --------------------------------------------------------------------------------------
def require_data() -> pd.DataFrame:
    from src import services  # import tardio para evitar ciclo

    df = st.session_state.get("df_dados")
    if df is not None:
        return df

    with st.container(border=True):
        c1, c2 = st.columns([3, 2], vertical_alignment="center")
        with c1:
            st.markdown("#### Nenhuma base carregada ainda")
            st.markdown(
                '<div class="gd-muted">Este módulo precisa de um histórico de demanda. Importe sua planilha '
                "(CSV/Excel) ou explore o sistema agora com a base de demonstração — 5 produtos com "
                "perfis estável, crescente, sazonal, irregular e intermitente.</div>",
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("Usar dados de demonstração", type="primary", icon=":material/bolt:", width="stretch", key="empty_demo"):
                services.load_demo_into_state()
                st.rerun()
            st.page_link("views/1_importacao.py", label="Importar minha base", icon=":material/upload_file:")
    st.stop()
