import numpy as np

class ScenarioBuilder:
    @staticmethod
    def aplicar_simulacao_linear(forecast, variacao_pct): return forecast * (1 + (variacao_pct / 100.0))
    @staticmethod
    def aplicar_simulacao_promocao(forecast, indices, variacao_pct):
        cenario = np.copy(forecast)
        for idx in indices:
            if idx < len(cenario): cenario[idx] *= (1 + (variacao_pct / 100.0))
        return cenario
