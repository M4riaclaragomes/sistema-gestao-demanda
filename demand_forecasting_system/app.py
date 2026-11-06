import streamlit as st
import importlib.util
import os

st.set_page_config(page_title="Sistema de Gestão e Previsão de Demanda", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

if 'df_dados' not in st.session_state:
    st.session_state['df_dados'] = None

def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    st.sidebar.title("📦 Gestão de Demanda")
    st.sidebar.markdown("---")
    
    menu = {
        "1. Importação de Dados": "views/importacao.py",
        "2. Análise Histórica": "views/2_analise_historica.py",
        "3. Previsão de Demanda": "views/3_previsao_demanda.py",
        "4. Comparação de Modelos": "views/4_comparacao_modelos.py",
        "5. Dashboard Gerencial": "views/5_dashboard_gerencial.py",
        "6. Cenários e CPFR": "views/6_cenarios_cpfr.py",
        "7. Relatórios": "views/7_relatorios.py"
    }
    
    escolha = st.sidebar.radio("Navegação:", list(menu.keys()))
    st.sidebar.markdown("---")
    st.sidebar.info("Status dos Dados:\n" + ("✅ Base Carregada" if st.session_state['df_dados'] is not None else "⚠️ Nenhuma base carregada"))

    filepath = menu[escolha]
    if filepath and os.path.exists(filepath):
        view_module = load_module("view_module", filepath)
        view_module.render()
    else:
        st.title(escolha)
        st.warning("🚧 Este módulo está em desenvolvimento.")

if __name__ == "__main__":
    main()