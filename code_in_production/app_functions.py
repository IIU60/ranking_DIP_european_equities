#import eikon as ek
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import dateutil.relativedelta
from tqdm import tqdm
import os
import streamlit as st
import plotly.express as px


def get_data(fields:list,desired_field_name:str):
    
    ek.set_app_key('89915a3b58874e1599870c6ecc45d6edd6344f8c')

    start_date = dt.date(2000,1,1)
    end_date = dt.date(2023,1,1)
    dates = [start_date]
    i = 0
    while (dates[0] + dateutil.relativedelta.relativedelta(months=i+1)) <= end_date:
        dates.append(dates[0] + dateutil.relativedelta.relativedelta(months=i+1))
        i += 1
    str_dates = list(map(str,dates))

    complete_df = pd.DataFrame(columns=['Instrument','Date','CallDate'])

    errors_dict = {}

    for date in tqdm(str_dates,smoothing=0):
        try:
            returned_df,err = ek.get_data(f'0#.STOXX({date})',fields=fields,parameters={'SDate':date})
        except Exception as x:
            print('failed for '+ date)
            errors_dict[date] = x
        else:
            returned_df['CallDate'] = date
            complete_df = pd.concat([complete_df,returned_df],axis=0)

    if not not errors_dict:
        for date in tqdm(list(errors_dict.keys()),smoothing=0):
            try:
                returned_df,err = ek.get_data(f'0#.STOXX({date})',fields=fields,parameters={'SDate':date})
            except Exception as x:
                print('failed again for '+ date)
                errors_dict[date] = x
            else:
                returned_df['CallDate'] = date
                complete_df = pd.concat([complete_df,returned_df],axis=0)

    complete_df.to_csv(f'C:/Users/hugo.perezdealbeniz/Desktop/Ranking DIP European Equities/Reuters Eikon/data/raw_data/raw_{desired_field_name}.csv',index=False)
    
    complete_df.rename(columns={list(set(complete_df.columns)-set(['Instrument','Date','CallDate']))[0]:desired_field_name},inplace = True)

    pivoted_df = complete_df.pivot(index='CallDate',columns='Instrument', values=desired_field_name)
    pivoted_df.to_csv(f'C:/Users/hugo.perezdealbeniz/Desktop/Ranking DIP European Equities/Reuters Eikon/data/pivoted_data/pivoted_{desired_field_name}.csv')

    return pivoted_df,errors_dict

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
def rank_data(pivoted_df, prices_csv_filepath, n_quantiles=5):

    #len_input = len(pivoted_df)

    pivoted_df = pivoted_df.dropna(axis=0,how='all').dropna(axis=1,how='all')
    pivoted_df = pivoted_df.loc[(pivoted_df.notna().sum(axis=1)/600)>0.8] # Estas dos lineas tambien se tendran que borrar y que la funcion solo reciba datos limpios

    ranked_df = pivoted_df.copy()

    for date,prices in zip(pivoted_df.index,pivoted_df.astype(float).values):
        ranked_df.loc[date] = pd.qcut(prices,n_quantiles,duplicates='drop',labels=False)

    #### decil 0 tiene los valores mas bajos y el 9 los mas altos ####

    precios_df = pd.read_csv(prices_csv_filepath,index_col='CallDate')

    extra_stocks = set(precios_df.columns)-set(ranked_df.columns)

    ranked_df = ranked_df.loc[:,list(set(precios_df.columns)-extra_stocks)]
    precios_df = precios_df.loc[:,ranked_df.columns]

    try:
        ranked_df.drop(index='2000-01-01',inplace=True)  #
    except KeyError:
        pass

    rentabilidad_acciones_df = precios_df.pct_change()

    deciles_df = pd.DataFrame(columns = ['equiponderado'])
    for i in range(n_quantiles):
        rents_list = []
        for date,ranks in ranked_df.T.items():
            rents_list.append(rentabilidad_acciones_df.loc[date,ranks == i].mean())
        deciles_df[f'decil_{i}'] = rents_list
    deciles_df['equiponderado'] = deciles_df.mean(axis=1)
    deciles_df = deciles_df.set_index(ranked_df.index)


    #if return_notna_graph == True:
    #    notna_graph = plt.figure()
    #    (pivoted_df.notna().sum(axis=1)/600).plot()
    #    plt.title(f'Dates kept:{len(ranked_df)}/{len_input}')
    #    plt.close()
    #    return rentabilidades_dict, notna_graph
    
    return deciles_df


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
    pivoted_df = pd.read_csv('../data/pivoted_data/pivoted_EV.csv',index_col=0)
    prices_csv_filepath = '../data\Final Data\PriceClose.csv'
    return_notna_graph = False
    n_quantiles = 10
    rents_dict = rank_data(pivoted_df,prices_csv_filepath,n_quantiles, return_dict=True)
    plot_NAV_absoluto(rents_dict)
    plt.show()