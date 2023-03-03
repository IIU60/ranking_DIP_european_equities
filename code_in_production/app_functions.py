import pandas as pd
import numpy as np
import os
import streamlit as st
import plotly.express as px

@st.cache_data
def filter_data(pivoted_data_directory_filepath, min_stocks_per_date_ratio=0.8, min_total_dates_ratio=0.8):
    
    good_dfs = {}
    bad_dfs = {}
    
    for filename in os.listdir(pivoted_data_directory_filepath):
        filepath = os.path.join(pivoted_data_directory_filepath,filename)
        df = pd.read_csv(filepath,index_col=0)
        len_input = len(df)
        df = df.dropna(axis=0,how='all').dropna(axis=1,how='all')
        df = df.loc[(df.notna().sum(axis=1)/600)>min_stocks_per_date_ratio]
        maintained_dates_ratio = len(df)/len_input
        if maintained_dates_ratio > min_total_dates_ratio:
            good_dfs[filename.strip('pivoted_').strip('.csv')] = df
        else:
            bad_dfs[filename.strip('pivoted_').strip('.csv')] = df
    return good_dfs,bad_dfs

@st.cache_data
def rank_data(pivoted_df, n_quantiles, type_=['alto','bajo']):
    
    ranks_list = []
    labels = range(1,n_quantiles+1) if type_=='bajo' else (range(n_quantiles,0,-1) if type_ == 'alto' else 'null')

    for row in pivoted_df.values:
        ranks_list.append(pd.qcut(row,n_quantiles,duplicates='drop',labels=labels))
    
    return pd.DataFrame(np.array(ranks_list), index=pivoted_df.index, columns=pivoted_df.columns)


@st.cache_data
def get_rents_df(ranked_df, prices_csv_filepath, n_quantiles):

    precios_df = pd.read_csv(prices_csv_filepath,index_col='CallDate')

    extra_stocks = set(precios_df.columns)-set(ranked_df.columns)

    ranked_df = ranked_df.loc[:,list(set(precios_df.columns)-extra_stocks)]
    precios_df = precios_df.loc[:,ranked_df.columns]

    try:
        ranked_df.drop(index='2000-01-01',inplace=True)
    except KeyError:
        pass

    rentabilidad_acciones_df = precios_df.pct_change()
    
    deciles_df = pd.DataFrame(columns = ['equiponderado'])
    for i in range(1,n_quantiles+1):
        rents_list = []
        for date,ranks in ranked_df.T.items():
            rents_list.append(rentabilidad_acciones_df.loc[date,ranks == i].mean())
        deciles_df[f'decil_{i}'] = rents_list
    deciles_df['equiponderado'] = deciles_df.mean(axis=1)
    deciles_df = deciles_df.set_index(ranked_df.index)

    return deciles_df

@st.cache_data
def multi_factor_ranking(weights_df, data_dict, n_quantiles):

    weights_df = weights_df.loc[weights_df.Weight > 0]

    ranked_data_dict = {}
    columns_list = []
    for factor,type_ in zip(weights_df.Factor,weights_df.Type):
        ranked_data = rank_data(data_dict[factor],n_quantiles, type_)
        ranked_data_dict[factor] = ranked_data
        columns_list.append(ranked_data.columns)

    common_columns = columns_list[0]
    for i in columns_list[1:]:
        common_columns = common_columns.intersection(i)

    weighted_df_dict = {}
    for factor,ranked_df in ranked_data_dict.items():
        weight = float(weights_df.loc[weights_df.Factor==factor].Weight)
        weighted_df_dict[factor] = ranked_df[common_columns]*weight

    dates = weighted_df_dict[list(weighted_df_dict.keys())[0]].index
    final_df_list = []
    for date in dates:
        summing_list = []
        try:
            for factor_df in weighted_df_dict.values():
                summing_list.append(factor_df.loc[date])
        except KeyError:
            continue
        final_df_list.append(sum(summing_list)/len(summing_list))

    return pd.DataFrame(final_df_list)


def plot_NAV_absoluto(df,colors,log_scale=False):
    fig = px.line(df.cumsum(), x=df.index, y=df.columns, color_discrete_sequence = colors)
    fig.update_layout(hovermode='x unified')
    if log_scale == True:
        fig.update_yaxes(type='log')
    return fig
    

def plot_NAV_relativo(df,colors,log_scale=False):
    fig = px.line((df.T - df.equiponderado).T.cumsum(), color_discrete_sequence = colors)
    fig.update_layout(hovermode='x unified')
    if log_scale == True:
        fig.update_yaxes(type='log')
    return fig


def plot_rentabilidad_media(df,colors,*args):
    rents_medias = pd.DataFrame(np.diag(np.mean(df*np.sqrt(12))),columns = df.columns, index = df.columns)
    fig = px.bar(rents_medias,color_discrete_sequence=colors)
    return fig


def plot_volatilidad(df,colors,*args):
    vols = pd.DataFrame(np.diag(np.std(df*np.sqrt(12),axis=0)),columns = df.columns, index = df.columns)
    fig = px.bar(vols,color_discrete_sequence=colors)
    return fig


def plot_sharpe(df,colors,*args):
    rents_medias = np.mean(df*np.sqrt(12),axis=0)
    vols_anualizadas = np.std(df*np.sqrt(12),axis=0)
    sharpe = pd.DataFrame(np.diag(rents_medias/vols_anualizadas),columns = df.columns, index = df.columns)
    fig = px.bar(sharpe,color_discrete_sequence=colors)
    return fig


if __name__=='__main__':
    pass