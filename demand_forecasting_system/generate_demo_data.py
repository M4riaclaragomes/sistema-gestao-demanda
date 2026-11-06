import pandas as pd
import numpy as np
import os

def generate_demo_dataset():
    """
    Gera um dataset de demonstração com 5 perfis de demanda diferentes.
    Período: 2 anos (104 semanas) finalizando na data atual para previsões futuras.
    """
    np.random.seed(42)
    
    # Gerando 104 semanas terminando no final de 2026
    dates = pd.date_range(end=pd.Timestamp.now().floor('D'), periods=104, freq='W-MON')
    n = len(dates)
    
    data = []
    
    # 1. SKU_001: Demanda Estável
    base_stable = 500
    demand_stable = np.random.normal(base_stable, 20, n).astype(int)
    for i, d in enumerate(dates):
        data.append(['SKU_001', 'Produto Estável', 'Básicos', d, max(0, demand_stable[i]), 50.0])

    # 2. SKU_002: Tendência de Crescimento
    base_trend = 100
    trend = np.linspace(0, 400, n)
    demand_trend = np.random.normal(base_trend + trend, 30, n).astype(int)
    for i, d in enumerate(dates):
        data.append(['SKU_002', 'Produto em Crescimento', 'Lançamentos', d, max(0, demand_trend[i]), 120.0])

    # 3. SKU_003: Comportamento Sazonal
    base_seasonal = 300
    seasonality = 200 * np.sin(np.linspace(0, 4 * np.pi, n))
    demand_seasonal = np.random.normal(base_seasonal + seasonality, 25, n).astype(int)
    for i, d in enumerate(dates):
        data.append(['SKU_003', 'Produto Sazonal', 'Sazonais', d, max(0, demand_seasonal[i]), 80.0])

    # 4. SKU_004: Demanda Irregular
    demand_irregular = np.random.uniform(50, 800, n).astype(int)
    for i, d in enumerate(dates):
        data.append(['SKU_004', 'Produto Irregular', 'Moda', d, max(0, demand_irregular[i]), 150.0])

    # 5. SKU_005: Demanda Intermitente
    demand_intermittent = np.random.choice([0, 0, 0, 0, 0, 10, 15, 5, 20], size=n)
    for i, d in enumerate(dates):
        data.append(['SKU_005', 'Produto Intermitente', 'Peças de Reposição', d, max(0, demand_intermittent[i]), 500.0])

    df = pd.DataFrame(data, columns=['sku', 'descricao', 'categoria', 'data', 'quantidade_vendida', 'preco_unitario'])
    
    # Inserindo alguns "erros" propositais para teste de validação
    df.loc[10, 'quantidade_vendida'] = -50
    df.loc[55, 'quantidade_vendida'] = np.nan
    
    os.makedirs('data', exist_ok=True)
    filepath = 'data/demo_dataset.csv'
    df.to_csv(filepath, index=False)
    print(f"Dataset de demonstração atualizado com sucesso para datas recentes em: {filepath}")

if __name__ == "__main__":
    generate_demo_dataset()