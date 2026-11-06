import streamlit as st
import pandas as pd
import os
import sys
import plotly.graph_objects as go

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine
from src.evaluator import ForecastEvaluator

def render():
    st.title("🏆 Módulo 4 e 5: Comparação e Validação")
    
    if st.session_state.get('df_dados') is None:
        st.warning("⚠️ Nenhuma base de dados encontrada.")
        st.stop()
        
    with st.expander("📖 Entenda os Indicadores de Erro"):
        st.markdown("""
        * **MAE (Erro Absoluto Médio):** A média da diferença absoluta entre o previsto e o real. (Ex: Errou por 5 unidades em média).
        * **RMSE (Raiz do Erro Quadrático Médio):** Penaliza erros muito grandes (outliers).
        * **MAPE (%):** Erro percentual médio. (Ex: Errou por 15% em média). Pode falhar matematicamente se houver demanda zerada.
        * **WAPE (%):** Erro percentual ponderado pelo volume. Excelente para logística, pois lida perfeitamente com períodos zerados.
        * **Viés (Bias):** Se positivo, o modelo está **superestimando** (prevê mais do que vende). Se negativo, está **subestimando** (risco de ruptura).
        """)

    df_dados = st.session_state['df_dados']
    eda = ExploratoryDataAnalysis(df_dados)
    skus = eda.get_skus()
    
    col1, col2, col3 = st.columns(3)
    with col1: sku = st.selectbox("Produto (SKU):", skus, key='cmp_sku')
    with col2:
        frequencia = st.selectbox("Granularidade:", ["Mensal (M)", "Semanal (W-MON)", "Diária (D)"], key='cmp_freq')
        freq_code = frequencia.split("(")[1].replace(")", "")
    with col3: metrica_alvo = st.selectbox("Métrica para Classificação (Ranking):", ["WAPE (%)", "MAPE (%)", "MAE", "RMSE"])

    if st.button("Executar Backtesting e Comparar Modelos", type="primary"):
        with st.spinner("Executando modelos estatísticos..."):
            df_agg = eda.agregar_dados(sku, frequencia=freq_code)
            series = df_agg.set_index('data')['quantidade_vendida']
            sazonalidade_m = 12 if freq_code == 'M' else (52 if 'W' in freq_code else 7)
            
            n = len(series)
            test_size = min(max(int(n * 0.2), 3), 12)
            train_size = n - test_size
            
            if train_size < 10:
                st.error("Histórico muito curto para realizar o backtesting.")
                st.stop()
                
            train_series, test_series = series.iloc[:train_size], series.iloc[train_size:]
            resultados = ForecastEngine.run_all(train_series, h=test_size, m=sazonalidade_m)
            
            tabela_erros = []
            for nome_modelo, (fitted, fcast) in resultados.items():
                metricas = ForecastEvaluator.calculate_metrics(test_series.values, fcast)
                linha = {'Modelo': nome_modelo, 'fcast': fcast}
                linha.update(metricas)
                tabela_erros.append(linha)
                
            df_erros = pd.DataFrame(tabela_erros).sort_values(by=metrica_alvo).reset_index(drop=True)
            melhor_modelo = df_erros.iloc[0]['Modelo']
            
            st.success("Análise concluída!")
            st.info(f"💡 **Recomendação:** O método **{melhor_modelo}** apresentou o melhor desempenho (menor {metrica_alvo}).")
            
            cols_format = {'MAE': '{:.2f}', 'MSE': '{:.2f}', 'RMSE': '{:.2f}', 'MAPE (%)': '{:.2f}%', 'WAPE (%)': '{:.2f}%', 'Viés (Bias)': '{:.2f}', 'Tracking Signal': '{:.2f}'}
            st.dataframe(df_erros.drop(columns=['fcast']).style.format(cols_format), use_container_width=True)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=series.index, y=series.values, mode='lines', name='Realizado', line=dict(color='black', width=3)))
            
            # Adiciona os modelos ao gráfico, mas esconde todos (legendonly) exceto o melhor modelo
            for idx, row in df_erros.iterrows():
                nome = row['Modelo']
                fcast = row['fcast']
                visibilidade = True if nome == melhor_modelo else 'legendonly'
                fig.add_trace(go.Scatter(x=test_series.index, y=fcast, mode='lines+markers', name=nome, visible=visibilidade))
            
            fig.add_vline(x=test_series.index[0], line_width=2, line_dash="dash", line_color="red")
            fig.update_layout(template='plotly_white', hovermode='x unified', title="Validação Temporal (Do marco vermelho em diante é o passado desconhecido)")
            st.plotly_chart(fig, use_container_width=True)