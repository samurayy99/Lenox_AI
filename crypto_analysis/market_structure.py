import pandas as pd
import numpy as np

def analyze_market_structure(ohlc: pd.DataFrame, join_consecutive: bool = False) -> dict:
    """Comprehensive market structure analysis with fair value gaps."""
    fvg_result = identify_fair_value_gap(ohlc, join_consecutive)
    return {
        "FVG": fvg_result
    }

def identify_fair_value_gap(ohlc: pd.DataFrame, join_consecutive: bool = False) -> pd.DataFrame:
    """Identify Fair Value Gaps (FVG) in the given OHLC data."""
    fvg = np.where(
        (ohlc["high"].shift(1) < ohlc["low"].shift(-1)) | (ohlc["low"].shift(1) > ohlc["high"].shift(-1)),
        np.where(ohlc["close"] > ohlc["open"], 1, -1),
        np.nan
    )

    top = np.where(
        ~np.isnan(fvg),
        np.where(ohlc["close"] > ohlc["open"], ohlc["low"].shift(-1), ohlc["low"].shift(1)),
        np.nan
    )

    bottom = np.where(
        ~np.isnan(fvg),
        np.where(ohlc["close"] > ohlc["open"], ohlc["high"].shift(1), ohlc["high"].shift(-1)),
        np.nan
    )

    mitigated_index = np.zeros(len(ohlc), dtype=np.int32)
    for i in np.where(~np.isnan(fvg))[0]:
        mask = np.zeros(len(ohlc), dtype=np.bool_)
        if fvg[i] == 1:
            mask = ohlc["low"][i + 2:] <= top[i]
        elif fvg[i] == -1:
            mask = ohlc["high"][i + 2:] >= bottom[i]
        if np.any(mask):
            j = np.argmax(mask) + i + 2
            mitigated_index[i] = j

    mitigated_index = np.where(np.isnan(fvg), np.nan, mitigated_index)

    return pd.DataFrame({
        "FVG": fvg,
        "Top": top,
        "Bottom": bottom,
        "MitigatedIndex": mitigated_index
    })
