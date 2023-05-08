import eikon as ek
from tqdm import tqdm
import pandas as pd
import utils
import os

from dotenv import load_dotenv; load_dotenv(r'..\.env') #load environment variables from .env file
ek.set_app_key(os.environ['EIKON_APP_KEY']) #set Eikon API key

#dictionary of known frequencies
frequencies_dict = {
    'yearly' : ['AY', 'AQ','Y', 'Q', 'FY', 'FS', 'FH', 'FQ', 'FI', 'CY', 'CQ', 'CS', 'CH', 'F'], 
    'weekly' : ['AW', 'CW', 'W'],
    'daily' : ['C', 'D', 'NA', 'WD'],
    'monthly' : ['AM', 'CM', 'M']
}

#function to download data for a specified field, using the Eikon API
def vertical_download(field_name:str,field_function,instruments_list,parameters):
    
    i = 0
    while i != -1: #create unique directory for field data, even if one with the same name already exists
        try:
            os.mkdir(field_name)
            i = -1
        except FileExistsError:
            field_name = f'{field_name.split("(")[0]}({i})'
            i += 1
    os.mkdir(field_name+'/raw_data')

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
        df.to_csv(f"{field_name}/raw_data/{instrument}.csv") #save data to CSV file
        dfs_list.append(df)

    #retry any failed downloads
    if not fails:
        print('Retrying fails:')
        for instrument in tqdm(fails[:]):
            try:
                df, err = ek.get_data(instrument, fields, parameters)
                fails.remove(instrument)
            except Exception:
                continue
            df.to_csv(f"{field_name}/raw_data/{instrument}.csv")
            dfs_list.append(df)
        print('Failed twice for:\n',fails)

    return dfs_list


#function to create a list of dataframes from CSV files in a specified directory
def dfs_list_from_dir(dir_fp):
    dfs_list = []
    for i in os.listdir(dir_fp):
        dfs_list.append(pd.read_csv(os.path.join(dir_fp,i),index_col=0))
    return dfs_list


#function to reconstruct a complete dataframe from a list of dataframes with missing values,
#using fill-forward interpolation up to 7 days of data
def reconstruction(dfs_list:list,start_date:tuple=(2000,1,1),end_date:tuple=(2023,1,1),desired_type_of_dates:str='monthly', day_of_week:int=None):
    types_of_dates = ['daily','weekly','first_of_month','monthly','yearly'] #list of known types of dates
    if desired_type_of_dates not in types_of_dates:
        raise ValueError('type_of_date: %s is not in %s'% (desired_type_of_dates,types_of_dates))
    
    concated_df = pd.concat(dfs_list) #concatenate dataframes into one

    processed_df = concated_df.replace(['NaN',''],pd.NA) #replace NaN and empty strings with pandas NA
    processed_df = processed_df.dropna().drop_duplicates() #drop rows with NA or duplicate values
    processed_df['Date'] = processed_df.Date.apply(lambda x: x[:10]) #extract date from timestamp column

    pivoted_df = processed_df.pivot(index='Date',columns='Instrument',values=list(set(processed_df.columns)-set(['Date','Instrument']))[0]) #pivot table to rearrange instrument data by date

    days_list = utils.create_dates_list('daily',start_date=start_date,end_date=end_date,as_str=True) #create list of all days in date range
    
    #determine desired dates based on desired type of dates and other parameters
    if desired_type_of_dates == 'first_of_month':
        selection_of_dates = utils.create_dates_list('months',start_date=start_date,end_date=end_date,as_str=True)
    elif desired_type_of_dates in ['monthly','yearly']:
        selection_of_dates = utils.dates_list_last_day_of_month(start_date,end_date,as_str=True)
    elif desired_type_of_dates == 'daily':
        selection_of_dates = days_list
    elif desired_type_of_dates == 'weekly':
        selection_of_dates = utils.create_dates_list('weekly',start_date,end_date,as_str=True,day_of_week=day_of_week)
    
    dates_dict = {}
    for i in days_list:
        dates_dict[i] = pd.NA
    dates_dict.update(pivoted_df.T.to_dict())
    complete_dates_df = pd.DataFrame(dates_dict).T.sort_index() #create a dataframe with desired dates but missing values for instruments not found in original dataframes
    
    filled_df = complete_dates_df.fillna(method='ffill',limit=7).loc[selection_of_dates] #fill missing values using a fill-forward method and selecting the desired dates frequency
    filled_df = filled_df.apply(pd.to_numeric) #format dataframe to contain only numeric values

    return filled_df


#function to determine the frequency of data, based on the freq parameter and the frequencies_dict
def find_freq(freq,frequencies_dict):
    for key, freqs_list in frequencies_dict.items():
        if freq in freqs_list:
            return key
    raise KeyError(f'{freq} not in the known dict of frequencies')


#main function to download and process data for specified fields and instruments, saving to CSV files in a specified directory
#using fill-forward interpolation for up to 12 months for extra-monthly data frequencies
def download_indicators(fields_list:list,instruments_list:list,parameters:dict,saving_directory_fp:str):
    
    os.chdir(fr'{saving_directory_fp}')

    start_date = tuple(map(int,parameters.get('SDate').split('-'))) #parse start date parameter
    end_date = tuple(map(int,parameters.get('EDate').split('-'))) #parse end date parameter
    freq = parameters.get('Frq') #parse frequency parameter
    
    data_dict = {} #dictionary to store resulting dataframes for each field

    for field_function in fields_list:

        field_name = field_function.split('.')[-1]
        
        desired_type_of_dates = find_freq(freq,frequencies_dict) #determine desired type of dates based on frequency parameter
        dfs_list = vertical_download(field_name,field_function,instruments_list,parameters) #download data for field and instruments
        complete_df = reconstruction(dfs_list=dfs_list,start_date=start_date,end_date=end_date,desired_type_of_dates=desired_type_of_dates) #reconstruct complete dataframe from downloaded data
        
        if freq in frequencies_dict['yearly']: #fill any remaining gaps in extra-monthly data
            complete_df = complete_df.fillna(method='ffill',limit=12)
        
        complete_df.to_csv(f'{field_name}/{field_name}.csv') #save complete dataframe to CSV file
        
        data_dict[field_name] = complete_df
    
    return data_dict
