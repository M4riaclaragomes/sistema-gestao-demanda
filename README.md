# Demanda+ · Sistema de Gestão de Demanda

Aplicação web em **Streamlit** para previsão e gestão de demanda, voltada a processos de **S&OP** e **CPFR**.
Do histórico de vendas ao plano consensado: importe a base, entenda o comportamento de cada produto,
gere previsões com 7 modelos estatísticos, valide com backtesting e alinhe o plano com parceiros.

🔗 **App online:** https://sistema-gestao-demanda-heqpkpiemd3dqb8df4mm2t.streamlit.app/

---

## Funcionalidades

| Seção | Módulo | O que faz |
|---|---|---|
| Início | **Visão geral** | Onboarding, KPIs do portfólio e perfil/tendência de cada SKU |
| Dados | **Importação de dados** | Upload CSV/Excel, mapeamento de colunas, auditoria de qualidade e modelo CSV |
| Dados | **Análise histórica** | Indicadores, classificação do perfil de demanda, média móvel, tendência, sazonalidade e distribuição |
| Planejamento | **Previsão de demanda** | 7 modelos, recomendação automática via backtesting, intervalos de confiança 80/95% e exportação |
| Planejamento | **Comparação de modelos** | Teste cego (out-of-sample) com ranking por WAPE, MAE, RMSE, MAPE, viés e tracking signal |
| Planejamento | **Cenários e CPFR** | Simulação de choques e promoções em tempo real; plano de consenso editável com alertas de divergência |
| Gestão | **Dashboard gerencial** | Filtros, variação 30 dias/12 meses, ranking, participação, evolução mensal e heatmap |
| Gestão | **Relatórios e laudos** | Laudo gerencial automático, visão consolidada do portfólio e exportação Excel/CSV/TXT |

### Modelos de previsão

| Modelo | Indicado para |
|---|---|
| Naive | Linha de base de comparação |
| Média Móvel | Demanda estável |
| SES (Suavização Exponencial Simples) | Demanda sem tendência, com ruído |
| Holt | Demanda com tendência |
| Holt-Winters | Tendência + sazonalidade |
| Regressão Linear | Tendência de longo prazo |
| Croston | Demanda intermitente (muitos períodos zerados) |

### Perfis de demanda identificados

**Estável**, **Crescente**, **Decrescente**, **Sazonal/Variável**, **Irregular** e **Intermitente** — calculados a partir
do coeficiente de variação, do crescimento entre metades da série e do percentual de períodos sem venda.

---

## Formato dos dados

Uma linha por **produto × data**. Colunas obrigatórias (nomes diferentes podem ser mapeados na importação):

| sku | data | quantidade_vendida |
|---|---|---|
| PROD_A | 2025-01-01 | 120 |
| PROD_A | 2025-01-02 | 98 |
| PROD_B | 2025-01-01 | 40 |

Tratamento automático: valores nulos e negativos viram 0, datas inválidas são descartadas e duplicidades são sinalizadas.
Uma base de demonstração com 5 produtos e 4 anos de histórico diário está em `demand_forecasting_system/data/demo_dataset.csv`.

---

## Como rodar localmente

Requer **Python 3.10+**.

```bash
git clone https://github.com/M4riaclaragomes/sistema-gestao-demanda.git
cd sistema-gestao-demanda
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux / macOS
pip install -r demand_forecasting_system/requirements.txt
streamlit run demand_forecasting_system/app.py
```

Acesse http://localhost:8501 e clique em **Carregar demonstração** na barra lateral.

---

## Estrutura do projeto

```
.
├── .streamlit/config.toml              # tema (usado quando executado a partir da raiz)
└── demand_forecasting_system/
    ├── app.py                          # ponto de entrada: navegação, barra lateral e tema
    ├── requirements.txt
    ├── .streamlit/config.toml          # tema: cores, fonte Inter, barra lateral escura
    ├── assets/                         # logo e ícone
    ├── data/demo_dataset.csv           # base de demonstração
    ├── generate_demo_data.py           # gerador de dados sintéticos
    ├── src/
    │   ├── ui.py                       # componentes visuais, CSS e template dos gráficos
    │   ├── services.py                 # camada com cache: agregação, modelos, backtesting, exportação
    │   ├── forecasting.py              # motor estatístico (7 modelos)
    │   ├── evaluator.py                # métricas de erro
    │   ├── eda.py                      # indicadores e classificação de perfil
    │   ├── data_processor.py           # leitura, validação e tratamento
    │   └── scenario_builder.py         # simulação de cenários
    └── views/                          # uma página por módulo (0_inicio … 7_relatorios)
```

---

## Deploy

Publicado no **Streamlit Community Cloud** com arquivo principal `demand_forecasting_system/app.py`.
Cada push na branch `main` atualiza o app automaticamente.

## Tecnologias

Streamlit · pandas · NumPy · Plotly · statsmodels · scikit-learn · openpyxl
