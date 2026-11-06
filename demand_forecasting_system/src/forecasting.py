import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings("ignore")

class ForecastEngine:
    @staticmethod
    def naive(series, h): 
        return series.shift(1).fillna(series.iloc[0]), np.repeat(series.iloc[-1], h)

    @staticmethod
    def simple_moving_average(series, h, window=3):
        if len(series) < window: return None, None
        # CORREÇÃO: Utilizando .bfill() direto ao invés de fillna(method='bfill')
        fitted = series.rolling(window=window).mean().shift(1).bfill()
        return fitted, np.repeat(fitted.iloc[-1], h)

    @staticmethod
    def simple_exponential_smoothing(series, h, alpha=0.2):
        model = SimpleExpSmoothing(series, initialization_method="estimated").fit(smoothing_level=alpha, optimized=False)
        return model.fittedvalues, model.forecast(h).values

    @staticmethod
    def holt(series, h):
        model = ExponentialSmoothing(series, trend='add', initialization_method="estimated").fit()
        return model.fittedvalues, model.forecast(h).values

    @staticmethod
    def holt_winters(series, h, m=12):
        try:
            model = ExponentialSmoothing(series, trend='add', seasonal='add', seasonal_periods=m, initialization_method="estimated").fit()
            return model.fittedvalues, model.forecast(h).values
        except: return None, None

    @staticmethod
    def linear_regression(series, h):
        X = np.arange(len(series)).reshape(-1, 1)
        reg = LinearRegression().fit(X, series.values)
        X_fut = np.arange(len(series), len(series) + h).reshape(-1, 1)
        return np.maximum(0, pd.Series(reg.predict(X), index=series.index)), np.maximum(0, reg.predict(X_fut))

    @staticmethod
    def croston(series, h):
        demanda = series.values
        n = len(demanda)
        level, period, forecast = np.zeros(n), np.zeros(n), np.zeros(n)
        non_zero = np.where(demanda > 0)[0]
        if len(non_zero) == 0: return series, np.zeros(h)
        alpha, q = 0.1, 1
        level[0], period[0] = demanda[non_zero[0]], 1 if non_zero[0] == 0 else non_zero[0]
        forecast[0] = level[0] / period[0]
        for t in range(1, n):
            if demanda[t] > 0:
                level[t], period[t], q = alpha * demanda[t] + (1 - alpha) * level[t-1], alpha * q + (1 - alpha) * period[t-1], 1
            else:
                level[t], period[t], q = level[t-1], period[t-1], q + 1
            forecast[t] = level[t] / period[t]
        return pd.Series(forecast, index=series.index), np.repeat(level[-1] / period[-1] if period[-1] > 0 else 0, h)

    @classmethod
    def run_all(cls, series, h, m=12):
        results = {}
        for nome, func in [('Naive', cls.naive), ('Média Móvel', lambda s,h: cls.simple_moving_average(s,h)), ('SES', cls.simple_exponential_smoothing), ('Holt', cls.holt), ('Holt-Winters', lambda s,h: cls.holt_winters(s,h,m)), ('Regressão', cls.linear_regression), ('Croston', cls.croston)]:
            fit, fcast = func(series, h)
            if fcast is not None: results[nome] = (fit, fcast)
        return results
