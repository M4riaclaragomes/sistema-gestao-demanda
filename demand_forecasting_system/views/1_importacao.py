import streamlit as st
import pandas as pd
import os
from src.data_processor import DataProcessor

def render():
    st.title("📥 Módulo 1: Importação de Dados")
    st.markdown("""
    Nesta etapa, você deve importar os dados históricos de vendas ou demanda. 
    O sistema realizará uma análise automática da qualidade da base antes de permitir as previsões.
    """)

    processor = DataProcessor()

    if 'usar_demo' not in st.session_state:
        st.session_state['usar_demo'] = False

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Carregar Base Própria")
        arquivo_upload = st.file_uploader("Selecione um arquivo Excel (.xlsx) ou CSV", type=['csv', 'xlsx', 'xls'])
    
    with col2:
        st.subheader("Utilizar Base de Demonstração")
        st.markdown("Carregue a base contendo os 5 perfis estatísticos (Estável, Crescente, Sazonal, Irregular e Intermitente).")
        if st.button("Carregar Dados de Demonstração", type="primary"):
            st.session_state['usar_demo'] = True 

    df_bruto = None
    origem = ""

    if arquivo_upload is not None:
        st.session_state['usar_demo'] = False 
        tipo = arquivo_upload.name.split('.')[-1]
        df_bruto, msg = processor.carregar_arquivo(arquivo_upload, tipo)
        if df_bruto is None:
            st.error(msg)
        else:
            origem = "Arquivo Próprio"
            
    elif st.session_state['usar_demo']:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        demo_path = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'demo_dataset.csv'))
        if os.path.exists(demo_path):
            with open(demo_path, 'rb') as f:
                df_bruto, msg = processor.carregar_arquivo(f, 'csv')
            origem = "Base de Demonstração"
        else:
            st.error("Arquivo de demonstração não encontrado. Verifique se a pasta 'data' foi enviada.")

    if df_bruto is not None:
        st.success(f"Base carregada com sucesso! ({origem}) - {len(df_bruto)} registros")
        
        st.markdown("### 🔍 Validação de Qualidade de Dados")
        alertas = processor.validar_dados(df_bruto)
        
        if alertas['colunas_ausentes']:
            st.error(f"Erro Crítico: Faltam colunas obrigatórias: {', '.join(alertas['colunas_ausentes'])}")
            st.stop()
            
        avisos = 0
        if alertas['valores_nulos'] > 0:
            st.warning(f"⚠️ Encontrados {alertas['valores_nulos']} registros com quantidade nula/vazia.")
            avisos += 1
        if alertas['valores_negativos'] > 0:
            st.warning(f"⚠️ Encontrados {alertas['valores_negativos']} registros com quantidade negativa.")
            avisos += 1
        if alertas['linhas_duplicadas'] > 0:
            st.warning(f"⚠️ Encontradas {alertas['linhas_duplicadas']} linhas duplicadas (Mesmo SKU na mesma data).")
            avisos += 1
        if alertas['tipos_invalidos_data']:
            st.error("Erro Crítico: Falha ao converter a coluna de datas.")
            st.stop()
            
        if avisos == 0:
            st.info("✅ A base de dados está íntegra e não apresenta anomalias graves.")

        st.markdown("### 📊 Visualizador da Base")
        
        # Aplica o tratamento básico (remover duplicadas) por segurança
        df_tratado = processor.aplicar_tratamento_padrao(df_bruto)
        
        st.dataframe(df_tratado, use_container_width=True, height=400)
        
        if st.button("Confirmar e Salvar Base para Análise", type="primary"):
            st.session_state['df_dados'] = df_tratado.copy()
            st.success("Dados salvos com sucesso! Acesse o menu lateral para iniciar a Análise Histórica.")
            st.balloons()
