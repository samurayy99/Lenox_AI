from flask import Flask
from dash import Dash, dcc, html
from .callbacks import register_callbacks

def create_dashboard(server: Flask) -> Dash:
    """Create a comprehensive cryptocurrency analysis dashboard."""
    dash_app = Dash(server=server, routes_pathname_prefix='/dashboard/')

    # Define the layout for the Dash app
    dash_app.layout = html.Div([
        html.H1("CryptoMaster Ultimate Dashboard", style={'textAlign': 'center'}),
        dcc.Tabs(id='main-tabs', value='tab-market', children=[
            dcc.Tab(label='Market Overview', value='tab-market'),
            dcc.Tab(label='Comparative Analysis', value='tab-comparative'),
            dcc.Tab(label='Historical Data Analysis', value='tab-historical'),
            dcc.Tab(label='Predictive Analytics', value='tab-predictive'),
            dcc.Tab(label='Technical Analysis', value='tab-technical'),
            dcc.Tab(label='Dynamic Visualization', value='tab-dynamic')
        ]),
        html.Div(id='main-tab-content')  # Update to match the ID referenced in callbacks
    ])

    # Register all callbacks for the Dash app
    register_callbacks(dash_app)

    return dash_app

# Example function (can be omitted if unused)
def evaluate_predictions(predictions, targets):
    from metrics.metrics import rmse, mae, accuracy_score, f1_score
    rmse_value = rmse(predictions, targets)
    mae_value = mae(predictions, targets)
    accuracy = accuracy_score(predictions, targets)

    # Return or store results for further visualization
    return {
        "rmse": rmse_value,
        "mae": mae_value,
        "accuracy": accuracy
    }
