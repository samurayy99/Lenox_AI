from typing import Dict, List, Union, Callable
import pandas as pd
import plotly
from plotly.io import to_json
import plotly.express as px
import json
import logging
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
        # Ergänze das plot_functions-Wörterbuch um zusätzliche Plotly-Funktionen
        plot_functions = {
            'line': px.line,
            'bar': px.bar,
            'scatter': px.scatter,
            'pie': px.pie,
            'histogram': px.histogram,  # Beispiel für eine Ergänzung
            'box': px.box,  # Ein weiteres Beispiel
        }
        self.plotly_function = plot_functions.get(self.visualization_type, px.line)
        
        
def create_visualization(config: VisualizationConfig):
    cleaned_data = {}
    for key, values in config.data.items():
        # Check if all values are either int or float, convert to float
        if all(isinstance(v, (int, float)) for v in values):
            cleaned_data[key] = [float(v) for v in values]
        # If values are mixed or non-numeric, keep as is but log a warning
        else:
            logging.warning(f"Non-numeric data found in column '{key}': {values}")
            cleaned_data[key] = values
    
    # Assuming 'x' and 'y' are the only columns needed for the visualization
    df = pd.DataFrame(cleaned_data)[['x', 'y']]
    logging.info(f"DataFrame types:\n{df.dtypes}")  # Log DataFrame types for debugging

    fig = config.plotly_function(df, **config.additional_kwargs)
    fig.update_layout(title=config.title)
    if 'x_label' in config.additional_kwargs:
        fig.update_xaxes(title_text=config.additional_kwargs['x_label'])
    if 'y_label' in config.additional_kwargs:
        fig.update_yaxes(title_text=config.additional_kwargs['y_label'])

    return fig    
        
        
