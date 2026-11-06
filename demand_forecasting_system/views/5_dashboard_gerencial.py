import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.eda import ExploratoryDataAnalysis

def render():
    st.title("🌎 Dashboard Gerencial")
    if not st.session_state.get('df_dados') is not None: st.warning("Importe os dados."); st.stop()
    eda = ExploratoryDataAnalysis(st.session_state['df_dados'])
    dados = []
    for s in eda.get_skus():
        ind = eda.calcular_indicadores(eda.agregar_dados(s))
        dados.append({'SKU': s, 'Volume': ind['total'], 'Perfil': eda.classificar_comportamento(ind)[0]})
    
    df = pd.DataFrame(dados)
    st.plotly_chart(px.pie(df, names='Perfil', title="Perfis de Demanda"))