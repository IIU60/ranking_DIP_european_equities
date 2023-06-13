import pandas as pd
import numpy as np
import os
import streamlit as st
from  warnings import warn


# Filter data based on certain criteria
@st.cache_data
def filter_data(pivoted_data_directory_filepath, min_stocks_per_date_ratio=0.0, min_total_dates_ratio=0.0, expected_stocks_per_date=1, mask=None):
    """
    Given a path to the directory with pivoted data files, filter the data based on the criteria below.

    :param pivoted_data_directory_filepath: (string) path to directory containing pivoted data
    :param min_stocks_per_date_ratio: (float) minimum ratio of stocks to expected stocks per date
    :param min_total_dates_ratio: (float) minimum ratio of total dates that meet the min_stocks_per_date_ratio criterion
    :param expected_stocks_per_date: (int) expected number of stocks per date
    :param mask: (dataframe) mask to apply to the data

    :return: good_dfs (dict), bad_dfs (dict)
    """

    good_dfs = {}
    bad_dfs = {}
    
    for filename in os.listdir(pivoted_data_directory_filepath):

        filepath = os.path.join(pivoted_data_directory_filepath,filename)
        if os.path.isfile(filepath):
            print('Filtering: ',filename)
            
            # Read and sort the data file
            df = read_and_sort_data(filepath)

            # If expected_stocks_per_date is not passed in as an argument, set it as the number of columns in df
            if expected_stocks_per_date == 0:
                expected_stocks_per_date = df.shape[1]

            # Apply mask to the data, if provided
            masked_df = apply_mask(df,mask)
    
            # Drop rows and columns with all NaN values
            masked_df = masked_df.dropna(axis=0,how='all').dropna(axis=1,how='all')

            # Filter data based on the min_stocks_per_date_ratio and expected_stocks_per_date criteria
            masked_df = masked_df.loc[(masked_df.notna().sum(axis=1)/expected_stocks_per_date) > min_stocks_per_date_ratio]

            # Calculate ratio of dates that meet the above criterion
            maintained_dates_ratio = len(masked_df)/len(df)
            
            # Categorize data into good or bad based on the min_total_dates_ratio criterion
            if maintained_dates_ratio > min_total_dates_ratio:
                good_dfs[filename.split('.')[0]] = df.loc[masked_df.index]
            else:
                bad_dfs[f"{filename.split('.')[0]}: {maintained_dates_ratio}"] = df.loc[masked_df.index]
    
    return good_dfs,bad_dfs


# Rank data based on quantiles
@st.cache_data
def rank_data(df:pd.DataFrame, n_quantiles:int, type_=['high','low']):
    """
    Given a dataframe, rank the data into n_quantiles based on the values in each row, 
    with the option to rank the top or bottom n_quantiles.

    :param df: (dataframe) dataframe to be ranked
    :param n_quantiles: (int) number of quantiles to create
    :param type_: (string) type of ranking - can be 'high' or 'low'

    :return: df (dataframe)
    """

    # Replace 0s with nans and drop rows and columns with all NaN values
    df = df.replace(to_replace=0,value=np.nan) # This was put in place to allow binning of rows with many 0s (duplicates in pct_change) - should be changed to something universal or dropped (not all rows which cannot be binned will be like so because of too many 0s. RSI for example does this with 100s)
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)

    # Set rank labels based on argument type_
    ranks_list = []
    failed_to_rank = []
    labels = range(1,n_quantiles+1) if type_=='low' else (range(n_quantiles,0,-1) if type_ == 'high' else None)

    # Raise error if type_ argument is not properly formatted
    if labels==None:
        raise ValueError('Type must be either "high" or "low"')

    # Create quantiles for each row, append to ranks_list
    for i, row in enumerate(df.values):
        try:
            ranks_list.append(pd.qcut(row,n_quantiles,duplicates='drop',labels=labels))
        except ValueError:
            failed_to_rank.append(i)
    print('Failed to rank:\n',df.iloc[failed_to_rank].index.tolist())
    
    # Return ranked data as a dataframe
    return pd.DataFrame(np.array(ranks_list), index=df.index.delete(failed_to_rank), columns=df.columns)


# Calculate returns based on ranked data
@st.cache_data
def get_returns(ranked_df:pd.DataFrame, prices_df:pd.DataFrame, n_quantiles:int, shift_period:int, rets_period:int):
    """
    Given a ranked dataframe and a prices dataframe, calculate returns for each quantile over time.

    :param ranked_df: (dataframe) dataframe with ranked data
    :param prices_df: (dataframe) dataframe with prices data
    :param n_quantiles: (int) number of quantiles
    :param shift_period: (int) number of periods to shift ranked data by
    :param rets_period: (int) number of periods to calculate returns over

    :return: quantiles_df (dataframe)
    """

    # Get common columns between ranked and prices dataframes
    common_stocks = list(set(prices_df.columns) & set(ranked_df.columns))
    ranked_df = ranked_df.loc[:,common_stocks]
    prices_df = prices_df.loc[:,common_stocks]

    # Shift ranked data by shift_period and prices data by rets_period
    ranked_df = ranked_df.shift(shift_period)[shift_period:]
    returns_df = prices_df.pct_change(rets_period,limit=1)

    # Create a dataframe to hold quantile returns
    quantiles_df = pd.DataFrame(columns=['equiponderado'], dtype=float)

    # Iterate over each quantile
    failed_dates = []
    for i in range(1, n_quantiles+1):
        returns_list = []
        for date,ranks in (ranked_df==i).T.items():
            try:
                returns_list.append(returns_df.loc[date,ranks].mean(axis=0))
            except KeyError:
                warn(f'{date} not found in prices file')
                ranked_df.drop(date,inplace=True)
                failed_dates.append(date)
        quantiles_df[f'decil_{i}'] = returns_list

    # Take mean of quantile returns to create 'equiponderado' column
    quantiles_df['equiponderado'] = quantiles_df.mean(axis=1)
    quantiles_df = quantiles_df.set_index(ranked_df.index)
    print('Failed to get returns for:\n',failed_dates)

    return quantiles_df


