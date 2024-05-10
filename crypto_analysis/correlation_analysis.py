import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def calculate_and_plot_correlations(prices_df: pd.DataFrame, title: str = 'Asset Correlation Matrix') -> pd.DataFrame:
    correlation_matrix = prices_df.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap='coolwarm', square=True)
    plt.title(title)
    plt.show()
    return correlation_matrix
