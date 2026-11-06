import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine

def render():
    st.title("🎯 Módulo 3: Previsão de Demanda")
    
    if st.session_state.get('df_dados') is None:
        st.warning("⚠️ Nenhuma base de dados encontrada. Retorne ao Módulo 1.")
        st.stop()
        
    with st.expander("📖 Entenda os Métodos de Previsão"):
        st.markdown("""
        * **Naive (Ingênuo):** Repete o último valor observado. Bom para demandas muito estáveis.
        * **Média Móvel Simples:** Tira a média dos últimos N períodos. Suaviza picos, mas atrasa na resposta a tendências.
        * **Suavização Exponencial (SES):** Dá mais peso aos dados recentes.
        * **Holt:** Identifica e projeta tendências de crescimento ou queda.
        * **Holt-Winters:** Lida com tendência e sazonalidade (picos que se repetem em ciclos, como Black Friday).
        * **Regressão Linear:** Traça uma reta de tendência global simplificada.
        * **Croston:** Específico para demanda intermitente (muitos períodos zerados entre as vendas).
        """)

    df_dados = st.session_state['df_dados']
    eda = ExploratoryDataAnalysis(df_dados)
    skus = eda.get_skus()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sku = st.selectbox("Produto (SKU):", skus)
    with col2:
        frequencia = st.selectbox("Granularidade:", ["Mensal (M)", "Semanal (W-MON)", "Diária (D)"])
        freq_code = frequencia.split("(")[1].replace(")", "")
    with col3:
        horizonte = st.number_input("Horizonte (Períodos):", min_value=1, max_value=24, value=6)
    with col4:
        metodo = st.selectbox("Método de Previsão:", [
            "Naive (Ingênuo)", 
            "Média Móvel Simples", 
            "Suavização Exponencial (SES)", 
            "Holt (Tendência)", 
            "Holt-Winters", 
            "Regressão Linear", 
            "Croston (Intermitente)"
        ])
        
    df_agg = eda.agregar_dados(sku, frequencia=freq_code)
    series = df_agg.set_index('data')['quantidade_vendida']
    sazonalidade_m = 12 if freq_code == 'M' else (52 if 'W' in freq_code else 7)
    
    fitted, forecast = None, None
    if metodo == "Naive (Ingênuo)": fitted, forecast = ForecastEngine.naive(series, horizonte)
    elif metodo == "Média Móvel Simples": fitted, forecast = ForecastEngine.simple_moving_average(series, horizonte)
    elif metodo == "Suavização Exponencial (SES)": fitted, forecast = ForecastEngine.simple_exponential_smoothing(series, horizonte)
    elif metodo == "Holt (Tendência)": fitted, forecast = ForecastEngine.holt(series, horizonte)
    elif metodo == "Holt-Winters":
        fitted, forecast = ForecastEngine.holt_winters(series, horizonte, m=sazonalidade_m)
        if forecast is None: st.error(f"Histórico insuficiente para Holt-Winters. Necessário {2*sazonalidade_m} períodos.")
    elif metodo == "Regressão Linear": fitted, forecast = ForecastEngine.linear_regression(series, horizonte)
    elif metodo == "Croston (Intermitente)": fitted, forecast = ForecastEngine.croston(series, horizonte)

    if forecast is not None:
        st.success(f"Previsão gerada com sucesso usando o método: {metodo}")
        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date, periods=horizonte+1, freq=freq_code)[1:]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.index, y=series.values, mode='lines+markers', name='Demanda Real (Histórico)', line=dict(color='black')))
        
        # Ajuste oculto por padrão (legendonly) para não sujar o gráfico
        fig.add_trace(go.Scatter(x=series.index, y=fitted.values, mode='lines', name='Ajuste (Fitted)', line=dict(dash='dot', color='orange'), visible='legendonly'))
        
        fig.add_trace(go.Scatter(x=future_dates, y=forecast, mode='lines+markers', name='Previsão', line=dict(color='green', width=3)))
        
        fig.update_layout(title=f'Previsão de Demanda para {sku} ({metodo})', template='plotly_white', hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📋 Valores Previstos")
        df_forecast = pd.DataFrame({'Data': future_dates.strftime('%Y-%m-%d'), 'Demanda Prevista': forecast.round(2)})
        st.dataframe(df_forecast.set_index('Data').T)