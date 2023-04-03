import pandas as pd
import ta

import utils # figure out best way to apply mask to calculations

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


def beta(monthly_prices:pd.DataFrame, monthly_mask:pd.DataFrame, window_size_months:int):

    masked_monthly_prices = utils.apply_mask(monthly_prices,monthly_mask) # should probably pass masked monthly prices directly instead of calculating inside the function
    market = masked_monthly_prices.mean(axis=1)

    window = window_size_months # Rolling window size in months
    
    df = monthly_prices.pct_change(limit=1) # Calculate monthly returns
    market_returns = market.pct_change(limit=1)

    covariance = df.rolling(window).cov(market_returns) # Calculate rolling covariance with market
    variance = market_returns.rolling(window).var() # Calculate rolling variance of market

    beta = covariance.div(variance,axis=0) # Calculate rolling beta
    return beta