import streamlit as st
import pandas as pd
import numpy as np
import os
from src.data_processor import DataProcessor

def render():
    st.title("📥 Módulo 1: Importação e Tratamento de Dados")
    st.markdown("""
    Importe os dados históricos e decida como tratar anomalias (como vendas a zero ou negativas) 
    para garantir que as previsões futuras refletem a verdadeira demanda e não erros do passado.
    """)

    processor = DataProcessor()

    if 'usar_demo' not in st.session_state:
        st.session_state['usar_demo'] = False
    if 'df_bruto' not in st.session_state:
        st.session_state['df_bruto'] = None

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Carregar Base Própria")
        arquivo_upload = st.file_uploader("Selecione um ficheiro Excel (.xlsx) ou CSV", type=['csv', 'xlsx', 'xls'])
    
    with col2:
        st.subheader("Utilizar Base de Demonstração")
        st.markdown("Carregue a base que contém os 5 perfis estatísticos e as anomalias simuladas de rutura.")
        if st.button("Carregar Dados de Demonstração", type="primary"):
            st.session_state['usar_demo'] = True 
            st.session_state['df_bruto'] = None 

    origem = ""

    if arquivo_upload is not None:
        st.session_state['usar_demo'] = False 
        tipo = arquivo_upload.name.split('.')[-1]
        df_temp, msg = processor.carregar_arquivo(arquivo_upload, tipo)
        if df_temp is None:
            st.error(msg)
        else:
            origem = "Arquivo Próprio"
            st.session_state['df_bruto'] = df_temp
            
    elif st.session_state['usar_demo']:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        demo_path = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'demo_dataset.csv'))
        if os.path.exists(demo_path):
            with open(demo_path, 'rb') as f:
                df_temp, msg = processor.carregar_arquivo(f, 'csv')
            origem = "Base de Demonstração"
            st.session_state['df_bruto'] = df_temp
        else:
            st.error("Ficheiro de demonstração não encontrado. Verifique se a pasta 'data' foi enviada.")

    if st.session_state['df_bruto'] is not None:
        df_atual = st.session_state['df_bruto'].copy()
        st.success(f"Base carregada com sucesso! ({origem}) - {len(df_atual)} registos")
        
        st.markdown("---")
        st.subheader("🛠️ Painel de Tratamento de Anomalias e Ruturas")
        
        df_atual['data'] = pd.to_datetime(df_atual['data'], errors='coerce')
        # 2. RESOLUÇÃO DA BASE NÃO MUDAR: Força a conversão matemática para impedir que o "0" seja lido como texto
        df_atual['quantidade_vendida'] = pd.to_numeric(df_atual['quantidade_vendida'], errors='coerce')
        
        mascara_zeros = df_atual['quantidade_vendida'] == 0
        mascara_negativos = df_atual['quantidade_vendida'] < 0
        mascara_nulos = df_atual['quantidade_vendida'].isna()
        
        total_anomalias = mascara_zeros.sum() + mascara_negativos.sum() + mascara_nulos.sum()
        
        if total_anomalias > 0:
            st.warning(f"⚠️ Foram encontradas {total_anomalias} anomalias na base de dados (vendas a zero, negativas ou nulas).")
            
            estrategia = st.radio(
                "Estratégia de Tratamento:",
                options=[
                    "1. Manter os valores originais (Assumir que a queda foi uma flutuação real de mercado)",
                    "2. Substituir pela Média do Produto (Tratar como erro de sistema ou rutura de stock)",
                    "3. Remover as linhas problemáticas (Ignorar os dias com falhas)"
                ]
            )
            
            if "2. Substituir" in estrategia:
                df_tratado = df_atual.copy()
                medias = df_tratado[df_tratado['quantidade_vendida'] > 0].groupby('sku')['quantidade_vendida'].mean()
                mascara_invalidos = (df_tratado['quantidade_vendida'] <= 0) | (df_tratado['quantidade_vendida'].isna())
                df_tratado.loc[mascara_invalidos, 'quantidade_vendida'] = df_tratado.loc[mascara_invalidos, 'sku'].map(medias)
                st.info("✅ Histórico de Tratamento: As anomalias foram substituídas pela média histórica.")
                
            elif "3. Remover" in estrategia:
                df_tratado = df_atual[~mascara_zeros & ~mascara_negativos & ~mascara_nulos].copy()
                st.info(f"✅ Histórico de Tratamento: {total_anomalias} linhas anómalas foram apagadas da base.")
            else:
                df_tratado = df_atual.copy()
                st.info("✅ Histórico de Tratamento: Os valores originais foram mantidos.")
        else:
            st.info("✅ A base de dados está íntegra e não apresenta anomalias graves de quantidade.")
            df_tratado = df_atual.copy()

        st.markdown("### 📊 Visualizador da Base Completa")
        st.dataframe(df_tratado, use_container_width=True, height=400)
        
        if st.button("Confirmar e Guardar Base Tratada", type="primary"):
            st.session_state['df_dados'] = df_tratado.copy()
            st.success("Dados validados e guardados com sucesso! Pode avançar para o menu de Análise Histórica.")
            st.balloons()
