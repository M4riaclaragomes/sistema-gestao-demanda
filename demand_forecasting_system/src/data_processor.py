import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self):
        self.expected_columns = ['sku', 'data', 'quantidade_vendida']
        
    def carregar_arquivo(self, file_object, file_type):
        try:
            if file_type == 'csv': df = pd.read_csv(file_object)
            elif file_type in ['xls', 'xlsx']: df = pd.read_excel(file_object)
            else: return None, "Formato não suportado."
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            return df, "Sucesso"
        except Exception as e: return None, str(e)

    def validar_dados(self, df):
        alertas = {'colunas_ausentes': [], 'valores_nulos': 0, 'valores_negativos': 0, 'linhas_duplicadas': 0, 'tipos_invalidos_data': False}
        for col in self.expected_columns:
            if col not in df.columns: alertas['colunas_ausentes'].append(col)
        if alertas['colunas_ausentes']: return alertas
        alertas['valores_nulos'] = df['quantidade_vendida'].isna().sum()
        if df['quantidade_vendida'].dtype in ['int64', 'float64']: alertas['valores_negativos'] = (df['quantidade_vendida'] < 0).sum()
        alertas['linhas_duplicadas'] = df.duplicated(subset=['sku', 'data']).sum()
        try: pd.to_datetime(df['data'])
        except: alertas['tipos_invalidos_data'] = True
        return alertas

    def aplicar_tratamento_padrao(self, df):
        df_tratado = df.copy()
        df_tratado['data'] = pd.to_datetime(df_tratado['data'], errors='coerce')
        df_tratado = df_tratado.dropna(subset=['sku', 'data'])
        df_tratado['quantidade_vendida'] = df_tratado['quantidade_vendida'].fillna(0).apply(lambda x: max(0, x))
        return df_tratado.sort_values(by=['sku', 'data']).reset_index(drop=True)
