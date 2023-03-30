import pandas as pd
import numpy as np
import os
import streamlit as st


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
def rank_data(df:pd.DataFrame, n_quantiles:int, type_=['alto','bajo']):

    df = df.astype(float)
    df = df.replace(to_replace=0,value=np.nan) # This was put in place to allow binning of rows with many 0s (duplicates in pct_change) - should be changed to something universal or dropped (not all rows which cannot be binned will be like so because of too many 0s. RSI for does this with 100s)
    df = df.dropna(how='all',axis=0).dropna(how='all',axis=1)

    ranks_list = []
    failed_to_rank = []
    labels = range(1,n_quantiles+1) if type_=='bajo' else (range(n_quantiles,0,-1) if type_ == 'alto' else None)

    for i, row in enumerate(df.values):
        try:
            ranks_list.append(pd.qcut(row,n_quantiles,duplicates='drop',labels=labels))
        except ValueError:
            print(i)
            failed_to_rank.append(i)
    return pd.DataFrame(np.array(ranks_list), index=df.index.delete(failed_to_rank), columns=df.columns)


@st.cache_data
def get_rents_df(ranked_df:pd.DataFrame, prices_df:pd.DataFrame, n_quantiles:int, shift_period:int,rets_period:int):

    og_len = len(ranked_df)
    ranked_df = ranked_df.sort_index()
    prices_df = prices_df.sort_index()

    common_stocks = list(set(prices_df.columns) & set(ranked_df.columns))
    ranked_df = ranked_df.loc[:,common_stocks]
    prices_df = prices_df.loc[:,common_stocks]

    ranked_df = ranked_df.shift(shift_period)[shift_period:]

    returns_df = prices_df.pct_change(rets_period,limit=1)

    quantiles_df = pd.DataFrame(columns=['equiponderado'])
    for i in range(1, n_quantiles+1):
        returns_list = []
        for date,ranks in (ranked_df==i).T.items():
            returns_list.append(returns_df.loc[date,ranks].mean(axis=0))
        quantiles_df[f'decil_{i}'] = returns_list
    quantiles_df['equiponderado'] = quantiles_df.mean(axis=1)
    
    quantiles_df = quantiles_df.set_index(ranked_df.index)
    #quantiles_df.dropna(inplace=True)

    return quantiles_df, len(quantiles_df)/og_len


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
