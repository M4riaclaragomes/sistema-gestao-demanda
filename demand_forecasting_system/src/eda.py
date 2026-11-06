import pandas as pd
import numpy as np

class ExploratoryDataAnalysis:
    def __init__(self, df): self.df = df.copy()
    def get_skus(self): return sorted(self.df['sku'].unique())
    def agregar_dados(self, sku, frequencia='W'):
        df_sku = self.df[self.df['sku'] == sku].set_index('data')
        return df_sku['quantidade_vendida'].resample(frequencia).sum().reset_index()
        
    def calcular_indicadores(self, df_agg):
        demanda = df_agg['quantidade_vendida']
        if len(demanda) == 0: return None
        media = demanda.mean()
        cv = demanda.std() / media if media > 0 else 0
        meio = len(demanda) // 2
        m1, m2 = demanda.iloc[:meio].mean(), demanda.iloc[meio:].mean()
        crescimento = ((m2 - m1) / m1) * 100 if m1 > 0 else 0
        return {'total': demanda.sum(), 'media': media, 'maximo': demanda.max(), 'minimo': demanda.min(), 'desvio_padrao': demanda.std(), 'cv': cv, 'crescimento_pct': crescimento, 'periodos_zerados': (demanda == 0).sum(), 'pct_zerados': (demanda == 0).sum() / len(demanda)}
        
    def classificar_comportamento(self, indicadores):
        if not indicadores: return "Sem Dados", ""
        if indicadores['pct_zerados'] > 0.30: return "Intermitente", "Muitos períodos sem demanda."
        elif indicadores['cv'] < 0.20 and abs(indicadores['crescimento_pct']) < 10: return "Estável", "Baixa variabilidade."
        elif indicadores['crescimento_pct'] > 20: return "Crescente", "Tendência de alta."
        elif indicadores['crescimento_pct'] < -20: return "Decrescente", "Tendência de queda."
        elif indicadores['cv'] >= 0.50: return "Irregular", "Alta variabilidade (picos)."
        else: return "Sazonal/Variável", "Variação moderada."
