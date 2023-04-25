import eikon as ek
from tqdm import tqdm
import pandas as pd
import utils
import os

ek.set_app_key('89915a3b58874e1599870c6ecc45d6edd6344f8c')

def vertical_download(field_name:str,field_function,instruments_list,parameters):
    
    fields = [field_function,f'{field_function}.date']

    print(f'Downloading {field_name}')

    fails = []
    dfs_list = []
    
    for instrument in tqdm(instruments_list):
        try:
            df, err = ek.get_data(instrument, fields, parameters)
            df.to_csv(f"{field_name}/raw_data/{instrument}.csv")
            dfs_list.append(df)
        except Exception as x:
            fails.append(instrument)
            print(x)

    for instrument in tqdm(fails):
        try:
            df, err = ek.get_data(instrument, fields, parameters)
            df.to_csv(f"{field_name}/raw_data/{instrument}.csv")
            dfs_list.append(df)
        except Exception as x:
            print(f'Failed twice for {instrument}',x)

    return dfs_list


def dfs_list_from_dir(dir_fp):
    dfs_list = []
    
    for i in os.listdir(dir_fp):
        dfs_list.append(pd.read_csv(os.path.join(dir_fp,i),index_col=0))
    return dfs_list


def reconstruction(field_name:str,dfs_list:list): # Start date and end date

    concated_df = pd.concat(dfs_list)

    processed_df = concated_df.dropna().drop_duplicates()
    processed_df['Date'] = processed_df.Date.apply(lambda x: x[:10])

    pivoted_df = processed_df.pivot(index='Date',columns='Instrument',values=list(set(processed_df.columns)-set(['Date','Instrument']))[0])

    days_list = utils.create_dates_list('days',as_str=True)
    months_list = utils.create_dates_list('months',as_str=True)
    dates_dict = {}
    for i in days_list:
        dates_dict[i] = pd.NA
    dates_dict.update(pivoted_df.T.to_dict())

    complete_dates_df = pd.DataFrame(dates_dict).T.sort_index()
    filled_df = complete_dates_df.fillna(method='ffill',limit=7).loc[months_list]

    return filled_df


def download_indicators(fields_list:list,instruments_list:list,parameters:dict,saving_directory_fp:str):
    
    os.chdir(fr'{saving_directory_fp}')
    
    for field_function in fields_list:
        field_name = field_function.split('.')[-1]
        i = 0
        while i != -1:
            try:
                os.mkdir(field_name)
                i = -1
            except FileExistsError:
                field_name = f'{field_name.split("(")[0]}({i})'
                i += 1
        os.mkdir(field_name+'/raw_data')

        dfs_list = vertical_download(field_name,field_function,instruments_list,parameters)
        try:
            complete_df = reconstruction(field_name,dfs_list) # star_date and end_date
        except ValueError as e:
            print(e,'\nRetrying...')
            dfs_list = dfs_list_from_dir(fr'{field_name}/raw_data')
            complete_df = reconstruction(field_name,dfs_list)
            print('\nSuccessful!')
        
        complete_df.to_csv(f'{field_name}/{field_name}.csv')
        
        
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