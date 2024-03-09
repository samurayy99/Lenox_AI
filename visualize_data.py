from typing import Dict, List, Union, Callable
import pandas as pd
import plotly
import plotly.express as px
import json
from dataclasses import dataclass, field
from plotly.graph_objs import Figure

@dataclass
class VisualizationConfig:
    data: Dict[str, List[Union[int, float, str]]]
    visualization_type: str = 'line'
    title: str = 'My Visualization'
    plotly_function: Callable = field(init=False)
    additional_kwargs: Dict = field(default_factory=dict)

    def __post_init__(self):
        # Mapping of visualization types to Plotly Express functions
        plot_functions = {
            'line': px.line,
            'bar': px.bar,
            'scatter': px.scatter,
            'pie': px.pie,
            'histogram': px.histogram,  # Hinzugefügt
            'box': px.box,  # Hinzugefügt
        }
        if self.visualization_type not in plot_functions:
            supported_types = ', '.join(plot_functions.keys())
            raise ValueError(f"Unsupported visualization type '{self.visualization_type}'. Supported types: {supported_types}.")
        self.plotly_function = plot_functions[self.visualization_type]
        self.set_dynamic_title()  # Korrekt innerhalb der Klasse aufgerufen

    def set_dynamic_title(self):
        if 'title' in self.additional_kwargs:
            self.title = self.additional_kwargs['title']
        else:
            self.title = f"{self.visualization_type.capitalize()} Visualization"


def create_visualization(config: VisualizationConfig) -> str:
    df = pd.DataFrame(config.data)
    
    # Check if 'x' and 'y' keys exist for non-pie charts
    if config.visualization_type != 'pie' and ('x' not in config.data or 'y' not in config.data):
        raise ValueError("Input data must contain 'x' and 'y' keys for this visualization type.")
    
    # Convert 'y' values to float if the visualization type is not 'pie'
    if config.visualization_type != 'pie':
        try:
            df['y'] = df['y'].astype(float)
        except ValueError as e:
            raise ValueError(f"Y values must be convertible to floats. Error: {e}")

    # Generate the figure based on the visualization type
    if config.visualization_type == 'pie':
        # For pie charts, assume the values are in the 'y' column and categories are in the 'x' column
        fig: Figure = config.plotly_function(df, values='y', names='x', **config.additional_kwargs)
    else:
        # For other chart types, use 'x' and 'y' columns
        fig: Figure = config.plotly_function(df, x='x', y='y', **config.additional_kwargs)
    
    return json.dumps({"data": fig.data, "layout": fig.layout}, cls=plotly.utils.PlotlyJSONEncoder)
