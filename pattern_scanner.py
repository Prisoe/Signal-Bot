import os
import pandas as pd
import numpy as np
import talib
import mplfinance as mpf
import cv2
from datetime import datetime
from pathlib import Path

CHART_DIR = 'temp_charts'
Path(CHART_DIR).mkdir(exist_ok=True)

def clear_temp_charts():
    for f in Path(CHART_DIR).glob('*.png'):
        try:
            os.remove(f)
        except OSError:
            pass

TA_PATTERNS = {
    'CDLHAMMER': talib.CDLHAMMER,
    'CDLENGULFING': talib.CDLENGULFING,
    'CDLMORNINGSTAR': talib.CDLMORNINGSTAR,
    'CDLPIERCING': talib.CDLPIERCING,
    'CDLSHOOTINGSTAR': talib.CDLSHOOTINGSTAR,
    'CDLDOJI': talib.CDLDOJI,
    'CDLHANGINGMAN': talib.CDLHANGINGMAN,
    'CDLHEADANDSHOULDERS': None
}

def detect_ta_pattern(df):
    pattern_results = {}
    for name, func in TA_PATTERNS.items():
        if func is None:
            continue
        result = func(df['Open'], df['High'], df['Low'], df['Close'])
        if result.iloc[-1] != 0:
            pattern_results[name] = int(result.iloc[-1])
    return pattern_results

def generate_chart(df, ticker):
    chart_path = f"{CHART_DIR}/{ticker}_chart.png"
    mpf.plot(df.tail(50), type='candle', style='charles', volume=False, savefig=chart_path)
    return chart_path

def detect_opencv_pattern(chart_path):
    try:
        img = cv2.imread(chart_path, cv2.IMREAD_GRAYSCALE)
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 120:
            return "Possible Head & Shoulders"
        elif len(contours) > 80:
            return "Triple Bottom"
        else:
            return "None"
    except Exception:
        return "Error"

def analyze_patterns(ticker, df):
    chart_path = generate_chart(df, ticker)
    ta_patterns = detect_ta_pattern(df)
    visual_pattern = detect_opencv_pattern(chart_path)
    # remove chart after processing
    try:
        os.remove(chart_path)
    except OSError:
        pass
    return {
        'Ticker': ticker,
        'TA-Lib Pattern': ', '.join(ta_patterns.keys()) if ta_patterns else 'None',
        'OpenCV Pattern': visual_pattern
    }

def run_pattern_scanner(ticker_df_map):
    clear_temp_charts()
    results = []
    for ticker, df in ticker_df_map.items():
        results.append(analyze_patterns(ticker, df))
    clear_temp_charts()
    return pd.DataFrame(results)
