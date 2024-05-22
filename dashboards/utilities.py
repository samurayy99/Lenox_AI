import time
import requests
import pandas as pd
import logging
from statsmodels.tsa.arima.model import ARIMA

def fetch_cryptocurrency_data(retries=3, delay=5):
    """Fetch live cryptocurrency data from CoinGecko with retries and delay on rate limit errors."""
    url = ("https://api.coingecko.com/api/v3/simple/price"
           "?ids=bitcoin,ethereum,litecoin,binancecoin,dogecoin"
           "&vs_currencies=usd"
           "&include_market_cap=true"
           "&include_24hr_vol=true"
           "&include_24hr_change=true")
    
    for attempt in range(retries):
        response = requests.get(url)
        
        # Check for HTTP 429 (Too Many Requests)
        if response.status_code == 429:
            print(f"Rate limit reached. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
            continue
        
        # If the request succeeds, parse the data
        if response.ok:
            data = response.json()
            return pd.DataFrame([
                {
                    'Symbol': symbol.capitalize(),
                    'Price (USD)': data[symbol]['usd'],
                    'Volume (24h)': data[symbol]['usd_24h_vol'],
                    'Market Cap (USD)': data[symbol]['usd_market_cap'],
                    'Change (24h %)': data[symbol]['usd_24h_change']
                }
                for symbol in data
            ])
    
    # If all retries fail, return an empty DataFrame or raise an error
    print("Unable to fetch cryptocurrency data after retries.")
    return pd.DataFrame(columns=['Symbol', 'Price (USD)', 'Volume (24h)', 'Market Cap (USD)', 'Change (24h %)'])

def fetch_historical_data(symbols, days=30):
    """Fetch historical price data for a list of cryptocurrencies over a specified number of days."""
    historical_data = {}
    for symbol in symbols:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days={days}"
            response = requests.get(url)
            response.raise_for_status()  # This will raise an exception for non-200 responses
            data = response.json()
            if 'prices' in data:
                prices = pd.DataFrame(data['prices'], columns=['Timestamp', 'Price'])
                prices['Date'] = pd.to_datetime(prices['Timestamp'], unit='ms').dt.date
                historical_data[symbol] = prices
        except requests.RequestException as e:
            logging.error(f"Failed to fetch historical data for {symbol}: {str(e)}")
            # Return an empty DataFrame with the same structure to avoid KeyError
            historical_data[symbol] = pd.DataFrame(columns=['Timestamp', 'Price', 'Date'])
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