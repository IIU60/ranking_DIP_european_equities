"""Utilities for generating synthetic financial datasets for demos."""

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


def _generate_bounded_series(
    rng: np.random.Generator,
    months: int,
    base: float,
    drift: float,
    noise_scale: float,
    lower: Optional[float],
    upper: Optional[float],
) -> np.ndarray:
    """Simulate a mean-reverting series constrained within optional bounds."""
    values = [base]
    for _ in range(1, months):
        new_val = values[-1] + drift + rng.normal(0, noise_scale)
        if lower is not None:
            new_val = max(lower, new_val)
        if upper is not None:
            new_val = min(upper, new_val)
        values.append(new_val)
    return np.array(values)


def _generate_growing_series(
    rng: np.random.Generator,
    months: int,
    base: float,
    monthly_drift: float,
    noise_scale: float,
) -> np.ndarray:
    """Create an exponentially growing series with stochastic shocks."""
    shocks = monthly_drift + rng.normal(0, noise_scale, size=months)
    return base * np.exp(shocks.cumsum())


def generate_sample_financial_data(
    num_stocks: int = 50,
    years: int = 25,
    seed: int = 42,
) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """Create a simulated financial dataset for demonstration purposes."""
    rng = np.random.default_rng(seed)
    months = years * 12
    end_date = pd.Timestamp.today().to_period("M").to_timestamp("M")
    date_index = pd.date_range(end=end_date, periods=months, freq="M")
    tickers = [f"STK{i:03d}" for i in range(1, num_stocks + 1)]

    metric_specs = [
        {
            "name": "ebitda",
            "base_range": (150, 500),
            "annual_drift_range": (0.03, 0.08),
            "noise_scale": 0.06,
            "bounds": (None, None),
            "is_ratio": False,
        },
        {
            "name": "revenue",
            "base_range": (500, 1500),
            "annual_drift_range": (0.04, 0.1),
            "noise_scale": 0.05,
            "bounds": (None, None),
            "is_ratio": False,
        },
        {
            "name": "net_income",
            "base_range": (50, 200),
            "annual_drift_range": (0.02, 0.07),
            "noise_scale": 0.07,
            "bounds": (None, None),
            "is_ratio": False,
        },
        {
            "name": "free_cash_flow",
            "base_range": (40, 180),
            "annual_drift_range": (0.02, 0.08),
            "noise_scale": 0.08,
            "bounds": (None, None),
            "is_ratio": False,
        },
        {
            "name": "eps",
            "base_range": (1.5, 5.0),
            "annual_drift_range": (0.02, 0.06),
            "noise_scale": 0.05,
            "bounds": (None, None),
            "is_ratio": False,
        },
        {
            "name": "operating_margin",
            "base_range": (0.12, 0.28),
            "annual_drift_range": (-0.01, 0.01),
            "noise_scale": 0.01,
            "bounds": (0.05, 0.4),
            "is_ratio": True,
        },
        {
            "name": "debt_to_equity",
            "base_range": (0.6, 1.6),
            "annual_drift_range": (-0.03, 0.02),
            "noise_scale": 0.04,
            "bounds": (0.1, 2.5),
            "is_ratio": True,
        },
        {
            "name": "dividend_yield",
            "base_range": (0.01, 0.04),
            "annual_drift_range": (-0.005, 0.005),
            "noise_scale": 0.01,
            "bounds": (0.0, 0.08),
            "is_ratio": True,
        },
        {
            "name": "pe_ratio",
            "base_range": (12, 25),
            "annual_drift_range": (-0.05, 0.05),
            "noise_scale": 0.1,
            "bounds": (5, 40),
            "is_ratio": True,
        },
        {
            "name": "price_to_book",
            "base_range": (1.0, 3.5),
            "annual_drift_range": (-0.03, 0.04),
            "noise_scale": 0.06,
            "bounds": (0.3, 6.0),
            "is_ratio": True,
        },
    ]

    metric_frames: Dict[str, pd.DataFrame] = {}
    for spec in metric_specs:
        data = []
        for _ in tickers:
            base = rng.uniform(*spec["base_range"])
            annual_drift = rng.uniform(*spec["annual_drift_range"])
            monthly_drift = annual_drift / 12
            if spec["is_ratio"]:
                series = _generate_bounded_series(
                    rng,
                    months,
                    base,
                    monthly_drift,
                    spec["noise_scale"],
                    *spec["bounds"],
                )
            else:
                series = _generate_growing_series(
                    rng,
                    months,
                    base,
                    monthly_drift,
                    spec["noise_scale"],
                )
            data.append(series)
        metric_frames[spec["name"]] = pd.DataFrame(
            np.array(data).T, index=date_index, columns=tickers
        )

    price_data = []
    for _ in tickers:
        start_price = rng.uniform(15, 120)
        annual_return = rng.normal(0.06, 0.04)
        annual_vol = rng.uniform(0.18, 0.35)
        monthly_return = annual_return / 12
        monthly_vol = annual_vol / np.sqrt(12)
        shocks = rng.normal(monthly_return, monthly_vol, size=months)
        series = start_price * np.exp(np.cumsum(shocks))
        price_data.append(series)
    prices_df = pd.DataFrame(np.array(price_data).T, index=date_index, columns=tickers)

    return metric_frames, prices_df
