import streamlit as st
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.eda import ExploratoryDataAnalysis
from src.forecasting import ForecastEngine
from src.evaluator import ForecastEvaluator

def gerar_texto_recomendacao(classe_demanda, metricas_erro, melhor_modelo):
    rec = []
    if "Crescente" in classe_demanda: rec.append("O produto apresenta tendência clara de crescimento nos últimos períodos.")
    elif "Estável" in classe_demanda: rec.append("A demanda é estável. Modelos baseados em Média Móvel ou Suavização Simples tendem a performar muito bem.")
    elif "Intermitente" in classe_demanda: rec.append("Demanda intermitente detectada (muitas vendas zeradas). O uso do método de Croston e análise via WAPE são altamente recomendados.")
        
    bias = metricas_erro.get('Viés (Bias)', 0)
    mae = metricas_erro.get('MAE', 1)
    
    if bias > (mae * 1.5): 
        rec.append("⚠️ O modelo apresenta tendência de **superestimar** a demanda, o que pode gerar excesso de estoque.")
    elif bias < -(mae * 1.5): 
        rec.append("⚠️ O modelo apresenta tendência de **subestimar** a demanda, aumentando o risco de ruptura e venda perdida.")
        
    rec.append(f"🎯 Com base no rigoroso backtesting executado, recomenda-se a adoção imediata do método **{melhor_modelo}** para o planejamento futuro.")
    return " ".join(rec)

def render():
    st.title("📑 Módulo 10: Relatórios e Laudos")
    
    if st.session_state.get('df_dados') is None:
        st.warning("⚠️ Nenhuma base de dados encontrada. Retorne ao Módulo 1.")
        st.stop()
        
    st.markdown("Nesta área, a inteligência do sistema analisa todos os dados em segundo plano e gera um laudo gerencial escrito automaticamente, pronto para basear suas reuniões de S&OP.")
    
    df_dados = st.session_state['df_dados']
    eda = ExploratoryDataAnalysis(df_dados)
    
    sku = st.selectbox("Selecione o SKU para gerar o Laudo:", eda.get_skus())
    
    if st.button("Gerar Laudo Gerencial", type="primary"):
        with st.spinner("Analisando histórico, rodando backtesting e compilando laudo..."):
            df_agg = eda.agregar_dados(sku, frequencia='W-MON')
            indicadores = eda.calcular_indicadores(df_agg)
            classe_demanda, _ = eda.classificar_comportamento(indicadores)
            
            series = df_agg.set_index('data')['quantidade_vendida']
            n = len(series)
            test_size = min(max(int(n * 0.2), 3), 12)
            train_size = n - test_size
            train, test = series.iloc[:train_size], series.iloc[train_size:]
            
            resultados = ForecastEngine.run_all(train, h=len(test), m=52)
            
            melhor_wape = float('inf')
            melhor_modelo = "Nenhum"
            melhores_metricas = {}
            
            for nome, (fit, fcast) in resultados.items():
                metricas = ForecastEvaluator.calculate_metrics(test.values, fcast)
                if not pd.isna(metricas['WAPE (%)']) and metricas['WAPE (%)'] < melhor_wape:
                    melhor_wape = metricas['WAPE (%)']
                    melhor_modelo = nome
                    melhores_metricas = metricas
                    
            texto_laudo = gerar_texto_recomendacao(classe_demanda, melhores_metricas, melhor_modelo)
            
            st.markdown("---")
            st.subheader(f"📋 Laudo Automático: {sku}")
            st.info(texto_laudo)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📊 Resumo Histórico")
                st.write(f"- **Volume Total:** {indicadores['total']:,.0f} unid.")
                st.write(f"- **Média por Período:** {indicadores['media']:,.1f} unid.")
                st.write(f"- **Coef. Variação (CV):** {indicadores['cv']:.2f}")
                st.write(f"- **Perfil Logístico:** {classe_demanda}")
            with col2:
                st.markdown("#### 🎯 Performance do Modelo")
                st.write(f"- **Modelo Campeão:** {melhor_modelo}")
                st.write(f"- **Acurácia Validada (WAPE):** {melhores_metricas.get('WAPE (%)', 0):.2f}%")
                st.write(f"- **Viés Geral:** {melhores_metricas.get('Viés (Bias)', 0):.2f}")
            
            st.markdown("---")
            st.markdown("#### 📥 Exportação de Dados")
            csv = df_agg.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar Base Histórica Deste Produto (CSV)",
                data=csv,
                file_name=f'historico_{sku}.csv',
                mime='text/csv',
            )