import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine

def render():
    st.title("🔄 Módulos 8 e 9: Cenários e CPFR")
    
    if 'df_dados' not in st.session_state or st.session_state['df_dados'] is None:
        st.warning("⚠️ Nenhuma base de dados tratada encontrada. Retorne ao Módulo 1.")
        return

    df = st.session_state['df_dados']
    eda = ExploratoryDataAnalysis(df)
    
    skus = df['sku'].unique()
    
    tab1, tab2 = st.tabs(["Módulo 8: Simulação de Cenários", "Módulo 9: CPFR (Gestão Colaborativa)"])
    
    # --- LÓGICA DA ABA 1 (CENÁRIOS) ---
    with tab1:
        st.markdown("Simule impactos macroeconômicos e campanhas de marketing sobre a previsão base.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            sku_cenario = st.selectbox("Produto:", skus, key="sku_cenario")
        with c2:
            h = st.number_input("Semanas no Futuro:", 4, 52, 12, key="h_cenario")
        with c3:
            choque = st.slider("Choque de Demanda Global (%):", -50, 100, 0, step=5)
            
        st.markdown("**Simular Promoção Específica**")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            semana_promo = st.selectbox("Aplicar Promoção na:", [f"Semana {i+1}" for i in range(h)])
        with col_p2:
            impacto_promo = st.number_input("Impacto da Promoção (%):", 0, 200, 0, step=10)
            
        if st.button("Gerar Cenário Executivo", type="primary"):
            df_agg = eda.agregar_dados(sku_cenario, frequencia="W")
            series = df_agg.set_index('data')['quantidade_vendida']
            
            # Utilizando Média Móvel como baseline simples para a simulação de cenário
            _, fcast = ForecastEngine.simple_moving_average(series, h, window=4)
            
            if fcast is not None:
                last_date = series.index[-1]
                future_dates = pd.date_range(start=last_date, periods=h+1, freq="W")[1:]
                
                fcast_cenario = fcast * (1 + (choque / 100))
                idx_promo = int(semana_promo.split(" ")[1]) - 1
                fcast_cenario[idx_promo] = fcast_cenario[idx_promo] * (1 + (impacto_promo / 100))
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=future_dates, y=fcast, mode='lines', name='Base Matemática', line=dict(dash='dash', color='grey')))
                fig.add_trace(go.Scatter(x=future_dates, y=fcast_cenario, mode='lines+markers', name='Cenário Alterado', line=dict(color='blue', width=2)))
                fig.update_layout(title="Comparativo de Cenários", hovermode="x unified", margin=dict(l=0, r=0, t=50, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Histórico insuficiente para criar baseline de simulação.")

    # --- LÓGICA DA ABA 2 (CPFR INTERATIVO) ---
    with tab2:
        st.markdown("Alinhe a previsão estatística interna com o plano de negócios do seu cliente ou fornecedor.")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            sku_cpfr = st.selectbox("Produto para Consenso:", skus, key="sku_cpfr")
        with col_c2:
            h_cpfr = st.slider("Horizonte de Análise (Semanas):", 4, 12, 4)
        
        df_agg_cpfr = eda.agregar_dados(sku_cpfr, frequencia="W")
        series_cpfr = df_agg_cpfr.set_index('data')['quantidade_vendida']
        _, fcast_cpfr = ForecastEngine.simple_moving_average(series_cpfr, h_cpfr, window=4)
        
        if fcast_cpfr is not None:
            last_date_cpfr = series_cpfr.index[-1]
            future_dates_cpfr = pd.date_range(start=last_date_cpfr, periods=h_cpfr+1, freq="W")[1:]
            
            # Construção do Dataframe para edição em tela
            df_cpfr = pd.DataFrame({
                "Semana (Data)": future_dates_cpfr.strftime('%Y-%m-%d'),
                "Estatística (Sistema)": np.round(fcast_cpfr, 0).astype(int),
                "Plano do Parceiro (Edite)": np.round(fcast_cpfr, 0).astype(int) 
            })
            
            st.info("💡 **Dica de Uso:** Dê um duplo clique nos valores da coluna 'Plano do Parceiro' para digitar as expectativas enviadas pelo seu cliente/fornecedor.")
            
            # Tabela de dados editável pelo usuário
            df_editado = st.data_editor(
                df_cpfr,
                column_config={
                    "Semana (Data)": st.column_config.Column(disabled=True),
                    "Estatística (Sistema)": st.column_config.NumberColumn(disabled=True),
                    "Plano do Parceiro (Edite)": st.column_config.NumberColumn(min_value=0)
                },
                hide_index=True,
                use_container_width=True
            )
            
            df_editado['Divergência (%)'] = ((df_editado['Plano do Parceiro (Edite)'] - df_editado['Estatística (Sistema)']) / df_editado['Estatística (Sistema)']) * 100
            
            alertas = df_editado[abs(df_editado['Divergência (%)']) >= 20]
            
            st.markdown("### Análise de Consenso")
            if not alertas.empty:
                st.error("⚠️ **Atenção: Desvios críticos identificados no plano.** É recomendada uma reunião de alinhamento tático com o parceiro.")
                for _, row in alertas.iterrows():
                    direcao = "ACIMA" if row['Divergência (%)'] > 0 else "ABAIXO"
                    motivo = "Risco elevado de Ruptura de Estoque" if direcao == "ACIMA" else "Risco de Capital Imobilizado / Encalhe"
                    st.write(f"- Na semana de **{row['Semana (Data)']}**, o parceiro projeta um volume **{abs(row['Divergência (%)']):.1f}% {direcao}** da base estatística. (*{motivo}*)")
            else:
                st.success("✅ Previsões perfeitamente alinhadas. O desvio entre o sistema e o parceiro está dentro da margem de segurança operacional (< 20%).")
