import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
import sys

# Revertido para o método de caminhos seguro que evita conflito com o /mount/src/ da nuvem
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))

from src.eda import EDA
from src.forecasting import ForecastEngine

def render():
    st.title("📈 Módulo 3: Previsão de Demanda")
    st.markdown("Cálculo estatístico do futuro baseado no histórico limpo.")

    if 'df_dados' not in st.session_state or st.session_state['df_dados'] is None:
        st.warning("⚠️ Nenhuma base de dados encontrada. Por favor, volte ao Módulo 1 e carregue os dados.")
        return

    df = st.session_state['df_dados']
    df.columns = [c.lower() for c in df.columns]
    
    eda = EDA(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        sku_list = df['sku'].unique()
        sku = st.selectbox("Selecione o SKU para prever:", sku_list)
    with col2:
        freq_map = {"Diária": "D", "Semanal": "W", "Mensal": "ME"}
        freq = st.selectbox("Frequência da Previsão:", list(freq_map.keys()), index=2)
        freq_code = freq_map[freq]
    with col3:
        h = st.number_input("Horizonte (Quantos períodos para frente?):", min_value=1, max_value=365, value=12)

    if st.button("Gerar Previsão Matemática", type="primary"):
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
        st.subheader(f"📊 Projeção para {sku}")
        
        modelos_disponiveis = list(resultados.keys())
        idx_padrao = modelos_disponiveis.index('Holt-Winters') if 'Holt-Winters' in modelos_disponiveis else 0
        modelo_selecionado = st.selectbox("Selecione o Modelo Estatístico:", modelos_disponiveis, index=idx_padrao)
        
        fit, fcast = resultados[modelo_selecionado]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values, mode='lines+markers', 
            name='Demanda Real (Histórico)', line=dict(color='black', width=2)
        ))
        
        if fit is not None:
            fig.add_trace(go.Scatter(
                x=series.index, y=fit, mode='lines', 
                name='Ajuste Matemático', line=dict(dash='dot', color='orange', width=2),
                visible='legendonly'
            ))
        
        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date, periods=h+1, freq=freq_code)[1:]
        
        fig.add_trace(go.Scatter(
            x=future_dates, y=fcast, mode='lines+markers', 
            name=f'Previsão ({modelo_selecionado})', line=dict(color='green', width=3)
        ))
        
        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📖 Entenda os Modelos Estatísticos"):
            st.markdown("""
            * **Naive (Ingênuo):** O modelo mais básico. Assume que o futuro será exatamente igual ao último período. Ideal para produtos intermitentes.
            * **Média Móvel:** Suaviza picos e quedas. Funciona bem para perfis altamente estáveis.
            * **SES (Suavização Exponencial Simples):** Dá mais peso aos dados recentes e esquece o passado distante.
            * **Holt:** Identifica se o produto tem uma tendência clara (se as vendas estão a subir ou a descer).
            * **Holt-Winters:** O mais avançado. Identifica tendência E sazonalidade (ex: vende mais no Natal).
            * **Regressão:** Cria uma linha reta de tendência matemática baseada em todo o histórico.
            * **Croston:** Algoritmo especial para logística de peças de reparo e itens com muitos dias de venda zerada.
            """)
