import eikon as ek
from tqdm import tqdm
import pandas as pd
import utils
import os

from dotenv import load_dotenv; load_dotenv(r'..\.env') #load environment variables from .env file

#dictionary of known frequencies
frequencies_dict = {
    'yearly' : ['AY', 'AQ','Y', 'Q', 'FY', 'FS', 'FH', 'FQ', 'FI', 'CY', 'CQ', 'CS', 'CH', 'F'], 
    'weekly' : ['AW', 'CW', 'W'],
    'daily' : ['C', 'D', 'NA', 'WD'],
    'monthly' : ['AM', 'CM', 'M']
}

#function to download data for a specified field, using the Eikon API
def vertical_download(field_name:str, field_function:str, instruments_list:list, parameters:dict ,saving_directory_fp:str,make_new_dir:bool=True):
    
    ek.set_app_key(os.environ['EIKON_APP_KEY']) #set Eikon API key
    if make_new_dir==True:    
        i = 0
        while i != -1: #create unique directory for field data, even if one with the same name already exists
            try:
                dir_to_save = os.path.join(saving_directory_fp, field_name)
                os.mkdir(dir_to_save)
                i = -1
            except FileExistsError:
                field_name = f'{field_name.split("(")[0]}({i})'
                i += 1
        raw_data_dir_fp = dir_to_save + '/raw_data'        
        os.mkdir(raw_data_dir_fp)
    else:
        raw_data_dir_fp = saving_directory_fp
    fields = [field_function,f'{field_function}.date']

    print(f'Downloading {field_name}')

    fails = []
    dfs_list = [] #list to store dataframes for each instrument

    #iterate through list of instruments, downloading data and saving to file
    for instrument in tqdm(instruments_list):
        try:
            df, err = ek.get_data(instrument, fields, parameters) #get data for instrument and chosen fields
        except Exception:
            fails.append(instrument)
            continue
        if err is not None:
            fails.append(instrument)
            continue
        df.to_csv(f"{raw_data_dir_fp}/{instrument}.csv") #save data to CSV file
        dfs_list.append(df)

    #retry any failed downloads
    if fails:
        print('Retrying fails:')
        for instrument in tqdm(fails[:]):
            try:
                df, err = ek.get_data(instrument, fields, parameters)
            except Exception:
                continue
            if err is not None:
                continue
            fails.remove(instrument)
            df.to_csv(f"{raw_data_dir_fp}/{instrument}.csv")
            dfs_list.append(df)
        print(f'Failed twice for: {len(fails)}\n{fails}\n')

    return dfs_list, field_name


#function to create a list of dataframes from CSV files in a specified directory
def dfs_list_from_dir(dir_fp:str):
    dfs_list = []
    for i in os.listdir(dir_fp):
        dfs_list.append(pd.read_csv(os.path.join(dir_fp,i), index_col=0))
    return dfs_list


#function to reconstruct a complete dataframe from a list of dataframes with missing values,
#using fill-forward interpolation up to 7 days of data
def reconstruction(dfs_list:list, start_date:tuple, end_date:tuple, desired_type_of_dates:str, day_of_week:int=None):
    types_of_dates = ['daily','weekly','first_of_month','monthly','yearly'] #list of known types of dates
    if desired_type_of_dates not in types_of_dates:
        raise ValueError('type_of_date: %s is not in %s'% (desired_type_of_dates,types_of_dates))
    
    concated_df = pd.concat(dfs_list) #concatenate dataframes into one

    processed_df = concated_df.replace(['NaN',''], pd.NA) #replace NaN and empty strings with pandas NA
    processed_df = processed_df.dropna(how='all', axis=1).dropna().drop_duplicates(subset=['Date','Instrument']) #drop rows with NA or duplicate values
    processed_df['Date'] = processed_df.Date.apply(lambda x: x[:10]) #extract date from timestamp column

    pivoted_df = processed_df.pivot(index='Date', columns='Instrument', values=list(set(processed_df.columns)-set(['Date','Instrument']))[0]) #pivot table to rearrange instrument data by date

    days_list = utils.create_dates_list('daily', start_date=start_date, end_date=end_date, as_str=True) #create list of all days in date range
    
    #determine desired dates based on desired type of dates and other parameters
    if desired_type_of_dates == 'first_of_month':
        selection_of_dates = utils.create_dates_list('months',start_date=start_date, end_date=end_date, as_str=True)
    elif desired_type_of_dates in ['monthly','yearly']:
        selection_of_dates = utils.dates_list_last_day_of_month(start_date, end_date, as_str=True)
    elif desired_type_of_dates == 'daily':
        selection_of_dates = days_list
    elif desired_type_of_dates == 'weekly':
        selection_of_dates = utils.create_dates_list('weekly', start_date, end_date, as_str=True, day_of_week=day_of_week)
    
    dates_dict = {}
    for i in days_list:
        dates_dict[i] = pd.NA
    dates_dict.update(pivoted_df.T.to_dict())
    complete_dates_df = pd.DataFrame(dates_dict).T.sort_index() #create a dataframe with desired dates but missing values for instruments not found in original dataframes
    
    filled_df = complete_dates_df.fillna(method='ffill', limit=7) #fill missing values using a fill-forward method
    
    final_df = filled_df.loc[selection_of_dates] #selecting the desired dates frequency

    if desired_type_of_dates == 'yearly': #fill any remaining gaps in extra-monthly data
        final_df = final_df.fillna(method='ffill', limit=12)

    final_df = final_df.apply(pd.to_numeric) #format dataframe to contain only numeric values

    return final_df


