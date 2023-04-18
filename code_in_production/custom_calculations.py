import pandas as pd
import ta

from app_functions import apply_mask


def rate_of_change(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    rate_of_change(df: DataFrame, period: int) -> DataFrame

    Calculate the rate of change of a DataFrame.

    This function calculates the percentage change between the current and a prior element in a DataFrame, at a distance of [period] rows.

    Parameters:
    df (DataFrame): The input DataFrame.
    period (int): The lookback period from which to calculate percent change.

    Returns:
    DataFrame: A DataFrame containing the rate of change.
    """
    pct_change_df = df.pct_change(period, limit=1)
    return pct_change_df


def rsi(df: pd.DataFrame, window) -> pd.DataFrame:
    """
    rsi(df: DataFrame, window: int) -> DataFrame

    Calculate the relative strength index (RSI) of a DataFrame.

    This function calculates the RSI of a DataFrame using a specified window size.

    Parameters:
    df (DataFrame): The input DataFrame.
    window (int): The size of the rolling window. It includes the current row, i.e.: if you want 1 month RSI you should use window=2 (current month and that prior).

    Returns:
    DataFrame: A DataFrame containing the RSI.
    """
    rsi_df = df.apply(ta.momentum.rsi, axis=0, window=window, fillna=False)
    return rsi_df


def simple_ma(df, rolling_window) -> pd.DataFrame:
    """
    simple_ma(df: DataFrame, rolling_window: int) -> DataFrame

    Calculate the simple moving average (SMA) of a DataFrame.

    This function calculates the SMA of a DataFrame using a specified rolling window size.

    Parameters:
    df (DataFrame): The input DataFrame.
    rolling_window (int): The size of the rolling window. It includes the current row, i.e.: if you want 1 month SMA you should use rolling_window=2 (current month and that prior).

    Returns:
    DataFrame: A DataFrame containing the SMA.
    """
    sma_df = df.rolling(rolling_window).mean()
    return sma_df


def exponential_ma(df: pd.DataFrame, rolling_window) -> pd.DataFrame:
    """
    exponential_ma(df: DataFrame, rolling_window: int) -> DataFrame

    Calculate the exponential moving average (EMA) of a DataFrame.

    This function calculates the EMA of a DataFrame using a specified rolling window size.

    Parameters:
    df (DataFrame): The input DataFrame.
    rolling_window (int): The size of the rolling window. It includes the current row, i.e.: if you want 1 month EMA you should use rolling_window=2 (current month and that prior).

    Returns:
    DataFrame: A DataFrame containing the EMA.
    """
    ema_df = df.ewm(span=rolling_window).mean()
    return ema_df


mask = None
def beta(df: pd.DataFrame, window_size: int) -> pd.DataFrame:
    """
    beta(df: DataFrame, window_size_months: int) -> DataFrame

    Calculate the beta of a DataFrame.

    This function calculates the beta of a DataFrame using a specified window size.

    Parameters:
    df (DataFrame): The input DataFrame.
    window_size (int): The size of the rolling window. It includes the current row, i.e.: if you want 1 month beta you should use rolling_window=2 (current month and that prior).

    Returns:
    DataFrame: A DataFrame containing the beta.
    """
    global mask  # be very careful

    masked_monthly_prices = apply_mask(df, mask)  # mask is a global variable that must be defined in the app or globals dict of the eval function
    market = masked_monthly_prices.mean(axis=1)

    returns = df.pct_change(limit=1)  # Calculate monthly returns
    market_returns = market.pct_change(limit=1)

    covariance = returns.rolling(window_size).cov(market_returns)  # Calculate rolling covariance with market
    variance = market_returns.rolling(window_size).var()  # Calculate rolling variance of market

    beta = covariance.div(variance, axis=0)  # Calculate rolling beta
    return beta


def rolling_volatility(df:pd.DataFrame, window_size:int):
    """
    rolling_volatility(df: DataFrame, window_size: int) -> DataFrame

    Calculate the rolling volatility of a DataFrame.

    This function calculates the rolling standard deviation of a DataFrame using a specified window size.

    Parameters:
    df (DataFrame): The input DataFrame.
    window_size (int): The size of the rolling window. It includes the current row, i.e.: if you want 1 month rolling volatility you should use rolling_window=2 (current month and that prior).

    Returns:
    DataFrame: A DataFrame containing the rolling standard deviation.
    """
    std_df = df.rolling(window_size).std()
    return std_df