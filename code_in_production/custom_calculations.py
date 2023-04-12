import pandas as pd
import ta

from app_functions import apply_mask


def rate_of_change(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    rate_of_change(df: pd.DataFrame, period: int) -> pd.DataFrame
    Calculates the rate of change for a given DataFrame over a specified period.

    :param df: The input DataFrame.
    :param period: The number of periods over which to calculate the rate of change.
    :return: A DataFrame containing the rate of change values.
    """
    pct_change_df = df.pct_change(period, limit=1)
    return pct_change_df


rate_of_change.__doc__ = "rate_of_change(df: pd.DataFrame, period: int) -> pd.DataFrame\n\nCalculates the rate of change for a given DataFrame over a specified period.\n\n:param df: The input DataFrame.\n:param period: The number of periods over which to calculate the rate of change.\n:return: A DataFrame containing the rate of change values."


def rsi(df: pd.DataFrame, window) -> pd.DataFrame:
    """
    rsi(df: pd.DataFrame, window) -> pd.DataFrame
    Calculates the Relative Strength Index (RSI) for a given DataFrame.

    :param df: The input DataFrame.
    :param window: The number of periods to use when calculating the RSI.
    :return: A DataFrame containing the RSI values.
    """
    rsi_df = df.apply(ta.momentum.rsi, axis=0, window=window, fillna=False)
    return rsi_df


rsi.__doc__ = "rsi(df: pd.DataFrame, window) -> pd.DataFrame\n\nCalculates the Relative Strength Index (RSI) for a given DataFrame.\n\n:param df: The input DataFrame.\n:param window: The number of periods to use when calculating the RSI.\n:return: A DataFrame containing the RSI values."


def simple_ma(df, rolling_window) -> pd.DataFrame:
    """
    simple_ma(df, rolling_window) -> pd.DataFrame
    Calculates the Simple Moving Average (SMA) for a given DataFrame.

    :param df: The input DataFrame.
    :param rolling_window: The number of periods to use when calculating the SMA.
    :return: A DataFrame containing the SMA values.
    """
    sma_df = df.rolling(rolling_window).mean()
    return sma_df


simple_ma.__doc__ = "simple_ma(df, rolling_window) -> pd.DataFrame\n\nCalculates the Simple Moving Average (SMA) for a given DataFrame.\n\n:param df: The input DataFrame.\n:param rolling_window: The number of periods to use when calculating the SMA.\n:return: A DataFrame containing the SMA values."


def exponential_ma(df: pd.DataFrame, rolling_window) -> pd.DataFrame:
    """
    exponential_ma(df: pd.DataFrame, rolling_window) -> pd.DataFrame
    Calculates the Exponential Moving Average (EMA) for a given DataFrame.

    :param df: The input DataFrame.
    :param rolling_window: The number of periods to use when calculating the EMA.
    :return: A DataFrame containing the EMA values.
    """
    ema_df = df.ewm(span=rolling_window).mean()
    return ema_df


exponential_ma.__doc__ = "exponential_ma(df: pd.DataFrame, rolling_window) -> pd.DataFrame\n\nCalculates the Exponential Moving Average (EMA) for a given DataFrame.\n\n:param df: The input DataFrame.\n:param rolling_window: The number of periods to use when calculating the EMA.\n:return: A DataFrame containing the EMA values."


mask = None
def beta(df: pd.DataFrame, window_size_months: int) -> pd.DataFrame:
    """beta(df: pd.DataFrame, window_size_months:int) -> pd.DataFrame

    Calculates the beta for a given DataFrame.

    :param df: The input DataFrame.
    :param window_size_months: The number of months to use when calculating beta.

    Note that this function uses a global variable `mask` that must be defined in the app or globals dict of the eval function. 
    Be very careful when using this function.

    Example usage:
    calcs.mask = mask

    :return: A DataFrame containing the beta values.
    """

    global mask  # be very careful

    masked_monthly_prices = apply_mask(df, mask)  # mask is a global variable that must be defined in the app or globals dict of the eval function
    market = masked_monthly_prices.mean(axis=1)

    returns = df.pct_change(limit=1)  # Calculate monthly returns
    market_returns = market.pct_change(limit=1)

    covariance = returns.rolling(window_size_months).cov(market_returns)  # Calculate rolling covariance with market
    variance = market_returns.rolling(window_size_months).var()  # Calculate rolling variance of market

    beta = covariance.div(variance, axis=0)  # Calculate rolling beta
    return beta


beta.__doc__ = "beta(df: pd.DataFrame, window_size_months: int) -> pd.DataFrame\n\nCalculates the beta for a given DataFrame.\n\n:param df: The input DataFrame.\n:param window_size_months: The number of months to use when calculating beta.\n\n :return: A DataFrame containing the beta values."""