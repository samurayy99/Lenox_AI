from dash import Input, Output, dash_table, dcc, html
from typing import Tuple
import pandas as pd
import logging
import plotly.express as px
import plotly.graph_objects as go
from dashboards.utilities import (
    fetch_cryptocurrency_data,
    fetch_historical_data,
    calculate_rsi,
    arima_forecast,
    calculate_correlation
)

def register_callbacks(dash_app):
    """Register all callbacks for the main dashboard."""
    @dash_app.callback(
        Output('main-tab-content', 'children'),  # Unique output ID
        Input('main-tabs', 'value')  # Tabs specific to the main dashboard
    )
    def render_main_tab_content(tab_value):
        """Render content based on the selected tab."""
        if tab_value == 'tab-market':
            return html.Div([
                dash_table.DataTable(
                    id='market-table',  # Unique ID for market table
                    columns=[{'name': col, 'id': col} for col in ['Symbol', 'Price (USD)', 'Volume (24h)', 'Market Cap (USD)', 'Change (24h %)']],
                    page_size=5,
                    style_cell={'textAlign': 'center'}
                ),
                dcc.Graph(id='market-bar-chart'),  # Unique ID for bar chart
                dcc.Graph(id='market-heatmap')  # Unique ID for heatmap
            ])
        elif tab_value == 'tab-comparative':
            return html.Div([
                dcc.Checklist(
                    id='comparative-crypto-list',
                    options=[{'label': crypto.capitalize(), 'value': crypto} for crypto in ['bitcoin', 'ethereum', 'litecoin', 'binancecoin', 'dogecoin']],
                    value=['bitcoin', 'ethereum'],
                    inline=True
                ),
                dcc.Graph(id='comparative-line-chart'),
                dcc.Graph(id='correlation-matrix')
            ])
        elif tab_value == 'tab-historical':
            return html.Div([
                dcc.Dropdown(
                    id='historical-crypto',
                    options=[{'label': crypto.capitalize(), 'value': crypto} for crypto in ['bitcoin', 'ethereum', 'litecoin', 'binancecoin', 'dogecoin']],
                    value='bitcoin',
                    clearable=False
                ),
                dcc.Graph(id='historical-line-chart'),
                dcc.RangeSlider(
                    id='historical-slider',
                    min=1, max=365,
                    value=[1, 30],
                    marks={1: '1D', 30: '1M', 180: '6M', 365: '1Y'}
                )
            ])
        elif tab_value == 'tab-predictive':
            return html.Div([
                dcc.Dropdown(
                    id='predictive-crypto',
                    options=[{'label': crypto.capitalize(), 'value': crypto} for crypto in ['bitcoin', 'ethereum', 'litecoin', 'binancecoin', 'dogecoin']],
                    value='bitcoin',
                    clearable=False
                ),
                dcc.Graph(id='predictive-forecast-chart'),
                dcc.Graph(id='predictive-anomaly-chart')
            ])
        elif tab_value == 'tab-technical':
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
        elif tab_value == 'tab-dynamic':
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
        else:
            return html.Div('No valid tab selected.')

    @dash_app.callback(
        Output('market-table', 'data'),
        Output('market-bar-chart', 'figure'),
        Output('market-heatmap', 'figure'),
        Input('refresh-market-interval', 'n_intervals')
    )
    def update_market_data(n_intervals):
        """Update market overview charts."""
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

    @dash_app.callback(
        Output('comparative-line-chart', 'figure'),
        Output('correlation-matrix', 'figure'),
        Input('comparative-crypto-list', 'value')
    )
    def update_comparative_line_chart_and_corr(selected_cryptos):
        """Update comparative analysis charts."""
        data = fetch_historical_data(selected_cryptos)
        fig = go.Figure()
        for symbol, df in data.items():
            normalized_price = df['Price'] / df['Price'].iloc[0] * 100
            fig.add_trace(go.Scatter(x=df['Date'], y=normalized_price, mode='lines', name=symbol.capitalize()))
        fig.update_layout(title='Normalized Comparative Cryptocurrency Analysis', xaxis_title='Date', yaxis_title='Normalized Price (%)', template='plotly_dark')

        correlation_matrix = calculate_correlation(selected_cryptos)
        corr_fig = px.imshow(correlation_matrix, text_auto=True, title='Cryptocurrency Correlation Matrix', color_continuous_scale='RdBu', template='plotly_dark')

        return fig, corr_fig

    @dash_app.callback(
        Output('historical-line-chart', 'figure'),
        Input('historical-crypto', 'value'),
        Input('historical-slider', 'value')
    )
    def update_historical_line_chart(crypto, days):
        """Update historical price chart with technical indicators."""
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

    @dash_app.callback(
        Output('predictive-forecast-chart', 'figure'),
        Output('predictive-anomaly-chart', 'figure'),
        Input('predictive-crypto', 'value')
    )
    def update_predictive_forecast_and_anomaly(crypto: str) -> Tuple[go.Figure, go.Figure]:
        """Construct the forecast and anomaly charts."""
        logging.info(f"Selected crypto: {crypto}")
        data = fetch_historical_data([crypto], days=180)[crypto]
        logging.info(f"Historical data for {crypto}: {data}")

        forecast_prices = arima_forecast(data["Price"])
        logging.info(f"ARIMA forecast data: {forecast_prices}")

        forecast_fig = go.Figure()
        forecast_fig.add_trace(go.Scatter(x=data["Date"], y=data["Price"], mode="lines", name=f"{crypto.capitalize()} Price"))
        future_dates = pd.date_range(start=data["Date"].iloc[-1], periods=len(forecast_prices) + 1, closed="right").date
        forecast_fig.add_trace(go.Scatter(x=future_dates, y=forecast_prices, mode="lines", name="ARIMA Forecast"))
        forecast_fig.update_layout(
            title=f"{crypto.capitalize()} Price Forecast (ARIMA)", xaxis_title="Date", yaxis_title="Price (USD)", template="plotly_dark"
        )

        anomaly_fig = go.Figure()  # Adjust with actual anomaly data
        anomaly_fig.update_layout(title=f"{crypto.capitalize()} Anomaly Detection", template="plotly_dark")

        return forecast_fig, anomaly_fig

    @dash_app.callback(
        Output('technical-chart', 'figure'),
        Input('technical-indicators-list', 'value')
    )
    def update_technical_chart(indicators):
        """Update the technical analysis chart with selected indicators."""
        data = fetch_historical_data(['bitcoin'], days=180)['bitcoin']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Price'], mode='lines', name='Bitcoin Price'))

        if 'SMA_20' in indicators:
            data['SMA_20'] = data['Price'].rolling(window=20).mean()
            fig.addentiful_trace(go.Scatter(x=data['Date'], y=data['SMA_20'], mode='lines', name='SMA 20'))

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

    @dash_app.callback(
        Output('dynamic-chart', 'figure'),
        Input('dynamic-chart-type', 'value')
    )
    def update_dynamic_chart(chart_type):
        """Update the dynamic chart visualization based on selected type."""
        data = fetch_cryptocurrency_data()
        if chart_type == 'candlestick':
            fig = go.Figure(
                data=[go.Candlestick(
                    x=['BTC', 'ETH', 'LTC', 'BNB', 'DOGE'],
                    open=[12, 15, 20, 18, 22],
                    high=[15, 18, 25, 22, 28],
                    low=[10, 12, 18, 16, 20],
                    close=[13, 17, 23, 20, 25]
                )]
            )
            fig.update_layout(title='Candlestick Chart', template='plotly_dark')
        else:
            fig = px.bar(data, x='Symbol', y='Price (USD)', title=f'{chart_type.title()} Chart', text='Price (USD)')
            fig.update_layout(template='plotly_dark')

        return fig
