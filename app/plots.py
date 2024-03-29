# This code defines several functions to plot financial data using Plotly.
# The functions are:
# - plot_NAV_absoluto: plots the absolute net asset value of a financial instrument.
# - plot_NAV_relativo: plots the relative net asset value of a financial instrument.
# - plot_rentabilidad_media: plots the annualized average return of a financial instrument.
# - plot_volatilidad: plots the annualized volatility of a financial instrument.
# - plot_sharpe: plots the Sharpe ratio of a financial instrument.
# - notna_plot: plots the number of non-null values in a DataFrame over time.

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# Define a color palette for the plots.
colors = ['#000000'] + px.colors.diverging.RdYlGn_r [::]

# Define a configuration for the "to image" button in the plots.
config = {
  'toImageButtonOptions': { 'height': None, 
                           'width': None, 
                           'format':'png',
                           'scale': 1}
}

# Define a constant for the annualizing period.
ANUALISING_PERIOD = 12

# Define a function to plot the absolute net asset value of a financial instrument.
@st.cache_data
def plot_NAV_absoluto(df, indicator_name='',log_scale=False):
    # Create a Plotly figure with the cumulative product of the DataFrame plus one.
    fig = px.line((df+1).cumprod(), x=df.index, y=df.columns, color_discrete_sequence=colors)
    # Set the hover mode to show all data points at once.
    fig.update_layout(hovermode='x unified')
    # If the log scale is enabled, set the y-axis to logarithmic.
    if log_scale == True:
        fig.update_yaxes(type='log')
    # Set the title and x-axis label of the plot.
    fig.update_layout(title=indicator_name + ' - NAV Absoluto', xaxis_title='Date')
    return fig

# Define a function to plot the relative net asset value of a financial instrument.
@st.cache_data
def plot_NAV_relativo(df, indicator_name='',log_scale=False):
    # Create a Plotly figure with the cumulative product of the DataFrame minus the equiponderated DataFrame plus one.
    fig = px.line((df.T - df.equiponderado + 1).T.cumprod(), color_discrete_sequence = colors)
    # Set the hover mode to show all data points at once.
    fig.update_layout(hovermode='x unified')
    # If the log scale is enabled, set the y-axis to logarithmic.
    if log_scale == True:
        fig.update_yaxes(type='log')
    # Set the title and x-axis label of the plot.
    fig.update_layout(title=indicator_name + ' - NAV relativo', xaxis_title='Date')
    return fig

# Define a function to plot the annualized average return of a financial instrument.
@st.cache_data
def plot_rentabilidad_media(df, indicator_name='',*args,**kwargs):
    # Create a DataFrame with the diagonal of the mean of the DataFrame times the annualizing period.
    rents_medias = pd.DataFrame(np.diag(np.mean(df*ANUALISING_PERIOD,axis=0)),columns = df.columns, index = df.columns)
    # Create a Plotly figure with a bar chart of the DataFrame.
    fig = px.bar(rents_medias,color_discrete_sequence=colors)
    # Set the title of the plot.
    fig.update_layout(title=indicator_name + ' - Rentabilidad Media Anualizada',xaxis_title=None)
    return fig

# Define a function to plot the annualized volatility of a financial instrument.
@st.cache_data
def plot_volatilidad(df, indicator_name='',*args,**kwargs):
    # Create a DataFrame with the diagonal of the standard deviation of the DataFrame times the square root of the annualizing period.
    vols = pd.DataFrame(np.diag(np.std(df*np.sqrt(ANUALISING_PERIOD),axis=0)),columns = df.columns, index = df.columns)
    # Create a Plotly figure with a bar chart of the DataFrame.
    fig = px.bar(vols,color_discrete_sequence=colors)
    # Set the title of the plot.
    fig.update_layout(title=indicator_name + ' - Volatilidad Anualizada',xaxis_title=None)
    return fig

# Define a function to plot the Sharpe ratio of a financial instrument.
@st.cache_data
def plot_sharpe(df, indicator_name='',*args,**kwargs):
    # Calculate the annualized average return of the DataFrame.
    rents_medias = np.mean(df*ANUALISING_PERIOD,axis=0)
    # Calculate the annualized volatility of the DataFrame.
    vols_anualizadas = np.std(df*np.sqrt(12),axis=0)
    # Create a DataFrame with the diagonal of the Sharpe ratio of the DataFrame.
    sharpe = pd.DataFrame(np.diag(rents_medias/vols_anualizadas),columns = df.columns, index = df.columns)
    # Create a Plotly figure with a bar chart of the DataFrame.
    fig = px.bar(sharpe,color_discrete_sequence=colors)
    # Set the title of the plot.
    fig.update_layout(title=indicator_name + ' - Ratio Sharpe',xaxis_title=None)
    return fig


def infer_inferred_freqs(data:pd.DataFrame|pd.Series) -> str:
    try:
        all_samples = np.lib.stride_tricks.sliding_window_view(data.index, window_shape=10)
    except ValueError as x:
        if x.args[0] == 'window shape cannot be larger than input array shape':
            raise ValueError('Insufficient data to infer frequency. Must be longer than 10')
        raise x
    
    rand_indices = np.unique(np.random.randint(0, all_samples.shape[0], size=30))

    samples = all_samples[rand_indices]

    freqs = pd.Series(list(samples)).apply(pd.infer_freq)

    freqs_count = freqs.value_counts().sort_values(ascending=False)

    if len(freqs_count) == 0:
        raise ValueError('Inferred data frequency is None')
    elif len(freqs_count)>1:
        if freqs_count.duplicated(keep='first').iloc[1]==True:
            raise ValueError('Inferred data frequency is Duplicated')

    return freqs_count.index[0]


# Define a function to plot the number of non-null values in a DataFrame over time.
def notna_plot(df, relative=False):

    infered_freq = infer_inferred_freqs(df)

    filled_df = df.asfreq(infered_freq)

    if relative == True:
        na_counts = filled_df.notna().sum(axis=1)/len(filled_df.columns)
    else:
        na_counts = filled_df.notna().sum(axis=1)

    changes = (na_counts==0).astype(int).diff()

    na_ranges = np.array((changes.iloc[changes.index.get_indexer(changes.loc[changes==1].index)-1].index,changes.loc[changes==-1].index)).T

    fig = px.line(na_counts)

    for start, end in na_ranges.astype(str):

        fig.add_vrect(x0=start, x1=end, fillcolor='red', opacity=0.5, line_width=0)
    
    fig.update_traces(line_color='#000000')

    return fig