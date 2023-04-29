import eikon as ek
from tqdm import tqdm
import pandas as pd
import utils
import os

from dotenv import load_dotenv; load_dotenv(r'..\.env')
ek.set_app_key(os.environ['EIKON_APP_KEY'])


frequencies_dict = {
    'yearly' : ['AY', 'AQ','Y', 'Q', 'FY', 'FS', 'FH', 'FQ', 'FI', 'CY', 'CQ', 'CS', 'CH', 'F'],
    'weekly' : ['AW', 'CW', 'W'],
    'daily' : ['C', 'D', 'NA', 'WD'],
    'monthly' : ['AM', 'CM', 'M']
}


def vertical_download(field_name:str,field_function,instruments_list,parameters):
    
    i = 0
    while i != -1:
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
    dfs_list = []
    
    for instrument in tqdm(instruments_list):
        try:
            df, err = ek.get_data(instrument, fields, parameters)
        except Exception:
            fails.append(instrument)
            continue
        df.to_csv(f"{field_name}/raw_data/{instrument}.csv")
        dfs_list.append(df)

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


def dfs_list_from_dir(dir_fp):
    dfs_list = []
    for i in os.listdir(dir_fp):
        dfs_list.append(pd.read_csv(os.path.join(dir_fp,i),index_col=0))
    return dfs_list


def reconstruction(dfs_list:list,start_date:tuple=(2000,1,1),end_date:tuple=(2023,1,1),desired_type_of_dates:str='monthly', day_of_week:int=None):
    types_of_dates = ['daily','weekly','first_of_month','monthly','yearly']
    if desired_type_of_dates not in types_of_dates:
        raise ValueError('type_of_date: %s is not in %s'% (desired_type_of_dates,types_of_dates))
    
    concated_df = pd.concat(dfs_list)

    processed_df = concated_df.replace(['NaN',''],pd.NA)
    processed_df = processed_df.dropna().drop_duplicates()
    processed_df['Date'] = processed_df.Date.apply(lambda x: x[:10])

    pivoted_df = processed_df.pivot(index='Date',columns='Instrument',values=list(set(processed_df.columns)-set(['Date','Instrument']))[0])

    days_list = utils.create_dates_list('daily',start_date=start_date,end_date=end_date,as_str=True)
    
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
    complete_dates_df = pd.DataFrame(dates_dict).T.sort_index()
    
    filled_df = complete_dates_df.fillna(method='ffill',limit=7).loc[selection_of_dates]

    return filled_df


def find_freq(freq,frequencies_dict):
    for key, freqs_list in frequencies_dict.items():
        if freq in freqs_list:
            return key
    raise KeyError(f'{freq} not in the known dict of frequencies')


def download_indicators(fields_list:list,instruments_list:list,parameters:dict,saving_directory_fp:str):
    
    os.chdir(fr'{saving_directory_fp}')

    start_date = tuple(map(int,parameters.get('SDate').split('-')))
    end_date = tuple(map(int,parameters.get('EDate').split('-')))
    freq = parameters.get('Frq')
    
    data_dict = {}
    
    for field_function in fields_list:

        field_name = field_function.split('.')[-1]
        
        desired_type_of_dates = find_freq(freq,frequencies_dict)
        dfs_list = vertical_download(field_name,field_function,instruments_list,parameters)
        complete_df = reconstruction(dfs_list=dfs_list,start_date=start_date,end_date=end_date,desired_type_of_dates=desired_type_of_dates)

        if freq in frequencies_dict['yearly']:
            complete_df = complete_df.fillna(method='ffill',limit=12)
        
        complete_df.to_csv(f'{field_name}/{field_name}.csv')
        
        data_dict[field_name] = complete_df
    
    return data_dict
        
        
#def get_data(fields:list,desired_field_name:str):
#
#    str_dates = utils.create_dates_list('months',as_str=True)
#
#    complete_df = pd.DataFrame(columns=['Instrument','Date','CallDate'])
#
#    errors_dict = {}
#
#    for date in tqdm(str_dates,smoothing=0):
#        try:
#            returned_df,err = ek.get_data(f'0#.STOXX({date})',fields=fields,parameters={'SDate':date})
#        except Exception as x:
#            print('failed for '+ date)
#            errors_dict[date] = x
#        else:
#            returned_df['CallDate'] = date
#            complete_df = pd.concat([complete_df,returned_df],axis=0)
#
#    if not not errors_dict:
#        for date in tqdm(list(errors_dict.keys()),smoothing=0):
#            try:
#                returned_df,err = ek.get_data(f'0#.STOXX({date})',fields=fields,parameters={'SDate':date})
#            except Exception as x:
#                print('failed again for '+ date)
#                errors_dict[date] = x
#            else:
#                returned_df['CallDate'] = date
#                complete_df = pd.concat([complete_df,returned_df],axis=0)
#
#    complete_df.to_csv(f'C:/Users/hugo.perezdealbeniz/Desktop/Ranking DIP European Equities/Reuters Eikon/data/raw_data/raw_{desired_field_name}.csv',index=False)
#    
#    complete_df.rename(columns={list(set(complete_df.columns)-set(['Instrument','Date','CallDate']))[0]:desired_field_name},inplace = True)
#
#    pivoted_df = complete_df.pivot(index='CallDate',columns='Instrument', values=desired_field_name)
#    pivoted_df.to_csv(f'C:/Users/hugo.perezdealbeniz/Desktop/Ranking DIP European Equities/Reuters Eikon/data/pivoted_data/pivoted_{desired_field_name}.csv')
#
#    return pivoted_df,errors_dict