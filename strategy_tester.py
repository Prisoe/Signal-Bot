import os
import pandas as pd
from analysis_engine import enrich_with_technical_analysis

# === SMART FILTER PARAMETERS ===
VWAP_THRESHOLD = 0
RSI_LONG_MIN = 50
RSI_SHORT_MAX = 50
VOLUME_SURGE_MIN = 80
VOLATILITY_MIN = 2

def add_technical_indicators(df):
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD Line'] = ema_12 - ema_26
    df['MACD Signal Line'] = df['MACD Line'].ewm(span=9, adjust=False).mean()
    df['9 EMA'] = df['close'].ewm(span=9, adjust=False).mean()
    df['20 EMA'] = df['close'].ewm(span=20, adjust=False).mean()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI 14'] = 100 - (100 / (1 + rs))
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    df['VWAP'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    df['VWAP Deviation %'] = ((df['close'] - df['VWAP']) / df['VWAP']) * 100
    df['Price Action %'] = df['close'].pct_change() * 100
    df['20D Avg Volume'] = df['volume'].rolling(window=20).mean()
    df['Volume Surge %'] = ((df['volume'] - df['20D Avg Volume']) / df['20D Avg Volume']) * 100
    df['Volatility %'] = ((df['high'] - df['low']) / df['close']) * 100
    df.drop(columns=['20D Avg Volume'], inplace=True, errors='ignore')
    return df

def smart_filter(df):
    filtered = df[
        (df['Volume Surge %'] >= VOLUME_SURGE_MIN) &
        (df['Volatility %'] >= VOLATILITY_MIN)
    ].copy()
    filtered['Bias'] = filtered.apply(determine_bias, axis=1)
    return filtered

def determine_bias(row):
    if (
        row['VWAP Deviation %'] > 0 and
        row['RSI 14'] >= 50 and
        row['MACD Line'] > row['MACD Signal Line'] and
        row['Volume Surge %'] > 50 and
        row['9 EMA'] > row['20 EMA'] and
        row['Price Action %'] > -5
    ):
        return 'Long'
    elif (
        row['VWAP Deviation %'] < 0 and
        row['RSI 14'] <= 50 and
        row['MACD Line'] < row['MACD Signal Line'] and
        row['Volume Surge %'] > 50 and
        row['9 EMA'] < row['20 EMA'] and
        row['Price Action %'] < 5
    ):
        return 'Short'
    return 'Neutral'

def run_all_strategies(df):
    df = add_technical_indicators(df)
    filtered_df = smart_filter(df)
    os.makedirs('filtered_csv_results', exist_ok=True)
    filtered_csv_path = 'filtered_csv_results/smart_filtered_results.csv'
    if os.path.exists(filtered_csv_path):
        filtered_df.to_csv(filtered_csv_path, mode='a', header=False, index=False)
    else:
        filtered_df.to_csv(filtered_csv_path, index=False)
    print(f"✅ Appended {len(filtered_df)} rows to '{filtered_csv_path}'.")
    ticker_ohlcv_map = {ticker: group.sort_values('date').copy() for ticker, group in df.groupby('Ticker') if len(group) >= 20}
    enriched_df = enrich_with_technical_analysis(filtered_df, ticker_ohlcv_map)
    print("\n✅ All strategies complete.")
    return enriched_df, filtered_df, []
