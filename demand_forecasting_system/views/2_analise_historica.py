import streamlit as st
import plotly.express as px
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.eda import ExploratoryDataAnalysis

def render():
    st.title("📊 Análise Histórica")
    if not st.session_state.get('df_dados') is not None: st.warning("Faça a importação 1º"); st.stop()
    eda = ExploratoryDataAnalysis(st.session_state['df_dados'])
    sku = st.selectbox("SKU:", eda.get_skus())
    df_agg = eda.agregar_dados(sku)
    ind = eda.calcular_indicadores(df_agg)
    classe, mot = eda.classificar_comportamento(ind)
    st.info(f"**{classe}**: {mot}")
    st.plotly_chart(px.line(df_agg, x='data', y='quantidade_vendida', title="Evolução"))