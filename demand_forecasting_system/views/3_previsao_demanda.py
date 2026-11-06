import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine

def render():
    st.title("📈 Módulo 3: Previsão de Demanda")
    st.markdown("Cálculo estatístico do futuro baseado no histórico limpo.")

    if 'df_dados' not in st.session_state or st.session_state['df_dados'] is None:
        st.warning("⚠️ Nenhuma base de dados encontrada. Por favor, volte ao Módulo 1 e carregue os dados.")
        return

    df = st.session_state['df_dados']
    df.columns = [c.lower() for c in df.columns]
    
    eda = ExploratoryDataAnalysis(df)

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

    # 1. Quando o botão é clicado, ativamos a "memória" do Streamlit
    if st.button("Gerar Previsão Matemática", type="primary"):
        st.session_state['mostrar_grafico_aba3'] = True
        st.session_state['parametros_aba3'] = (sku, freq_code, h)

    # 2. Se a memória estiver ativa para estes exatos parâmetros, mostramos o gráfico
    if st.session_state.get('mostrar_grafico_aba3') and st.session_state.get('parametros_aba3') == (sku, freq_code, h):
        
        # 3. Só calculamos a matemática pesada 1 vez e guardamos na memória. 
        # Assim, trocar de modelo no selectbox fica instantâneo!
        if 'resultados_aba3' not in st.session_state or st.session_state.get('parametros_calculados_aba3') != (sku, freq_code, h):
            df_agg = eda.agregar_dados(sku, frequencia=freq_code)
            
            if len(df_agg) < 3:
                st.error("Histórico insuficiente para previsões estatísticas (mínimo de 3 períodos).")
                st.session_state['mostrar_grafico_aba3'] = False
                return
                
            series = df_agg.set_index('data')['quantidade_vendida']
            m = 12 if freq == "Mensal" else (7 if freq == "Diária" else 52)
            
            # Guarda as contas na sessão
            st.session_state['resultados_aba3'] = ForecastEngine.run_all(series, h, m=m)
            st.session_state['series_aba3'] = series
            st.session_state['parametros_calculados_aba3'] = (sku, freq_code, h)

        # Recupera os dados da memória
        resultados = st.session_state['resultados_aba3']
        series = st.session_state['series_aba3']

        if not resultados:
            st.error("Erro ao calcular modelos estatísticos.")
            return

        st.markdown("---")
        st.subheader(f"📊 Projeção para {sku}")
        
        modelos_disponiveis = list(resultados.keys())
        idx_padrao = modelos_disponiveis.index('Holt-Winters') if 'Holt-Winters' in modelos_disponiveis else 0
        
        # Como o selectbox agora está fora do botão, interagir com ele não quebra a tela!
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
            * **Naive (Ingênuo):** Assume que o futuro será igual ao último período.
            * **Média Móvel:** Suaviza picos e quedas. Funciona bem para perfis altamente estáveis.
            * **SES:** Dá mais peso aos dados recentes e esquece o passado distante.
            * **Holt:** Identifica se o produto tem uma tendência clara de subida ou descida.
            * **Holt-Winters:** Identifica tendência E sazonalidade (ex: vende mais no Natal).
            * **Regressão:** Cria uma linha reta matemática baseada em todo o histórico.
            * **Croston:** Algoritmo especial para itens intermitentes e peças de reparo.
            """)
    else:
        # Se você alterar o produto ou a frequência antes de clicar no botão novamente, ele fecha o gráfico antigo por segurança
        if 'mostrar_grafico_aba3' in st.session_state:
            st.session_state['mostrar_grafico_aba3'] = False