# Rank data based on multiple factors
@st.cache_data
def multi_factor_ranking(weights_df:pd.DataFrame, data_dict:dict, n_quantiles:int, mask:pd.DataFrame):
    """
    Given a weights dataframe and a dictionary of data dataframes, rank the data based on factor weight and number of quantiles.

    :param weights_df: (dataframe) dataframe containing weights and names of factors
    :param data_dict: (dict) dictionary of dataframes to be ranked
    :param n_quantiles: (int) number of quantiles to create
    :param mask: (dataframe) mask to apply to the data

    :return: final_df (dataframe)
    """

    # Drop factors with 0 weight
    weights_df = weights_df.loc[weights_df.Weight > 0]

    # Create ranked_data_dict and columns_list
    ranked_data_dict = {}
    columns_list = []

    # Iterate over each factor in weights_df, apply mask to the data, 
    # and rank the data based on n_quantiles and its type
    for factor,type_ in zip(weights_df.Factor,weights_df.Type):
        masked_data = apply_mask(data_dict[factor],mask)
        ranked_data = rank_data(masked_data,n_quantiles, type_)
        ranked_data_dict[factor] = ranked_data
        columns_list.append(ranked_data.columns)

    # Get common columns between ranked data of different factors
    common_columns = columns_list[0]
    for i in columns_list[1:]:
        common_columns = common_columns.intersection(i)

    # Create dictionary of ranked data weighted by factor weight
    weighted_df_dict = {}
    for factor,ranked_df in ranked_data_dict.items():
        weight = float(weights_df.loc[weights_df.Factor==factor].Weight)
        weighted_df_dict[factor] = ranked_df[common_columns]*weight

    # Iterate over each date and create final_df
    dates = weighted_df_dict[list(weighted_df_dict.keys())[0]].index
    final_df_list = []
    failed_dates = []
    for i, date in enumerate(dates):
        summing_list = []
        try:
            for factor_df in weighted_df_dict.values():
                summing_list.append(factor_df.loc[date])
        except KeyError:
            failed_dates.append(i)
            continue
        final_df_list.append(sum(summing_list)/len(summing_list))

    # Combine final dataframes into a single dataframe
    return pd.DataFrame(final_df_list,index=dates.delete(failed_dates),columns=common_columns)


# Apply mask to the data
@st.cache_data
def apply_mask(df:pd.DataFrame,mask:pd.DataFrame=None):
    """
    Apply mask to the given dataframe.

    :param df: (dataframe) dataframe to apply mask to
    :param mask: (dataframe) mask to apply

    :return: df (dataframe)
    """

    # Return dataframe without mask if no mask is provided
    if mask is None:
        warn("No mask was provided.")
        return df

    # Convert mask to boolean and get common rows and columns between mask and dataframe
    mask = mask.astype(bool)
    common_columns = sorted(list(set(df.columns) & set(mask.columns)))
    common_rows = sorted(list(set(df.index) & set(mask.index)))

    # Return dataframe with applied mask
    df = df.loc[common_rows,common_columns]
    mask = mask.loc[common_rows,common_columns]
    return df.where(mask)


# Read and sort data based on file extension
@st.cache_data
def read_and_sort_data(filepath):
    """
    Given a file path, read and sort data based on file extension.

    :param filepath: (string) path to data file

    :return: df (dataframe)
    """

    # Get file extension and read data based on file type
    extension = os.path.splitext(filepath)[-1].lower()
    if os.path.isfile(filepath):
        if extension == '.csv':
            df = pd.read_csv(filepath,index_col=0,sep=',',decimal='.')
        elif extension in ('.xlsx','.xlsm'):
            df = pd.read_excel(filepath,index_col=0,decimal='.')
        else:
            raise IOError(f'Unsupported filetype: [{extension}]. Must be in [".csv", ".xlsx", ".xlsm"]')

        # Convert dataframe values to numeric type, convert index to datetime type, and sort the dataframe by index
        df = df.apply(pd.to_numeric)
        df = df.set_index(pd.to_datetime(df.index)).sort_index()
        return df


# Check directory for filename and return new filename if necessary 
def check_dir_and_change_filename(filename,dir_fp,ext):
    if f'{filename}{ext}' in os.listdir(dir_fp):
        i = 0
        while f'{filename}{ext}' in os.listdir(dir_fp):
            filename = f'{filename.split("(")[0]}({i})'
            i += 1
        st.warning(f'File already existed. Saving as:{filename}')
    return filename