import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine
from src.scenario_builder import ScenarioBuilder

def render():
    st.title("🔄 Módulo 8 e 9: Cenários e CPFR")
    
    if st.session_state.get('df_dados') is None:
        st.warning("⚠️ Nenhuma base carregada.")
        st.stop()
        
    df_dados = st.session_state['df_dados']
    eda = ExploratoryDataAnalysis(df_dados)
    skus = eda.get_skus()
    
    aba1, aba2 = st.tabs(["Módulo 8: Simulação de Cenários", "Módulo 9: CPFR (Gestão Colaborativa)"])
    
    with aba1:
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            sku = st.selectbox("Selecione o Produto:", skus, key='cen_sku')
        with col_c2:
            horizonte = st.number_input("Horizonte de Previsão (Semanas):", 1, 24, 12, key='cen_hor')
        with col_c3:
            variacao_global = st.slider("Choque de Demanda Global (%):", -50, 100, 0, step=5)
            
        st.markdown("**Simular Promoção Específica:**")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            semana_promo = st.selectbox("Aplicar Promoção na Semana:", ["Nenhuma"] + [f"Semana {i+1}" for i in range(horizonte)])
        with col_p2:
            impacto_promo = st.number_input("Impacto da Promoção (%):", 0, 300, 50, step=10)
            
        if st.button("Gerar Cenário"):
            df_agg = eda.agregar_dados(sku, frequencia='W-MON')
            series = df_agg.set_index('data')['quantidade_vendida']
            
            _, fcast_base = ForecastEngine.linear_regression(series, horizonte)
            fcast_cenario = ScenarioBuilder.aplicar_simulacao_linear(fcast_base, variacao_global)
            
            if semana_promo != "Nenhuma":
                idx_semana = int(semana_promo.split(" ")[1]) - 1
                fcast_cenario = ScenarioBuilder.aplicar_simulacao_promocao(fcast_cenario, [idx_semana], impacto_promo)
                
            future_dates = pd.date_range(start=series.index[-1], periods=horizonte+1, freq='W-MON')[1:]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=future_dates, y=fcast_base, mode='lines', name='Baseline', line=dict(dash='dash', color='gray')))
            fig.add_trace(go.Scatter(x=future_dates, y=fcast_cenario, mode='lines+markers', name='Cenário Simulado', line=dict(color='blue')))
            
            fig.update_layout(title="Comparativo de Cenários", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    with aba2:
        previsao_parceiro = st.number_input("Previsão Mensal informada pelo Parceiro:", min_value=0, value=1500)
        previsao_interna = 1200 
        
        st.metric("Previsão Estatística Interna Média", previsao_interna)
        
        delta = previsao_parceiro - previsao_interna
        delta_pct = (delta / previsao_interna) * 100 if previsao_interna > 0 else 0
        
        st.markdown("#### Análise de Consenso")
        if abs(delta_pct) <= 10:
            st.success(f"✅ Previsões alinhadas. Diferença de apenas {delta_pct:.1f}%.")
        elif delta_pct > 10:
            st.warning(f"⚠️ O parceiro prevê uma demanda {delta_pct:.1f}% MAIOR que o modelo estatístico.")
        else:
            st.error(f"📉 O parceiro prevê uma demanda {abs(delta_pct):.1f}% MENOR que o modelo.")