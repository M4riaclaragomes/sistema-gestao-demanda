import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import sys

# Mapeamento de caminhos robusto para o servidor Linux do Streamlit
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine

def render():
    st.title("🏆 Módulo 4: Comparação de Modelos")
    st.markdown("Avalie a precisão de diferentes algoritmos para descobrir qual se ajusta melhor ao seu produto.")

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
        # CORREÇÃO: "Mensal" agora usa "ME" para compatibilidade com o Pandas atualizado
        freq_map = {"Diária": "D", "Semanal": "W", "Mensal": "ME"}
        freq = st.selectbox("Frequência:", list(freq_map.keys()), index=2)
        freq_code = freq_map[freq]
    with col3:
        h = st.number_input("Horizonte (Quantos períodos prever?):", min_value=1, max_value=365, value=12)

    if st.button("Executar Batalha de Modelos", type="primary"):
        df_agg = eda.agregar_dados(sku, frequencia=freq_code)
        
        if len(df_agg) < 3:
            st.error("Histórico insuficiente para previsões estatísticas (mínimo de 3 períodos).")
            return
            
        series = df_agg.set_index('data')['quantidade_vendida']
        m = 12 if freq == "Mensal" else (7 if freq == "Diária" else 52)
        
        resultados = ForecastEngine.run_all(series, h, m=m)
        
        if not resultados:
            st.error("Erro ao calcular modelos estatísticos.")
            return

        st.markdown("---")
        st.subheader(f"📊 Ranking de Precisão para {sku}")

        # Calcular métricas de erro histórico (in-sample)
        metricas = []
        for nome, (fit, fcast) in resultados.items():
            if fit is not None:
                erro = series - fit
                mae = np.mean(np.abs(erro))
                rmse = np.sqrt(np.mean(erro**2))
                
                # Evitar divisão por zero no cálculo do MAPE
                series_safe = np.where(series == 0, 1e-9, series)
                mape = np.mean(np.abs(erro / series_safe)) * 100
                
                metricas.append({
                    "Modelo": nome,
                    "MAE (Erro Médio Absoluto)": mae,
                    "RMSE (Raiz do Erro Quadrático)": rmse,
                    "MAPE (%)": mape
                })
        
        # Cria a tabela ordenada do menor erro (melhor) para o maior (pior)
        df_metricas = pd.DataFrame(metricas).sort_values("MAE (Erro Médio Absoluto)").reset_index(drop=True)
        
        # Formatação limpa para exibição
        df_display = df_metricas.copy()
        df_display["MAE (Erro Médio Absoluto)"] = df_display["MAE (Erro Médio Absoluto)"].round(2)
        df_display["RMSE (Raiz do Erro Quadrático)"] = df_display["RMSE (Raiz do Erro Quadrático)"].round(2)
        df_display["MAPE (%)"] = df_display["MAPE (%)"].round(2).astype(str) + "%"
        
        st.dataframe(df_display, use_container_width=True)
        
        melhor_modelo = df_metricas.iloc[0]["Modelo"]
        st.success(f"🏆 **Vencedor:** O modelo **{melhor_modelo}** apresentou a menor margem de erro na simulação do passado.")
        
        # Gráfico comparativo visual
        st.markdown("### 📈 Visualização das Previsões (Top 3)")
        
        fig = go.Figure()
        
        # Demanda Real Histórica
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values, mode='lines+markers', 
            name='Demanda Real (Passado)', line=dict(color='black', width=3)
        ))
        
        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date, periods=h+1, freq=freq_code)[1:]
        
        # Desenha as linhas apenas dos 3 melhores modelos para não poluir o gráfico
        top_3 = df_metricas.head(3)["Modelo"].tolist()
        cores = ['#00b050', '#0070c0', '#ffc000']
        
        for i, modelo in enumerate(top_3):
            _, fcast = resultados[modelo]
            fig.add_trace(go.Scatter(
                x=future_dates, y=fcast, mode='lines', 
                name=f'{i+1}º - {modelo}', 
                line=dict(color=cores[i], width=2 if i > 0 else 3, dash='solid' if i == 0 else 'dash')
            ))
            
        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
