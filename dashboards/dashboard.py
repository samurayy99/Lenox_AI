from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
from flask import Flask
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.arima.model import ARIMA
from plotly.subplots import make_subplots
import logging

def fetch_cryptocurrency_data():
    """Fetch live cryptocurrency data from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin,binancecoin,dogecoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        data = response.json()

        # Log or print the data for debugging purposes
        logging.debug(f"Raw API response: {data}")

        return pd.DataFrame([
            {
                'Symbol': symbol.capitalize(),
                'Price (USD)': details.get('usd', 'N/A'),
                'Volume (24h)': details.get('usd_24h_vol', 'N/A'),
                'Market Cap (USD)': details.get('usd_market_cap', 'N/A'),
                'Change (24h %)': details.get('usd_24h_change', 'N/A')
            }
            for symbol, details in data.items()
        ])
    except requests.RequestException as e:
        logging.error(f"Error fetching cryptocurrency data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame to prevent further errors
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return pd.DataFrame()

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

# Create the main dashboard function
def create_dashboard(server: Flask) -> Flask:
    """Create a comprehensive cryptocurrency analysis dashboard."""
    dash_app = Dash(server=server, routes_pathname_prefix='/dashboard/')
    available_cryptos = ['bitcoin', 'ethereum', 'litecoin', 'binancecoin', 'dogecoin']

    dash_app.layout = html.Div([
        html.H1("CryptoMaster Ultimate Dashboard", style={'textAlign': 'center'}),

        dcc.Tabs(id='tabs', value='tab-market', children=[
            dcc.Tab(label='Market Overview', value='tab-market'),
            dcc.Tab(label='Comparative Analysis', value='tab-comparative'),
            dcc.Tab(label='Historical Data Analysis', value='tab-historical'),
            dcc.Tab(label='Predictive Analytics', value='tab-predictive'),
            dcc.Tab(label='Technical Analysis', value='tab-technical'),
            dcc.Tab(label='Dynamic Visualization', value='tab-dynamic')
        ]),

        html.Div(id='tab-content')
    ])

    @dash_app.callback(
        Output('tab-content', 'children'),
        Input('tabs', 'value')
    )
    def render_tab_content(tab):
        if tab == 'tab-market':
            return html.Div([
                dash_table.DataTable(
                    id='crypto-table',
                    columns=[{'name': col, 'id': col} for col in ['Symbol', 'Price (USD)', 'Volume (24h)', 'Market Cap (USD)', 'Change (24h %)']],
                    page_size=5,
                    style_cell={'textAlign': 'center'}
                ),
                dcc.Graph(id='crypto-bar-chart'),
                dcc.Graph(id='crypto-heatmap'),
                dcc.Interval(id='refresh-market-interval', interval=30*1000, n_intervals=0)
            ])
        elif tab == 'tab-comparative':
            return html.Div([
                dcc.Checklist(
                    id='comparative-crypto-list',
                    options=[{'label': crypto.capitalize(), 'value': crypto} for crypto in available_cryptos],
                    value=['bitcoin', 'ethereum'],
                    inline=True
                ),
                dcc.Graph(id='comparative-line-chart'),
                dcc.Graph(id='correlation-matrix')
            ])
        elif tab == 'tab-historical':
            return html.Div([
                dcc.Dropdown(
                    id='historical-crypto',
                    options=[{'label': crypto.capitalize(), 'value': crypto} for crypto in available_cryptos],
                    value='bitcoin',
                    clearable=False
                ),
                dcc.Graph(id='historical-line-chart'),
                dcc.RangeSlider(
                    id='historical-slider',
                    min=1, max=365, value=[1, 30],
                    marks={1: '1D', 30: '1M', 180: '6M', 365: '1Y'}
                )
            ])
        elif tab == 'tab-predictive':
            return html.Div([
                dcc.Dropdown(
                    id='predictive-crypto',
                    options=[{'label': crypto.capitalize(), 'value': crypto} for crypto in available_cryptos],
                    value='bitcoin',
                    clearable=False
                ),
                dcc.Graph(id='predictive-forecast-chart'),
                dcc.Graph(id='predictive-anomaly-chart')
            ])
        elif tab == 'tab-technical':
            return html.Div([
                dcc.Checklist(
                    id='technical-indicators-list',
                    options=[
                        {'label': 'SMA (20)', 'value': 'SMA_20'},
                        {'label': 'SMA (50)', 'value': 'SMA_50'},
                        {'label': 'RSI', 'value': 'RSI'}
                    ],
                    value=['SMA_20', 'SMA_50', 'RSI'],
                    inline=True
                ),
                dcc.Graph(id='technical-chart')
            ])
        elif tab == 'tab-dynamic':
            return html.Div([
                dcc.Dropdown(
                    id='dynamic-chart-type',
                    options=[
                        {'label': 'Candlestick', 'value': 'candlestick'},
                        {'label': 'Renko Chart', 'value': 'renko'},
                        {'label': 'Kagi Chart', 'value': 'kagi'},
                        {'label': 'Point & Figure', 'value': 'point_figure'}
                    ],
                    value='candlestick',
                    clearable=False
                ),
                dcc.Graph(id='dynamic-chart')
            ])

    # Update market overview charts
    @dash_app.callback(
        Output('crypto-table', 'data'),
        Output('crypto-bar-chart', 'figure'),
        Output('crypto-heatmap', 'figure'),
        Input('refresh-market-interval', 'n_intervals')
    )
    def update_market_data(n_intervals):
        data = fetch_cryptocurrency_data()
        bar_fig = px.bar(data, x='Symbol', y='Price (USD)', title='Market Prices', text='Price (USD)')
        bar_fig.update_layout(yaxis_title='Price (USD)', template='plotly_dark')

        heatmap_data = data.pivot_table(values='Change (24h %)', index='Symbol')
        heatmap_fig = px.imshow(
            heatmap_data,
            aspect='auto',
            color_continuous_scale='RdYlGn',
            title='24h Change Heatmap'
        )
        heatmap_fig.update_layout(yaxis_title='Symbol', template='plotly_dark')

        return data.to_dict('records'), bar_fig, heatmap_fig

    # Comparative analysis line chart and correlation matrix
    @dash_app.callback(
        Output('comparative-line-chart', 'figure'),
        Output('correlation-matrix', 'figure'),
        Input('comparative-crypto-list', 'value')
    )
    def update_comparative_line_chart_and_corr(selected_cryptos):
        data = fetch_historical_data(selected_cryptos)
        fig = go.Figure()
        for symbol, df in data.items():
            normalized_price = df['Price'] / df['Price'].iloc[0] * 100
            fig.add_trace(go.Scatter(x=df['Date'], y=normalized_price, mode='lines', name=symbol.capitalize()))
        fig.update_layout(title='Normalized Comparative Cryptocurrency Analysis', xaxis_title='Date', yaxis_title='Normalized Price (%)', template='plotly_dark')

        correlation_matrix = calculate_correlation(selected_cryptos)
        corr_fig = px.imshow(correlation_matrix, text_auto=True, title='Cryptocurrency Correlation Matrix', color_continuous_scale='RdBu', template='plotly_dark')

        return fig, corr_fig

    # Historical price chart with technical indicators
    @dash_app.callback(
        Output('historical-line-chart', 'figure'),
        Input('historical-crypto', 'value'),
        Input('historical-slider', 'value')
    )
    def update_historical_line_chart(crypto, days):
        data = fetch_historical_data([crypto], days=max(days))[crypto]
        data['SMA_20'] = data['Price'].rolling(window=20).mean()
        data['SMA_50'] = data['Price'].rolling(window=50).mean()
        data['RSI'] = calculate_rsi(data['Price'], period=14)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Price'], mode='lines', name=f'{crypto.capitalize()} Price'))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['SMA_20'], mode='lines', name='SMA 20'))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['SMA_50'], mode='lines', name='SMA 50'))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['RSI'], mode='lines', name='RSI', yaxis='y2'))
        fig.update_layout(
            title=f'{crypto.capitalize()} Historical Price Analysis with Moving Averages and RSI',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            yaxis2=dict(title='RSI', overlaying='y', side='right'),
            template='plotly_dark'
        )
        return fig

    # Predictive analytics chart using ARIMA forecasting and anomaly detection
    @dash_app.callback(
        Output('predictive-forecast-chart', 'figure'),
        Output('predictive-anomaly-chart', 'figure'),
        Input('predictive-crypto', 'value')
    )
    def update_predictive_forecast_and_anomaly(crypto):
        data = fetch_historical_data([crypto], days=180)[crypto]
        forecast_prices = arima_forecast(data['Price'])
        forecast_fig = go.Figure()
        forecast_fig.add_trace(go.Scatter(x=data['Date'], y=data['Price'], mode='lines', name=f'{crypto.capitalize()} Price'))
        future_dates = pd.date_range(start=data['Date'].iloc[-1], periods=len(forecast_prices) + 1, closed='right').date
        forecast_fig.add_trace(go.Scatter(x=future_dates, y=forecast_prices, mode='lines', name='ARIMA Forecast'))
        forecast_fig.update_layout(title=f'{crypto.capitalize()} Price Forecast (ARIMA)', xaxis_title='Date', yaxis_title='Price (USD)', template='plotly_dark')

        # Anomaly detection (placeholder for custom anomaly detection model)
        anomaly_fig = go.Figure()
        anomaly_fig.update_layout(title=f'{crypto.capitalize()} Anomaly Detection', template='plotly_dark')

        return forecast_fig, anomaly_fig

    # Technical indicators chart with multiple indicator options
    @dash_app.callback(
        Output('technical-chart', 'figure'),
        Input('technical-indicators-list', 'value')
    )
    def update_technical_chart(indicators):
        data = fetch_historical_data(['bitcoin'], days=180)['bitcoin']
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=data['Date'], y=data['Price'], mode='lines', name='Bitcoin Price'))

        if 'SMA_20' in indicators:
            data['SMA_20'] = data['Price'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=data['Date'], y=data['SMA_20'], mode='lines', name='SMA 20'))

        if 'SMA_50' in indicators:
            data['SMA_50'] = data['Price'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(x=data['Date'], y=data['SMA_50'], mode='lines', name='SMA 50'))

        if 'RSI' in indicators:
            data['RSI'] = calculate_rsi(data['Price'], period=14)
            fig.add_trace(go.Scatter(x=data['Date'], y=data['RSI'], mode='lines', name='RSI', yaxis='y2'))

        fig.update_layout(
            title='Bitcoin Price Analysis with Selected Technical Indicators',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            yaxis2=dict(title='RSI', overlaying='y', side='right'),
            template='plotly_dark'
        )
        return fig

    # Dynamic chart visualization based on selected type
    @dash_app.callback(
        Output('dynamic-chart', 'figure'),
        Input('dynamic-chart-type', 'value')
    )
    def update_dynamic_chart(chart_type):
        data = fetch_cryptocurrency_data()
        if chart_type == 'candlestick':
            fig = make_subplots(rows=1, cols=1)
            fig.append_trace(
                go.Candlestick(
                    x=data['Symbol'],
                    open=[12, 15, 20, 18, 22],
                    high=[15, 18, 25, 22, 28],
                    low=[10, 12, 18, 16, 20],
                    close=[13, 17, 23, 20, 25]
                ), row=1, col=1
            )
            fig.update_layout(title='Candlestick Chart')
        elif chart_type == 'renko':
            fig = px.line(data, x='Symbol', y='Price (USD)', title='Renko Chart')
        elif chart_type == 'kagi':
            fig = px.line(data, x='Symbol', y='Price (USD)', title='Kagi Chart')
        elif chart_type == 'point_figure':
            fig = px.line(data, x='Symbol', y='Price (USD)', title='Point & Figure Chart')
        else:
            fig = px.bar(data, x='Symbol', y='Price (USD)', title='Bar Chart', text='Price (USD)')

        fig.update_layout(yaxis_title='Price (USD)', template='plotly_dark')
        return fig

    return dash_app.server