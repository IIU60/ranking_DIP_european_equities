import eikon as ek
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import dateutil.relativedelta
from tqdm import tqdm

ek.set_app_key('89915a3b58874e1599870c6ecc45d6edd6344f8c')

def get_data(fields:list,desired_field_name:str):
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


def rank_data(pivoted_df, prices_csv_filepath, return_notna_graph = True, n_quantiles = 5):

    len_input = len(pivoted_df)

    pivoted_df = pivoted_df.dropna(axis=0,how='all').dropna(axis=1,how='all')
    pivoted_df = pivoted_df.loc[pivoted_df.notna().sum(axis=1)>200]

    ranked_df = pivoted_df.copy()
    ###### HAY QUE HACER DE FORMA VECTORIZADA #########
    for date,prices in zip(pivoted_df.index,pivoted_df.astype(float).values):
        ranked_df.loc[date] = pd.qcut(prices,n_quantiles,duplicates='drop',labels=False)

    #### decil 0 tiene los valores mas bajos y el 9 los mas altos ####
    def deciles_lists(df):
        diccionario = {}
        for i in range(n_quantiles):
            diccionario[f'decil_{i}'] = {}
            for date,ranks in df.T.items():
                diccionario[f'decil_{i}'][date] = ranks.loc[ranks == i].index.tolist()
        return diccionario

    precios_df = pd.read_csv(prices_csv_filepath,index_col='CallDate')

    extra_stocks = set(precios_df.columns)-set(ranked_df.columns)

    ranked_df = ranked_df.loc[:,list(set(precios_df.columns)-extra_stocks)]
    precios_df = precios_df.loc[:,ranked_df.columns]

    try:
        ranked_df.drop(index='2000-01-01',inplace=True)
    except KeyError:
        pass

    deciles_dict = deciles_lists(ranked_df)
    rentabilidad_acciones_df = precios_df.pct_change()

    rentabilidades_dict = {}
    rentabilidades_dict['equiponderado'] = {}
    for decil,fechas in deciles_dict.items():
        rentabilidades_dict[decil] = {}
        for fecha, stocks in fechas.items():
            rentabilidades_dict[decil][fecha] = rentabilidad_acciones_df.loc[fecha,stocks].mean()
            rentabilidades_dict['equiponderado'][fecha] = rentabilidad_acciones_df.loc[fecha].mean()

    if return_notna_graph == True:
        notna_graph = plt.figure()
        (pivoted_df.notna().sum(axis=1)/600).plot()
        plt.title(f'Dates kept:{len(ranked_df)}/{len_input}')
        plt.close()
        return rentabilidades_dict, notna_graph
    
    return rentabilidades_dict

def plot_NAV_absoluto(rentabilidades_dict):

    fig = plt.figure(figsize=(20,10))
    for decil in rentabilidades_dict:
        plt.plot(list(rentabilidades_dict['decil_0'].keys()),np.array(list(rentabilidades_dict[decil].values())).cumsum(),label=decil)
    plt.xticks(rotation=-45,fontsize=10,ha='left',rotation_mode='anchor')
    plt.legend()
    plt.title('NAV Absoluto')
    plt.close()
    return fig
    
def plot_NAV_relativo(rentabilidades_dict):
    equiponderado = np.array(list(rentabilidades_dict['equiponderado'].values()))
    fig = plt.figure(figsize=(20,10))
    for decil in rentabilidades_dict:
        plt.plot(list(rentabilidades_dict['decil_0'].keys()),(np.array(list(rentabilidades_dict[decil].values()))-equiponderado).cumsum(),label=decil)
    plt.xticks(rotation=-45,fontsize=10,ha='left',rotation_mode='anchor')
    plt.legend()
    plt.title('NAV relativo a Equiponderado')
    plt.close()
    return fig

def plot_rentabilidad_media(rentabilidades_dict):
    keys = list(rentabilidades_dict.keys())
    rentabilidades_medias = [np.mean(list(rentabilidades_dict[decil].values()))*np.sqrt(12) for decil in rentabilidades_dict]
    fig = plt.figure()
    plt.bar(keys[::-1],rentabilidades_medias[::-1])
    plt.xticks(rotation=-45,ha='left',rotation_mode='anchor')
    plt.title('Rentabilidad media anualizada')
    plt.close()
    return fig

def plot_Volatilidad(rentabilidades_dict):
    volatilidades_anualizadas = [np.std(list(rentabilidades_dict[decil].values()))*np.sqrt(12) for decil in rentabilidades_dict]
    keys = list(rentabilidades_dict.keys())
    fig = plt.figure()
    plt.bar(keys[::-1],volatilidades_anualizadas[::-1])
    plt.xticks(rotation=-45,ha='left',rotation_mode='anchor')
    plt.title('Volatilidad Anualizada')
    plt.close()
    return fig

def plot_sharpe(rentabilidades_dict):
    rentabilidades_medias = [np.mean(list(rentabilidades_dict[decil].values()))*np.sqrt(12) for decil in rentabilidades_dict]
    volatilidades_anualizadas = [np.std(list(rentabilidades_dict[decil].values()))*np.sqrt(12) for decil in rentabilidades_dict]
    sharpe = np.array(rentabilidades_medias)/np.array(volatilidades_anualizadas)
    keys = list(rentabilidades_dict.keys())
    fig = plt.figure()
    plt.bar(keys[::-1],sharpe[::-1])
    plt.xticks(rotation=-45,ha='left',rotation_mode='anchor')
    plt.title('Ratio Sharpe')
    plt.close()
    return fig