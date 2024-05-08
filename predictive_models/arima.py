from statsmodels.tsa.arima.model import ARIMA  # Correct import statement for ARIMA
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd

def evaluate_arima():
    """Evaluate ARIMA model predictions for a dataset."""
    data = [112, 118, 132, 129, 121, 135, 148, 148, 136, 119, 104, 118, 115, 126, 141, 135, 125, 149]
    model = ARIMA(data, order=(5, 1, 0))
    model_fit = model.fit()
    predictions = model_fit.forecast(steps=5)
    targets = data[-5:]
    return predictions, targets

class MyARIMA:
    sc_in = MinMaxScaler(feature_range=(0, 1))
    sc_out = MinMaxScaler(feature_range=(0, 1))

    def __init__(self, args):
        self.train_size = -1
        self.test_size = -1
        self.order = tuple(map(int, args.order.split(', ')))

    def fit(self, data_x):
        data_x = np.array(data_x)
        train_x = data_x[:, 1:-1]
        train_y = data_x[:, -1]
        self.train_size = train_x.shape[0]
        train_x = self.sc_in.fit_transform(train_x)
        train_y = train_y.reshape(-1, 1)
        train_y = self.sc_out.fit_transform(train_y)
        train_x = np.array(train_x, dtype=float)
        train_y = np.array(train_y, dtype=float)
        self.model = ARIMA(train_y, exog=train_x, order=self.order)
        self.result = self.model.fit()

    def predict(self, test_x):
        test_x = np.array(test_x.iloc[:, 1:], dtype=float)
        test_x = self.sc_in.transform(test_x)
        self.test_size = test_x.shape[0]
        pred_y = self.result.predict(start=self.train_size, end=self.train_size + self.test_size - 1, exog=test_x)
        pred_y = pred_y.reshape(-1, 1)
        pred_y = self.sc_out.inverse_transform(pred_y)
        return pred_y
