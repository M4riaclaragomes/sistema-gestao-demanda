import numpy as np

class ForecastEvaluator:
    @staticmethod
    def calculate_metrics(y_true, y_pred):
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        errors = y_true - y_pred
        mae = np.mean(np.abs(errors))
        mse = np.mean(errors ** 2)
        non_zero = y_true != 0
        mape = np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100 if np.any(non_zero) else np.nan
        sum_y = np.sum(y_true)
        wape = (np.sum(np.abs(errors)) / sum_y) * 100 if sum_y > 0 else np.nan
        return {'MAE': mae, 'MSE': mse, 'RMSE': np.sqrt(mse), 'MAPE (%)': mape, 'WAPE (%)': wape, 'Viés (Bias)': np.sum(y_pred - y_true), 'Tracking Signal': np.sum(errors) / mae if mae > 0 else 0}