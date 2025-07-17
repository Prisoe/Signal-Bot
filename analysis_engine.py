import os
import pandas as pd
import numpy as np
import talib
import mplfinance as mpf
import cv2
from pathlib import Path
from scipy.signal import find_peaks

CHART_DIR = 'temp_charts'
Path(CHART_DIR).mkdir(exist_ok=True)

# helper to clear temp charts
def clear_temp_charts():
    for f in Path(CHART_DIR).glob('*.png'):
        try:
            os.remove(f)
        except OSError:
            pass

# === TA FEATURE EXTRACTION ===
def compute_ta_indicators(df):
    df = df.copy()
    open_ = df['open'].astype(float).values
    high = df['high'].astype(float).values
    low = df['low'].astype(float).values
    close = df['close'].astype(float).values
    volume = df['volume'].astype(float).values
    df['SMA_20'] = talib.SMA(close, timeperiod=20)
    df['TRIX'] = talib.TRIX(close, timeperiod=15)
    df['STOCH_slowk'], df['STOCH_slowd'] = talib.STOCH(high, low, close)
    df['CCI'] = talib.CCI(high, low, close, timeperiod=14)
    df['ULTOSC'] = talib.ULTOSC(high, low, close)
    df['WILLR'] = talib.WILLR(high, low, close, timeperiod=14)
    df['OBV'] = talib.OBV(close, volume)
    df['MFI'] = talib.MFI(high, low, close, volume, timeperiod=14)
    df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
    upper, middle, lower = talib.BBANDS(close, timeperiod=20)
    df['BB_upper'] = upper
    df['BB_middle'] = middle
    df['BB_lower'] = lower
    df['ADX'] = talib.ADX(high, low, close, timeperiod=14)
    df['SAR'] = talib.SAR(high, low, acceleration=0.02, maximum=0.2)
    df['AROON_up'], df['AROON_down'] = talib.AROON(high, low, timeperiod=14)
    return df

# === DYNAMIC TA-LIB CANDLE PATTERNS ===
def detect_ta_patterns_dynamic(df):
    open_ = df['open'].astype(float).values
    high = df['high'].astype(float).values
    low = df['low'].astype(float).values
    close = df['close'].astype(float).values
    pattern_funcs = talib.get_function_groups().get('Pattern Recognition', [])
    pattern_results = []
    for name in pattern_funcs:
        func = getattr(talib, name, None)
        if func is not None:
            result = func(open_, high, low, close)
            if result[-1] != 0:
                pattern_results.append(name)
    return ', '.join(pattern_results) if pattern_results else 'None'

# === OPENCV PATTERN DETECTION ===
def detect_visual_pattern(df):
    prices = df['close'].astype(float).values
    patterns = []
    peaks, _ = find_peaks(prices, distance=2)
    troughs, _ = find_peaks(-prices, distance=2)
    if len(peaks) >= 3:
        for i in range(len(peaks)-2):
            p1,p2,p3 = peaks[i],peaks[i+1],peaks[i+2]
            if prices[p1] < prices[p2] > prices[p3] and abs(prices[p1]-prices[p3]) < 0.05*prices[p2]:
                patterns.append('Head & Shoulders')
                break
    if len(troughs) >= 2:
        for i in range(len(troughs)-1):
            if abs(prices[troughs[i]]-prices[troughs[i+1]]) < 0.03*prices[troughs[i]]:
                patterns.append('Double Bottom')
                break
    min_idx = np.argmin(prices)
    if 0.3*len(prices) < min_idx < 0.7*len(prices):
        left = prices[:min_idx]
        right = prices[min_idx:]
        if np.mean(left) > prices[min_idx] and np.mean(right) > prices[min_idx]:
            patterns.append('Cup & Handle')
    if len(prices) >= 10:
        slope = np.polyfit(range(10), prices[-10:], 1)[0]
        if abs(slope) < 0.05:
            patterns.append('Bull Flag')
    return ', '.join(patterns) if patterns else 'None'

# === MAIN WRAPPER ===
def enrich_with_technical_analysis(filtered_df, ticker_ohlcv_map):
    clear_temp_charts()
    enriched_rows = []
    for _, row in filtered_df.iterrows():
        ticker = row['Ticker']
        df = ticker_ohlcv_map.get(ticker)
        if df is None or df.empty:
            continue
        df_ta = compute_ta_indicators(df)
        ta_pattern = detect_ta_patterns_dynamic(df_ta)
        visual_pattern = detect_visual_pattern(df_ta)
        enriched = row.to_dict()
        enriched['TA-Lib Pattern'] = ta_pattern
        enriched['Visual Pattern'] = visual_pattern
        enriched_rows.append(enriched)
    clear_temp_charts()
    return pd.DataFrame(enriched_rows)