#function to determine the frequency of data, based on the freq parameter and the frequencies_dict
def find_freq(freq:str, frequencies_dict:dict):
    for key, freqs_list in frequencies_dict.items():
        if freq in freqs_list:
            return key
    raise KeyError(f'{freq} not in the known dict of frequencies')


#main function to download and process data for specified fields and instruments, saving to CSV files in a specified directory
#using fill-forward interpolation for up to 12 months for extra-monthly data frequencies
def download_indicators(fields_list:list, instruments_list:list, parameters:dict, saving_directory_fp:str):
    
    start_date = tuple(map(int,parameters.get('SDate').split('-'))) #parse start date parameter
    end_date = tuple(map(int,parameters.get('EDate').split('-'))) #parse end date parameter
    freq = parameters.get('Frq') #parse frequency parameter
    
    data_dict = {} #dictionary to store resulting dataframes for each field

    for field_function in fields_list:

        field_name = field_function.split('.')[-1]
        
        desired_type_of_dates = find_freq(freq, frequencies_dict) #determine desired type of dates based on frequency parameter
        dfs_list, dir_name = vertical_download(field_name, field_function, instruments_list, parameters, saving_directory_fp) #download data for field and instruments
        complete_df = reconstruction(dfs_list=dfs_list, start_date=start_date, end_date=end_date, desired_type_of_dates=desired_type_of_dates) #reconstruct complete dataframe from downloaded data
        
        complete_df.to_csv(f'{os.path.join(saving_directory_fp,dir_name,field_name)}.csv') #save complete dataframe to CSV file
        
        data_dict[field_name] = complete_df
    
    return data_dict


#function to identify an incomplete download from a 'raw_data' directory, download the remanining files, and call reconstruction in the same way 'download_idnicators'does
def continue_download(field_function:str, raw_data_dir_fp:str, full_instruments_list:list, parameters:dict):
    already_downloaded_names = set(map(lambda x:x.strip('.csv'),os.listdir(raw_data_dir_fp)))
    instruments_list = list(set(full_instruments_list)-already_downloaded_names)

    already_downloaded_dfs_list = dfs_list_from_dir(raw_data_dir_fp)
    start_date = tuple(map(int,parameters.get('SDate').split('-'))) #parse start date parameter
    end_date = tuple(map(int,parameters.get('EDate').split('-'))) #parse end date parameter
    freq = parameters.get('Frq') #parse frequency parameter

    field_name = field_function.split('.')[-1]

    desired_type_of_dates = find_freq(freq, frequencies_dict) #determine desired type of dates based on frequency parameter
    
    dfs_list, _ = vertical_download(field_name, field_function, instruments_list, parameters, raw_data_dir_fp, make_new_dir=False) #download data for field and instruments
    dfs_list.extend(already_downloaded_dfs_list)

    complete_df = reconstruction(dfs_list=dfs_list, start_date=start_date, end_date=end_date, desired_type_of_dates=desired_type_of_dates) #reconstruct complete dataframe from downloaded data
    
    complete_df.to_csv(f'{raw_data_dir_fp}/../{field_name}.csv') #save complete dataframe to CSV file
