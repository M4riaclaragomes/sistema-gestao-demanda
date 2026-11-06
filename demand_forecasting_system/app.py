import os
import sys
import importlib.util
import streamlit as st

# 1. RESOLUÇÃO DEFINITIVA DO IMPORTERROR: Injeta a pasta raiz no sistema de forma global
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

def load_module(module_name, filepath):
    if not os.path.exists(filepath):
        return None
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    st.set_page_config(page_title="Gestão de Demanda", page_icon="📦", layout="wide")
    
    st.sidebar.title("📦 Gestão de Demanda")
    st.sidebar.markdown("---")
    
    PAGES = {
        "1. Importação de Dados": "views/1_importacao.py",
        "2. Análise Histórica": "views/2_analise_historica.py",
        "3. Previsão de Demanda": "views/3_previsao_demanda.py",
        "4. Comparação de Modelos": "views/4_comparacao_modelos.py",
        "5. Dashboard Gerencial": "views/5_dashboard_gerencial.py",
        "6. Cenários e CPFR": "views/6_cenarios_cpfr.py",
        "7. Relatórios": "views/7_relatorios.py"
    }
    
    st.sidebar.markdown("Navegação:")
    selection = st.sidebar.radio("", list(PAGES.keys()))
    
    filepath = os.path.join(ROOT_DIR, PAGES[selection])
    view_module = load_module("view_module", filepath)
    
    if view_module:
        view_module.render()
    else:
        st.title(selection)
        st.warning("🚧 Este módulo está em desenvolvimento.")

if __name__ == "__main__":
    main()
