import eikon as ek
import datetime as dt
import dateutil.relativedelta
import tqdm
import pandas as pd
import utils

def get_data(fields:list,desired_field_name:str):
    
    ek.set_app_key('89915a3b58874e1599870c6ecc45d6edd6344f8c')

    str_dates = utils.create_dates_list('months',as_str=True)

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