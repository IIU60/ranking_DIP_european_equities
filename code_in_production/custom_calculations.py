import pandas as pd
import ta

from app_functions import apply_mask # figure out best way to apply mask to calculations

def rate_of_change(df:pd.DataFrame,period:int):
    pct_change_df = df.pct_change(period,limit=1)
    return pct_change_df


def rsi(df:pd.DataFrame,window):
    rsi_df = df.apply(ta.momentum.rsi,axis=0,window=window,fillna=False)
    return rsi_df


def simple_ma(df, rolling_window):
    sma_df = df.rolling(rolling_window).mean()
    return sma_df


def exponential_ma(df:pd.DataFrame, rolling_window):
    ema_df = df.ewm(span=rolling_window).mean()
    return ema_df

mask = None
def beta(df:pd.DataFrame, window_size_months:int):

    global mask # be very careful

    masked_monthly_prices = apply_mask(df,mask) # mask is a global variable that must be defined in the app or globals dict of the eval function: calcs.mask = mask
    market = masked_monthly_prices.mean(axis=1)
    
    returns = df.pct_change(limit=1) # Calculate monthly returns
    market_returns = market.pct_change(limit=1)

    covariance = returns.rolling(window_size_months).cov(market_returns) # Calculate rolling covariance with market
    variance = market_returns.rolling(window_size_months).var() # Calculate rolling variance of market

    beta = covariance.div(variance,axis=0) # Calculate rolling beta
    return beta