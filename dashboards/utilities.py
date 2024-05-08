import requests
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def fetch_cryptocurrency_data():
    """Fetch live cryptocurrency data from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin,binancecoin,dogecoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
    response = requests.get(url).json()
    return pd.DataFrame([
        {
            'Symbol': symbol.capitalize(),
            'Price (USD)': data['usd'],
            'Volume (24h)': data['usd_24h_vol'],
            'Market Cap (USD)': data['usd_market_cap'],
            'Change (24h %)': data['usd_24h_change']
        }
        for symbol, data in response.items()
    ])

def fetch_historical_data(symbols, days=30):
    """Fetch historical price data for a list of cryptocurrencies over a specified number of days."""
    historical_data = {}
    for symbol in symbols:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url).json()
        if 'prices' in response:
            historical_data[symbol] = pd.DataFrame(response['prices'], columns=['Timestamp', 'Price'])
            historical_data[symbol]['Date'] = pd.to_datetime(historical_data[symbol]['Timestamp'], unit='ms').dt.date
    return historical_data

def calculate_rsi(prices, period=14):
    """Calculate the Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def arima_forecast(prices, steps=30):
    """Predict future prices using ARIMA model."""
    model = ARIMA(prices, order=(5, 1, 0))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=steps)
    return forecast

def calculate_correlation(cryptos, days=30):
    """Fetch historical data and calculate the correlation between selected cryptocurrencies."""
    historical_data = fetch_historical_data(cryptos, days)
    prices_df = pd.DataFrame({symbol: df['Price'] for symbol, df in historical_data.items()})
    return prices_df.corr()
