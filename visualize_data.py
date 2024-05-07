from typing import Dict, List, Union, Callable
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs as go
from dataclasses import dataclass, field
import json
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder

@dataclass
class VisualizationConfig:
    """Configuration class for visualizations."""
    data: Dict[str, List[Union[int, float, str]]]
    visualization_type: str = 'line'
    title: str = 'My Visualization'
    plotly_function: Callable = field(init=False)
    additional_kwargs: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Set up mapping of visualization types to Plotly Express functions."""
        plot_functions = {
            'line': px.line,
            'bar': px.bar,
            'scatter': px.scatter,
            'pie': px.pie,
            'histogram': px.histogram,
            'box': px.box,
            'heatmap': px.density_heatmap,
            'sunburst': px.sunburst,
            'funnel': px.funnel,
            'strip': px.strip,
            'treemap': px.treemap,
            'area': px.area,  # Additional visualization types
            'violin': px.violin
        }

        # Validate and assign the appropriate Plotly function
        if self.visualization_type not in plot_functions:
            supported_types = ', '.join(plot_functions.keys())
            raise ValueError(f"Unsupported visualization type '{self.visualization_type}'. "
                             f"Supported types: {supported_types}.")
        self.plotly_function = plot_functions[self.visualization_type]
        self.set_dynamic_title()

    def set_dynamic_title(self):
        """Set dynamic title based on the visualization type or use user-provided title."""
        if 'title' in self.additional_kwargs:
            self.title = self.additional_kwargs['title']
        else:
            self.title = f"{self.visualization_type.capitalize()} Visualization"

def create_visualization(config: VisualizationConfig) -> str:
    """Generate Plotly visualization based on the provided configuration.

    Args:
        config (VisualizationConfig): Configuration object defining the type of visualization and data.

    Returns:
        str: JSON-encoded Plotly graph data.
    """
    df = pd.DataFrame(config.data)

    # Ensure required columns are present and have correct data types
    if config.visualization_type != 'pie' and ('x' not in df.columns or 'y' not in df.columns):
        raise ValueError("Input data must contain 'x' and 'y' keys for this visualization type.")
    
    if config.visualization_type != 'pie':
        df['y'] = df['y'].astype(float)  # Ensure y-values are numeric

    # Generate the desired visualization using Plotly Express functions
    if config.visualization_type == 'pie':
        fig = config.plotly_function(df, values='y', names='x', title=config.title)
    else:
        fig = config.plotly_function(df, x='x', y='y', title=config.title, **config.additional_kwargs)

    # Additional layout settings can be added here
    return json.dumps({"data": fig.data, "layout": fig.layout}, cls=plotly.utils.PlotlyJSONEncoder)


def create_custom_graph(graph_type: str, data: List[Dict[str, Union[int, float, str]]], layout: Dict[str, Union[str, int, float]]) -> str:
    """Create a custom Plotly graph using Graph Objects.

    Args:
        graph_type (str): The type of graph to create.
        data (List[Dict[str, Union[int, float, str]]]): List of data dictionaries with 'x' and 'y' keys.
        layout (Dict[str, Union[str, int, float]]): Dictionary containing layout configurations.

    Returns:
        str: JSON-encoded Plotly graph data.
    """
    graph_map = {
        'scatter': go.Scatter,
        'bar': go.Bar,
        'line': go.Scatter  # For line charts
    }

    if graph_type not in graph_map:
        raise ValueError(f"Unsupported graph type '{graph_type}'.")

    graph_class = graph_map[graph_type]
    fig_data = [graph_class(**item) for item in data]
    fig_layout = go.Layout(**layout)
    fig = go.Figure(data=fig_data, layout=fig_layout)

    return json.dumps({"data": fig.data, "layout": fig.layout}, cls=PlotlyJSONEncoder)