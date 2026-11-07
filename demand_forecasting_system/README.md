# Demanda+ · Sistema de Gestão de Demanda

Aplicação Streamlit para previsão e gestão de demanda (S&OP / CPFR), redesenhada a partir de
[M4riaclaragomes/sistema-gestao-demanda](https://github.com/M4riaclaragomes/sistema-gestao-demanda/tree/main/demand_forecasting_system).

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Acesse http://localhost:8501 e clique em **Carregar demonstração** para explorar com dados de exemplo.

## Módulos

| Seção | Página | O que faz |
|---|---|---|
| Início | Visão geral | Onboarding, KPIs do portfólio e tabela com perfil e tendência de cada SKU |
| Dados | Importação | Upload CSV/Excel, mapeamento de colunas, auditoria de qualidade, modelo CSV |
| Dados | Análise histórica | KPIs, perfil de demanda, média móvel/tendência, mapa de calor sazonal, distribuição, comparação de SKUs |
| Planejamento | Previsão | 7 modelos, recomendação via backtesting, intervalo de confiança 80/95%, exportação Excel/CSV |
| Planejamento | Comparação de modelos | Teste cego out-of-sample, ranking por WAPE, MAE/RMSE/MAPE/Viés/Tracking Signal |
| Planejamento | Cenários e CPFR | Choque de demanda + promoções em tempo real; plano de consenso editável com alertas |
| Gestão | Dashboard gerencial | Filtros, KPIs com variação 30d/12m, ranking, participação, evolução e heatmap |
| Gestão | Relatórios e laudos | Laudo automático, visão consolidada do portfólio e exportação |

## Estrutura

```
app.py                 # navegação (st.navigation), sidebar e tema
.streamlit/config.toml # tema (cores, fonte Inter, sidebar escura)
src/ui.py              # componentes visuais, CSS e template Plotly
src/services.py        # camada com cache: agregação, modelos, backtesting, exportação
src/forecasting.py     # motor estatístico (original)
src/eda.py, evaluator.py, data_processor.py, scenario_builder.py
views/                 # uma página por módulo
data/demo_dataset.csv  # base de demonstração
```
