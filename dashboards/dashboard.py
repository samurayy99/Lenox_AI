from flask import Flask
from dash import Dash, dcc, html, dash_table
from .callbacks import register_callbacks
# In dashboards/dashboard.py
from metrics.metrics import rmse, mae, accuracy_score, f1_score


def create_dashboard(server: Flask) -> Flask:
    """Create a comprehensive cryptocurrency analysis dashboard."""
    dash_app = Dash(server=server, routes_pathname_prefix='/dashboard/')

    # Define the layout for the Dash app
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

    # Register all callbacks for the Dash app
    register_callbacks(dash_app)

    return server


def evaluate_predictions(predictions, targets):
    rmse_value = rmse(predictions, targets)
    mae_value = mae(predictions, targets)
    accuracy = accuracy_score(predictions, targets)

    # Return or store results for further visualization
    return {
        "rmse": rmse_value,
        "mae": mae_value,
        "accuracy": accuracy
    }