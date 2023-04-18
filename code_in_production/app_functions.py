import pandas as pd
import numpy as np
import os
import streamlit as st
from  warnings import warn


@st.cache_data
def filter_data(pivoted_data_directory_filepath, min_stocks_per_date_ratio=0.0, min_total_dates_ratio=0.0,expected_stocks_per_date=1,mask=None):
    
    good_dfs = {}
    bad_dfs = {}
    
    for filename in os.listdir(pivoted_data_directory_filepath):

        filepath = os.path.join(pivoted_data_directory_filepath,filename)
        df = read_and_sort_data(filepath)
        len_input = len(df)
        if expected_stocks_per_date == 1:
            expected_stocks_per_date = df.shape[1]
        masked_df = apply_mask(df,mask)
 
        masked_df = masked_df.dropna(axis=0,how='all').dropna(axis=1,how='all')
        masked_df = masked_df.loc[(masked_df.notna().sum(axis=1)/expected_stocks_per_date)>min_stocks_per_date_ratio]
        
        maintained_dates_ratio = len(masked_df)/len_input
        
        if maintained_dates_ratio > min_total_dates_ratio:
            good_dfs[filename.split('.')[0]] = df
        else:
            bad_dfs[f"{filename.split('.')[0]}: {maintained_dates_ratio}"] = df
    
    return good_dfs,bad_dfs


@st.cache_data
def rank_data(df:pd.DataFrame, n_quantiles:int, type_=['high','low']):

    df = df.astype(float)
    df = df.replace(to_replace=0,value=np.nan) # This was put in place to allow binning of rows with many 0s (duplicates in pct_change) - should be changed to something universal or dropped (not all rows which cannot be binned will be like so because of too many 0s. RSI for example does this with 100s)
    df = df.dropna(how='all',axis=0).dropna(how='all',axis=1)

    ranks_list = []
    failed_to_rank = []
    labels = range(1,n_quantiles+1) if type_=='low' else (range(n_quantiles,0,-1) if type_ == 'high' else None)
    if labels==None:
        raise ValueError('Type must be either "high" or "low"')
    
    for i, row in enumerate(df.values):
        try:
            ranks_list.append(pd.qcut(row,n_quantiles,duplicates='drop',labels=labels))
        except ValueError:
            failed_to_rank.append(i)
    print(failed_to_rank)
    return pd.DataFrame(np.array(ranks_list), index=df.index.delete(failed_to_rank), columns=df.columns)


@st.cache_data
def get_returns(ranked_df:pd.DataFrame, prices_df:pd.DataFrame, n_quantiles:int, shift_period:int,rets_period:int):

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

    return quantiles_df


@st.cache_data
def multi_factor_ranking(weights_df:pd.DataFrame, data_dict:dict, n_quantiles:int,mask:pd.DataFrame):

    weights_df = weights_df.loc[weights_df.Weight > 0]

    ranked_data_dict = {}
    columns_list = []
    for factor,type_ in zip(weights_df.Factor,weights_df.Type):
        masked_data = apply_mask(data_dict[factor],mask)
        ranked_data = rank_data(masked_data,n_quantiles, type_)
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
    failed_dates = []
    for date in dates:
        summing_list = []
        try:
            for factor_df in weighted_df_dict.values():
                summing_list.append(factor_df.loc[date])
        except KeyError:
            failed_dates.append(date)
            continue
        final_df_list.append(sum(summing_list)/len(summing_list))

    return pd.DataFrame(final_df_list,index=dates.delete(failed_dates),columns=common_columns) ## dict_keys remove


@st.cache_data
def apply_mask(df,mask=None,mask_fp=None):
    if mask is None:
        if mask_fp is None:
            warn("No mask was provided.")
            return df
        mask = read_and_sort_data(mask_fp)
    common_columns = sorted(list(set(df.columns) & set(mask.columns)))
    common_rows = sorted(list(set(df.index) & set(mask.index)))
    df = df.loc[common_rows,common_columns]
    mask = mask.loc[common_rows,common_columns]
    return df.where(mask)

@st.cache_data
def read_and_sort_data(filepath):
    df = pd.read_csv(filepath,index_col=0,sep=',')
    df = df.set_index(pd.to_datetime(df.index)).sort_index()
    return df
