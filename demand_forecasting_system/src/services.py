"""Serviços de dados e modelagem com cache (camada entre o motor estatístico e as telas)."""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.data_processor import DataProcessor
from src.eda import ExploratoryDataAnalysis
from src.evaluator import ForecastEvaluator
from src.forecasting import ForecastEngine

ROOT = Path(__file__).resolve().parent.parent
DEMO_PATH = ROOT / "data" / "demo_dataset.csv"

FREQS = {"Diária": "D", "Semanal": "W", "Mensal": "ME"}
SEASON = {"D": 7, "W": 52, "ME": 12}
UNIT = {"D": "dias", "W": "semanas", "ME": "meses"}
UNIT_SING = {"D": "dia", "W": "semana", "ME": "mês"}
DEFAULT_H = {"D": 30, "W": 12, "ME": 6}
MAX_H = {"D": 180, "W": 52, "ME": 24}

MODEL_INFO = {
    "Naive": "Repete o último valor observado. Linha de base para comparar os demais.",
    "Média Móvel": "Média das últimas 3 observações. Suaviza ruído; ideal para demanda estável.",
    "SES": "Suavização exponencial simples: pondera mais os dados recentes.",
    "Holt": "Suavização com tendência — capta crescimento ou queda consistente.",
    "Holt-Winters": "Tendência + sazonalidade — capta ciclos (ex.: verão, fim de ano).",
    "Regressão": "Reta de tendência ajustada sobre todo o histórico.",
    "Croston": "Específico para demanda intermitente (muitos períodos zerados).",
}


# --------------------------------------------------------------------------------------
# Carga de dados
# --------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def read_demo_raw() -> pd.DataFrame:
    df = pd.read_csv(DEMO_PATH)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    return df


def set_dataset(df: pd.DataFrame, origem: str) -> None:
    st.session_state["df_dados"] = df
    st.session_state["origem"] = origem


def load_demo_into_state() -> None:
    df = DataProcessor().aplicar_tratamento_padrao(read_demo_raw())
    set_dataset(df, "Base de demonstração")
    st.toast("Base de demonstração carregada", icon=":material/check_circle:")


def clear_dataset() -> None:
    for k in ("df_dados", "origem"):
        st.session_state.pop(k, None)


def dataset_summary(df: pd.DataFrame) -> dict:
    return {
        "registros": len(df),
        "skus": df["sku"].nunique(),
        "inicio": df["data"].min(),
        "fim": df["data"].max(),
        "volume": float(df["quantidade_vendida"].sum()),
    }


# --------------------------------------------------------------------------------------
# Séries
# --------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def series_for(df: pd.DataFrame, sku: str, freq: str) -> pd.Series:
    raw = df.loc[df["sku"] == sku].set_index("data")["quantidade_vendida"].astype(float)
    s = raw.resample(freq).sum()
    # Descarta períodos parciais nas pontas (ex.: mês que termina no dia 27) para não distorcer modelos.
    if freq != "D" and len(s) > 2:
        first, last = raw.index.min(), raw.index.max()
        if freq == "W":
            if s.index[-1] > last.normalize():
                s = s.iloc[:-1]
            if first.normalize() > s.index[0] - pd.Timedelta(days=6):
                s = s.iloc[1:]
        elif freq == "ME":
            if s.index[-1].normalize() > last.normalize():
                s = s.iloc[:-1]
            if first.day > 1:
                s = s.iloc[1:]
    s.name = "quantidade_vendida"
    return s


@st.cache_data(show_spinner=False)
def profile(df: pd.DataFrame, sku: str, freq: str = "W") -> tuple[dict | None, str, str]:
    s = series_for(df, sku, freq)
    eda = ExploratoryDataAnalysis(df)
    ind = eda.calcular_indicadores(s.reset_index())
    classe, motivo = eda.classificar_comportamento(ind)
    return ind, classe, motivo


