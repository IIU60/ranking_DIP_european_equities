import pandas as pd
import json
import datetime as dt
from dateutil.relativedelta import relativedelta

def create_df_mask_from_json(json_fp,output_fp):
    with open(fr'{json_fp}') as file:
        daily_filter = json.load(file)
    df_filter = pd.DataFrame.from_dict(daily_filter,orient='index').stack()
    mask = pd.crosstab(df_filter.index.get_level_values(0),df_filter).astype(bool)
    mask.to_csv(fr'{output_fp}')
    return mask


def create_dates_list(type_=['days','months'], start_date=(2000,1,1), end_date=(2023,1,1), as_str=False, only_weekdays=False):
    start_date = dt.date(start_date[0],start_date[1],start_date[2])
    end_date = dt.date(end_date[0],end_date[1],end_date[2])
    dates = [start_date]
    i = 0

    if type_=='days':
        while (date := start_date + relativedelta(days=i+1)) <= end_date:
            dates.append(date)
            i +=1
    if type_=='months':
        while (date := start_date + relativedelta(months=i+1)) <= end_date:
            dates.append(date)
            i +=1
    
    if only_weekdays==True:
        weekday0 = dates[0].weekday()
        saturdays = dates[5-weekday0::7]
        sundays = dates[6-weekday0::7]
        dates = set(dates) - set(saturdays) - set(sundays)
        dates = sorted(list(dates))

    if as_str==True:
        return list(map(str,dates))
    
    return dates