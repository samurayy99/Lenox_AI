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

def create_visualization(config: VisualizationConfig) -> str:
    df = pd.DataFrame(config.data)
    if config.visualization_type == 'pie':
        fig: Figure = config.plotly_function(df, values='y', names='x', **config.additional_kwargs)
    else:
        fig: Figure = config.plotly_function(df, x='x', y='y', **config.additional_kwargs)
    return json.dumps({"data": fig.data, "layout": fig.layout}, cls=plotly.utils.PlotlyJSONEncoder)