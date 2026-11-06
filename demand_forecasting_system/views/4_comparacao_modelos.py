import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine

def render():
    st.title("🏆 Módulo 4: Comparação de Modelos")
    st.markdown("Avalie a precisão de diferentes algoritmos através de um **Teste Cego (Out-of-Sample)** para descobrir qual se ajusta melhor ao futuro do seu produto.")

    if 'df_dados' not in st.session_state or st.session_state['df_dados'] is None:
        st.warning("⚠️ Nenhuma base de dados encontrada. Por favor, volte ao Módulo 1 e carregue os dados.")
        return

    df = st.session_state['df_dados']
    df.columns = [c.lower() for c in df.columns]
    
    eda = ExploratoryDataAnalysis(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        sku_list = df['sku'].unique()
        sku = st.selectbox("Selecione o SKU para análise:", sku_list)
    with col2:
        freq_map = {"Diária": "D", "Semanal": "W", "Mensal": "ME"}
        freq = st.selectbox("Frequência:", list(freq_map.keys()), index=2)
        freq_code = freq_map[freq]
    with col3:
        h = st.number_input("Horizonte (Quantos períodos prever?):", min_value=1, max_value=365, value=12)

    if st.button("Executar Batalha de Modelos", type="primary"):
        df_agg = eda.agregar_dados(sku, frequencia=freq_code)
        
        if len(df_agg) <= h + 3:
            st.error(f"Histórico insuficiente para separar Treino e Teste. A base tem {len(df_agg)} períodos e você quer testar {h}. Reduza o horizonte.")
            return
            
        series = df_agg.set_index('data')['quantidade_vendida']
        m = 12 if freq == "Mensal" else (7 if freq == "Diária" else 52)
        
        # TÉCNICA DE DATA SCIENCE: Separar em Treino (passado) e Teste (futuro real)
        train = series.iloc[:-h]
        test = series.iloc[-h:]
        
        # Roda os modelos apenas com o Treino para ver se eles acertam o Teste (Teste Cego)
        resultados_teste = ForecastEngine.run_all(train, h, m=m)
        
        metricas = []
        for nome, (fit, fcast) in resultados_teste.items():
            if fcast is not None and len(fcast) == len(test):
                erro = test.values - fcast
                mae = np.mean(np.abs(erro))
                rmse = np.sqrt(np.mean(erro**2))
                
                test_safe = np.where(test.values == 0, 1e-9, test.values)
                mape = np.mean(np.abs(erro / test_safe)) * 100
                
                metricas.append({
                    "Modelo": nome,
                    "MAE (Erro Médio Absoluto)": mae,
                    "RMSE (Raiz do Erro Quadrático)": rmse,
                    "MAPE (%)": mape
                })
        
        if not metricas:
            st.error("Nenhum modelo conseguiu calcular o horizonte selecionado.")
            return
            
        df_metricas = pd.DataFrame(metricas).sort_values("MAE (Erro Médio Absoluto)").reset_index(drop=True)
        
        df_display = df_metricas.copy()
        df_display["MAE (Erro Médio Absoluto)"] = df_display["MAE (Erro Médio Absoluto)"].round(2)
        df_display["RMSE (Raiz do Erro Quadrático)"] = df_display["RMSE (Raiz do Erro Quadrático)"].round(2)
        df_display["MAPE (%)"] = df_display["MAPE (%)"].round(2).astype(str) + "%"
        
        st.dataframe(df_display, use_container_width=True)
        
        melhor_modelo = df_metricas.iloc[0]["Modelo"]
        st.success(f"🏆 **Vencedor:** O modelo **{melhor_modelo}** apresentou a menor margem de erro ao prever dados desconhecidos.")
        
        st.markdown("### 📈 Visualização do Teste Cego (Top 3)")
        
        fig = go.Figure()
        
        # Plota os dados de Treino (Preto) e de Teste (Cinza Claro)
        fig.add_trace(go.Scatter(
            x=train.index, y=train.values, mode='lines', 
            name='Histórico (Treino)', line=dict(color='black', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=test.index, y=test.values, mode='lines+markers', 
            name='Realidade Escondida (Teste)', line=dict(color='lightgrey', width=3)
        ))
        
        top_3 = df_metricas.head(3)["Modelo"].tolist()
        cores = ['#00b050', '#0070c0', '#ffc000']
        
        future_dates = test.index
        
        for i, modelo in enumerate(top_3):
            _, fcast = resultados_teste[modelo]
            fig.add_trace(go.Scatter(
                x=future_dates, y=fcast, mode='lines', 
                name=f'{i+1}º - {modelo}', 
                line=dict(color=cores[i], width=3 if i == 0 else 2, dash='solid' if i == 0 else 'dash')
            ))
            
        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
