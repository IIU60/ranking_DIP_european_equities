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
    start_date = dt.date(*start_date)
    end_date = dt.date(*end_date)
    
    dates = [start_date]
    i = 0
    if type_=='days':
        while (date := start_date + relativedelta(days=i+1)) <= end_date:
            dates.append(date)
            i +=1
    elif type_=='months':
        while (date := start_date + relativedelta(months=i+1)) <= end_date:
            dates.append(date)
            i +=1
    
    if only_weekdays==True:
        if type_=='days':
            weekday0 = dates[0].weekday()
            saturdays = dates[5-weekday0::7]
            sundays = dates[6-weekday0::7]
            dates = set(dates) - set(saturdays) - set(sundays)
            dates = sorted(list(dates))
        else:
            raise ValueError('can only calculate weekdays if type_ is daily')

    if as_str==True:
        return list(map(str,dates))
    
    return dates

def dates_list_last_day_of_month(start_date=(2000,1,1),end_date=(2023,4,26)):

    start_date = dt.date(*start_date)
    end_date = dt.date(*end_date)

    def last_day_of_month(year, month):
        next_month = dt.date(year, month, 1) + dt.timedelta(days=32)
        return next_month.replace(day=1) - dt.timedelta(days=1)
    
    last_days = [date for year in range(start_date.year,end_date.year+1) for month in range(1,13) if (start_date < (date:=last_day_of_month(year,month)) and date < end_date)]

    return last_days

