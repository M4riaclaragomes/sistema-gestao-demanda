import io

import pandas as pd
import streamlit as st

from src import services, ui
from src.data_processor import DataProcessor

processor = DataProcessor()
REQUIRED = {"sku": "Produto / SKU", "data": "Data", "quantidade_vendida": "Quantidade vendida"}

ui.hero(
    "Importação de dados",
    "Traga o histórico de vendas ou demanda. O sistema mapeia as colunas, audita a qualidade da base e "
    "aplica o tratamento padrão antes de liberar as análises.",
    eyebrow="Módulo 01 · Dados",
    chips=["CSV · XLSX · XLS", "Validação automática", "Tratamento de nulos e negativos"],
)

# ---------- Origem dos dados ----------
c1, c2 = st.columns([3, 2], gap="medium")
with c1, st.container(border=True, height="stretch"):
    st.markdown("##### :material/upload_file: Carregar base própria")
    arquivo = st.file_uploader(
        "Arraste o arquivo ou clique para selecionar",
        type=["csv", "xlsx", "xls"],
        help="Colunas mínimas: sku, data e quantidade_vendida (nomes diferentes podem ser mapeados abaixo).",
    )
with c2, st.container(border=True, height="stretch"):
    st.markdown("##### :material/science: Base de demonstração")
    st.markdown(
        '<div class="gd-muted">5 produtos com perfis estatísticos distintos, 4 anos de histórico diário — '
        "ideal para conhecer todas as funcionalidades.</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    b1, b2 = st.columns(2)
    if b1.button("Usar demonstração", type="primary", icon=":material/bolt:", width="stretch"):
        st.session_state["import_demo"] = True
    b2.download_button("Modelo CSV", services.template_csv(), "modelo_importacao.csv", "text/csv", icon=":material/download:", width="stretch")

df_bruto, origem = None, ""
if arquivo is not None:
    st.session_state["import_demo"] = False
    df_bruto, msg = processor.carregar_arquivo(arquivo, arquivo.name.rsplit(".", 1)[-1].lower())
    if df_bruto is None:
        st.error(f"Não foi possível ler o arquivo: {msg}", icon=":material/error:")
        st.stop()
    origem = f"Arquivo · {arquivo.name}"
elif st.session_state.get("import_demo"):
    df_bruto, origem = services.read_demo_raw().copy(), "Base de demonstração"

if df_bruto is None:
    with st.expander("Formato esperado do arquivo", icon=":material/help:"):
        st.markdown("Uma linha por **produto × data**. Colunas extras (ex.: `categoria`, `preco_unitario`) são preservadas.")
        st.dataframe(pd.read_csv(io.BytesIO(services.template_csv())), hide_index=True, width="content")
    st.stop()

# ---------- Mapeamento de colunas ----------
faltando = [c for c in REQUIRED if c not in df_bruto.columns]
if faltando:
    ui.section("Mapeamento de colunas", "Não encontramos alguns nomes padrão. Indique qual coluna do arquivo corresponde a cada campo.")
    with st.container(border=True):
        cols = st.columns(len(faltando))
        mapping = {}
        opcoes = [c for c in df_bruto.columns if c not in REQUIRED]
        for col, campo in zip(cols, faltando):
            mapping[campo] = col.selectbox(REQUIRED[campo], opcoes, index=None, placeholder="Selecione a coluna…", key=f"map_{campo}")
    if any(v is None for v in mapping.values()):
        st.info("Complete o mapeamento para continuar.", icon=":material/info:")
        st.stop()
    df_bruto = df_bruto.rename(columns={v: k for k, v in mapping.items()})

# ---------- Auditoria de qualidade ----------
alertas = processor.validar_dados(df_bruto)
if alertas["tipos_invalidos_data"]:
    st.error("A coluna de datas não pôde ser convertida. Verifique o formato (ex.: AAAA-MM-DD).", icon=":material/error:")
    st.stop()

df_tratado = processor.aplicar_tratamento_padrao(df_bruto)
resumo = services.dataset_summary(df_tratado)
problemas = int(alertas["valores_nulos"]) + int(alertas["valores_negativos"]) + int(alertas["linhas_duplicadas"])
score = max(0.0, 100 - problemas / max(len(df_bruto), 1) * 100 * 10)

ui.section("Auditoria de qualidade", f"Origem: {origem}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Registros", ui.fmt_int(len(df_bruto)))
k2.metric("SKUs", resumo["skus"])
k3.metric("Período", f"{resumo['inicio']:%m/%y} – {resumo['fim']:%m/%y}", help=f"{ui.fmt_date(resumo['inicio'])} a {ui.fmt_date(resumo['fim'])}")
k4.metric("Índice de qualidade", f"{score:.0f}/100", delta=f"{problemas} ocorrência(s)" if problemas else "Sem ocorrências",
          delta_color="inverse" if problemas else "normal", delta_arrow="off")

checks = [
    ("Valores nulos", int(alertas["valores_nulos"]), "substituídos por 0"),
    ("Quantidades negativas", int(alertas["valores_negativos"]), "ajustadas para 0"),
    ("Duplicidades (SKU × data)", int(alertas["linhas_duplicadas"]), "mantidas para revisão"),
]
with st.container(border=True):
    cc = st.columns(3)
    for col, (nome, qtd, acao) in zip(cc, checks):
        with col:
            tone = "green" if qtd == 0 else "amber"
            st.html(
                f'<div class="gd-card-title">{nome}</div>'
                f'<div style="display:flex;align-items:center;gap:10px"><span class="gd-big">{qtd}</span>'
                f'{ui.badge_html("OK" if qtd == 0 else "Tratado: " + acao, tone)}</div>'
            )

# ---------- Visualização ----------
ui.section("Pré-visualização da base tratada", "Ordenada por SKU e data. Use a busca e a ordenação das colunas para inspecionar.")
tab1, tab2 = st.tabs([":material/table: Registros", ":material/inventory_2: Resumo por SKU"])
with tab1:
    st.dataframe(
        df_tratado,
        width="stretch",
        height=380,
        hide_index=True,
        column_config={
            "sku": st.column_config.TextColumn("SKU"),
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "quantidade_vendida": st.column_config.NumberColumn("Quantidade", format="localized"),
        },
    )
with tab2:
    por_sku = (
        df_tratado.groupby("sku")
        .agg(registros=("quantidade_vendida", "size"), volume=("quantidade_vendida", "sum"), media=("quantidade_vendida", "mean"),
             inicio=("data", "min"), fim=("data", "max"))
        .reset_index()
    )
    st.dataframe(
        por_sku,
        hide_index=True,
        width="stretch",
        column_config={
            "sku": "SKU",
            "registros": st.column_config.NumberColumn("Registros", format="localized"),
            "volume": st.column_config.ProgressColumn("Volume", format="%.0f", min_value=0, max_value=float(por_sku["volume"].max())),
            "media": st.column_config.NumberColumn("Média por registro", format="%.1f"),
            "inicio": st.column_config.DateColumn("Início", format="DD/MM/YYYY"),
            "fim": st.column_config.DateColumn("Fim", format="DD/MM/YYYY"),
        },
    )

st.write("")
with st.container(border=True):
    a, b = st.columns([3, 1], vertical_alignment="center")
    a.markdown("**Tudo certo?** Confirme para disponibilizar a base em todos os módulos de análise e previsão.")
    if b.button("Confirmar e salvar base", type="primary", icon=":material/check_circle:", width="stretch"):
        services.set_dataset(df_tratado.copy(), origem)
        st.session_state["import_demo"] = False
        st.toast("Base salva! Abrindo a análise histórica…", icon=":material/celebration:")
        st.switch_page("views/2_analise_historica.py")
