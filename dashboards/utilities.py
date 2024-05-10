import requests
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def fetch_cryptocurrency_data():
    """Fetch live cryptocurrency data from CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin,binancecoin,dogecoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame([
            {
                'Symbol': symbol.capitalize(),
                'Price (USD)': data_info['usd'],
                'Volume (24h)': data_info['usd_24h_vol'],
                'Market Cap (USD)': data_info['usd_market_cap'],
                'Change (24h %)': data_info['usd_24h_change']
            }
            for symbol, data_info in data.items()
        ])
    except requests.RequestException as e:
        print(f"Error fetching cryptocurrency data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def fetch_historical_data(symbols, days=30):
    """Fetch historical price data for a list of cryptocurrencies over a specified number of days."""
    historical_data = {}
    for symbol in symbols:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days={days}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if 'prices' in data:
                historical_data[symbol] = pd.DataFrame(data['prices'], columns=['Timestamp', 'Price'])
                historical_data[symbol]['Date'] = pd.to_datetime(historical_data[symbol]['Timestamp'], unit='ms').dt.date
        except requests.RequestException as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            historical_data[symbol] = pd.DataFrame()
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
    """Predict future prices using the ARIMA model."""
    try:
        model = ARIMA(prices, order=(5, 1, 0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=steps)
        return forecast
    except Exception as e:
        print(f"Error in ARIMA forecasting: {e}")
        return pd.Series()  # Return an empty series on error

def calculate_correlation(cryptos, days=30):
    """Fetch historical data and calculate the correlation between selected cryptocurrencies."""
    historical_data = fetch_historical_data(cryptos, days)
    prices_df = pd.DataFrame({symbol: df['Price'] for symbol, df in historical_data.items() if not df.empty})
    return prices_df.corr()
