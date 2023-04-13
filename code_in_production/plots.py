import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

colors = ['#000000'] + px.colors.diverging.RdYlGn_r [::]

ANUALISING_PERIOD = 12

@st.cache_data
def plot_NAV_absoluto(df, indicator_name='',log_scale=False):
    fig = px.line((df+1).cumprod(), x=df.index, y=df.columns, color_discrete_sequence=colors)
    fig.update_layout(hovermode='x unified')
    if log_scale == True:
        fig.update_yaxes(type='log')
    fig.update_layout(title=indicator_name + ' - NAV Absoluto', xaxis_title='Date')
    return fig


@st.cache_data
def plot_NAV_relativo(df, indicator_name='',log_scale=False):
    fig = px.line((df.T - df.equiponderado + 1).T.cumprod(), color_discrete_sequence = colors)
    fig.update_layout(hovermode='x unified')
    if log_scale == True:
        fig.update_yaxes(type='log')
    fig.update_layout(title=indicator_name + ' - NAV relativo', xaxis_title='Date')
    return fig


@st.cache_data
def plot_rentabilidad_media(df, indicator_name='',*args,**kwargs):
    rents_medias = pd.DataFrame(np.diag(np.mean(df*ANUALISING_PERIOD,axis=0)),columns = df.columns, index = df.columns)
    fig = px.bar(rents_medias,color_discrete_sequence=colors)
    fig.update_layout(title=indicator_name + ' - Rentabilidad Media Anualizada',xaxis_title=None)
    return fig


@st.cache_data
def plot_volatilidad(df, indicator_name='',*args,**kwargs):
    vols = pd.DataFrame(np.diag(np.std(df*np.sqrt(ANUALISING_PERIOD),axis=0)),columns = df.columns, index = df.columns)
    fig = px.bar(vols,color_discrete_sequence=colors)
    fig.update_layout(title=indicator_name + ' - Volatilidad Anualizada',xaxis_title=None)
    return fig


@st.cache_data
def plot_sharpe(df, indicator_name='',*args,**kwargs):
    rents_medias = np.mean(df*ANUALISING_PERIOD,axis=0)
    vols_anualizadas = np.std(df*np.sqrt(12),axis=0)
    sharpe = pd.DataFrame(np.diag(rents_medias/vols_anualizadas),columns = df.columns, index = df.columns)
    fig = px.bar(sharpe,color_discrete_sequence=colors)
    fig.update_layout(title=indicator_name + ' - Ratio Sharpe',xaxis_title=None)
    return fig

def notna_plot(df):
    data = df.notna().sum(axis=1)
    fig = px.line(data)
    return fig