@st.cache_data(show_spinner=False)
def portfolio_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sku in sorted(df["sku"].unique()):
        ind, classe, _ = profile(df, sku, "W")
        weekly = series_for(df, sku, "W")
        rows.append(
            {
                "SKU": sku,
                "Perfil": classe,
                "Volume total": ind["total"] if ind else 0,
                "Média semanal": ind["media"] if ind else 0,
                "CV": ind["cv"] if ind else 0,
                "Crescimento (%)": ind["crescimento_pct"] if ind else 0,
                "Tendência (52 sem.)": weekly.tail(52).round(0).tolist(),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Modelagem
# --------------------------------------------------------------------------------------
def _clean(fit, fcast, index) -> tuple[pd.Series | None, np.ndarray]:
    fc = np.maximum(0, np.asarray(fcast, dtype=float))
    fit_s = None
    if fit is not None:
        fit_s = pd.Series(np.asarray(fit, dtype=float), index=index)
    return fit_s, fc


@st.cache_data(show_spinner=False)
def run_models(series: pd.Series, h: int, m: int) -> dict:
    """Ajusta todos os modelos e retorna previsão + desvio dos resíduos (para intervalos)."""
    out = {}
    for nome, (fit, fcast) in ForecastEngine.run_all(series, h, m=m).items():
        fit_s, fc = _clean(fit, fcast, series.index)
        if fit_s is not None:
            resid = (series - fit_s).iloc[1:]
            sigma = float(np.nanstd(resid)) if len(resid) > 1 else 0.0
        else:
            sigma = float(series.std())
        out[nome] = {"fit": fit_s, "forecast": fc, "sigma": sigma}
    return out


@st.cache_data(show_spinner=False)
def backtest(series: pd.Series, h: int, m: int) -> tuple[pd.DataFrame, dict, pd.Series, pd.Series]:
    """Teste cego: treina com o passado e mede o erro nos últimos *h* períodos."""
    train, test = series.iloc[:-h], series.iloc[-h:]
    res = ForecastEngine.run_all(train, h, m=m)
    rows, fcasts = [], {}
    for nome, (fit, fcast) in res.items():
        if fcast is None or len(fcast) != len(test):
            continue
        _, fc = _clean(fit, fcast, train.index)
        met = ForecastEvaluator.calculate_metrics(test.values, fc)
        fcasts[nome] = fc
        rows.append({"Modelo": nome, **met})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Acurácia (%)"] = (100 - df["WAPE (%)"]).clip(lower=0)
        df = df.sort_values("WAPE (%)", na_position="last").reset_index(drop=True)
        df.insert(0, "Posição", range(1, len(df) + 1))
    return df, fcasts, train, test


def future_index(series: pd.Series, h: int, freq: str) -> pd.DatetimeIndex:
    return pd.date_range(start=series.index[-1], periods=h + 1, freq=freq)[1:]


def best_model(series: pd.Series, freq: str, h: int | None = None) -> tuple[str | None, pd.DataFrame]:
    m = SEASON[freq]
    n = len(series)
    h_bt = h or min(max(int(n * 0.2), 3), 12)
    h_bt = min(h_bt, max(n - 4, 1))
    if n < 6:
        return None, pd.DataFrame()
    metrics, *_ = backtest(series, h_bt, m)
    if metrics.empty:
        return None, metrics
    return str(metrics.iloc[0]["Modelo"]), metrics


# --------------------------------------------------------------------------------------
# Exportação
# --------------------------------------------------------------------------------------
def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, d in sheets.items():
            d.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


def template_csv() -> bytes:
    exemplo = pd.DataFrame(
        {
            "sku": ["PROD_A", "PROD_A", "PROD_B"],
            "data": ["2025-01-01", "2025-01-02", "2025-01-01"],
            "quantidade_vendida": [120, 98, 40],
        }
    )
    return exemplo.to_csv(index=False).encode("utf-8")
