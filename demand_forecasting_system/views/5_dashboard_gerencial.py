import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import services, ui

ui.hero(
    "Dashboard gerencial",
    "Visão executiva do portfólio: volume, ritmo recente, participação por produto e evolução temporal.",
    eyebrow="Módulo 05 · Gestão",
)
df = ui.require_data()
skus = sorted(df["sku"].unique())

with st.container(border=True):
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    sel = c1.multiselect("Produtos", skus, default=skus, key="dash_skus", placeholder="Todos os produtos")
    dmin, dmax = df["data"].min().date(), df["data"].max().date()
    periodo = c2.date_input("Período", value=(dmin, dmax), min_value=dmin, max_value=dmax, format="DD/MM/YYYY", key="dash_period")

sel = sel or skus
ini, fim = (periodo if isinstance(periodo, (tuple, list)) and len(periodo) == 2 else (dmin, dmax))
base = df[df["sku"].isin(sel) & df["data"].between(pd.Timestamp(ini), pd.Timestamp(fim))].copy()
if base.empty:
    st.info("Nenhum dado para os filtros selecionados.", icon=":material/filter_alt_off:")
    st.stop()

# ---------- KPIs ----------
ultimo = base["data"].max()
r30 = base[base["data"] > ultimo - pd.Timedelta(days=30)]["quantidade_vendida"].sum()
p30 = base[(base["data"] <= ultimo - pd.Timedelta(days=30)) & (base["data"] > ultimo - pd.Timedelta(days=60))]["quantidade_vendida"].sum()
delta30 = (r30 - p30) / p30 * 100 if p30 else None
ano = base[base["data"] > ultimo - pd.Timedelta(days=365)]["quantidade_vendida"].sum()
ano_ant = base[(base["data"] <= ultimo - pd.Timedelta(days=365)) & (base["data"] > ultimo - pd.Timedelta(days=730))]["quantidade_vendida"].sum()
yoy = (ano - ano_ant) / ano_ant * 100 if ano_ant else None
por_sku = base.groupby("sku")["quantidade_vendida"].sum().sort_values(ascending=False)
diario = base.groupby("data")["quantidade_vendida"].sum()
mensal = base.set_index("data")["quantidade_vendida"].resample("ME").sum()
mensal = mensal[mensal.index <= ultimo.normalize()]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Volume no período", ui.fmt_int(base["quantidade_vendida"].sum()), chart_data=mensal.tolist(), chart_type="area")
k2.metric("Últimos 30 dias", ui.fmt_int(r30), delta=ui.fmt_pct(delta30, signed=True) if delta30 is not None else None, delta_description="vs. 30 dias anteriores")
k3.metric("Últimos 12 meses", ui.fmt_int(ano), delta=ui.fmt_pct(yoy, signed=True) if yoy is not None else None, delta_description="vs. 12 meses anteriores")
k4.metric("Média diária", ui.fmt_num(diario.mean()), chart_data=diario.tail(60).tolist(), chart_type="line")
k5.metric("Produto campeão", por_sku.index[0], delta=f"{ui.fmt_num(por_sku.iloc[0] / por_sku.sum() * 100, 0)}% do volume", delta_color="off", delta_arrow="off")

# ---------- Distribuição ----------
c1, c2 = st.columns([3, 2], gap="medium")
with c1, st.container(border=True):
    st.markdown("**Volume por produto**")
    d = por_sku.reset_index()
    fig = go.Figure(go.Bar(y=d["sku"], x=d["quantidade_vendida"], orientation="h",
                           marker=dict(color=[ui.PALETTE[skus.index(s) % len(ui.PALETTE)] for s in d["sku"]], cornerradius=6),
                           text=[ui.fmt_int(v) for v in d["quantidade_vendida"]], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:,.0f} un.<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(hovermode="closest", margin=dict(l=8, r=60, t=10, b=8))
    ui.chart(fig, height=320)
with c2, st.container(border=True):
    st.markdown("**Participação no portfólio**")
    fig = go.Figure(go.Pie(labels=por_sku.index, values=por_sku.values, hole=0.62, sort=False,
                           marker=dict(colors=[ui.PALETTE[skus.index(s) % len(ui.PALETTE)] for s in por_sku.index], line=dict(color="#fff", width=2)),
                           textinfo="percent", textposition="inside", hovertemplate="%{label}<br>%{value:,.0f} un. (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"<b>{ui.fmt_int(por_sku.sum())}</b><br><span style='font-size:11px;color:#64748B'>unidades</span>", showarrow=False, font=dict(size=18, color=ui.INK))
    fig.update_layout(showlegend=True, legend=dict(orientation="v", x=1, y=0.5, yanchor="middle", xanchor="left"), margin=dict(l=8, r=8, t=10, b=8),
                      uniformtext=dict(minsize=10, mode="hide"))
    ui.chart(fig, height=320)

# ---------- Evolução ----------
ui.section("Evolução temporal", "Volume mensal por produto.")
modo = st.segmented_control("Visualização", ["Empilhado", "Linhas", "Participação %"], default="Empilhado", key="dash_mode") or "Empilhado"
tempo = base.groupby([pd.Grouper(key="data", freq="ME"), "sku"])["quantidade_vendida"].sum().reset_index()
tempo = tempo[tempo["data"] <= ultimo.normalize()]  # ignora mês final incompleto
st.caption(f"Meses incompletos no fim do período são omitidos. Dados até {ui.fmt_date(ultimo)}.")
cmap = {s: ui.PALETTE[skus.index(s) % len(ui.PALETTE)] for s in skus}
if modo == "Linhas":
    fig = px.line(tempo, x="data", y="quantidade_vendida", color="sku", color_discrete_map=cmap, markers=True)
else:
    fig = px.area(tempo, x="data", y="quantidade_vendida", color="sku", color_discrete_map=cmap, groupnorm="percent" if modo == "Participação %" else None)
    fig.update_traces(line=dict(width=1))
fig.update_layout(xaxis_title="", yaxis_title="% do volume" if modo == "Participação %" else "Volume mensal", legend_title_text="")
ui.chart(fig, height=420)

# ---------- Heatmap ----------
ui.section("Intensidade mensal por produto", "Índice do mês em relação à média do próprio produto (100 = média).")
pv = tempo.pivot(index="sku", columns="data", values="quantidade_vendida")
idx = pv.div(pv.mean(axis=1), axis=0) * 100
fig = go.Figure(go.Heatmap(z=idx.values, x=idx.columns, y=idx.index, zmid=100,
                           colorscale=[[0, "#FDE68A"], [0.5, "#FFFFFF"], [1, "#4F46E5"]], xgap=2, ygap=3,
                           hovertemplate="%{y} · %{x|%b/%Y}<br>índice %{z:.0f}<extra></extra>", colorbar=dict(thickness=10, outlinewidth=0)))
fig.update_layout(hovermode="closest")
ui.chart(fig, height=300)
