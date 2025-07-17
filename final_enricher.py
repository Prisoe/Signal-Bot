import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from analysis_engine import compute_ta_indicators, detect_ta_patterns_dynamic, detect_visual_pattern
from strategy_tester import add_technical_indicators, smart_filter, determine_bias

DAYS_FORWARD = [1,2,3]
LABEL_THRESHOLD = 0.03

def calculate_returns(df):
    for d in DAYS_FORWARD:
        df[f'Return_{d}d'] = (df['close'].shift(-d) - df['close']) / df['close']
    return df

def label_signal(row):
    return int(any([row[f'Return_{d}d'] >= LABEL_THRESHOLD for d in DAYS_FORWARD]))

def enrich_row(ticker):
    try:
        df = yf.download(ticker, period='30d', interval='1d', progress=False).reset_index()
        df.columns = [col.lower() if isinstance(col,str) else col for col in df.columns]
        if len(df) < max(DAYS_FORWARD)+1:
            return []
        df = calculate_returns(df)
        df = add_technical_indicators(df)
        latest = df.iloc[-(max(DAYS_FORWARD)+1)].copy()
        enriched = latest.to_dict()
        enriched['Ticker'] = ticker
        enriched.update({f'Return_{d}d': df.iloc[-(max(DAYS_FORWARD)+1)][f'Return_{d}d'] for d in DAYS_FORWARD})
        enriched['Label'] = label_signal(df.iloc[-(max(DAYS_FORWARD)+1)])
        df_ta = compute_ta_indicators(df)
        enriched['TA-Lib Pattern'] = detect_ta_patterns_dynamic(df_ta)
        enriched['Visual Pattern'] = detect_visual_pattern(df_ta)
        bias = determine_bias(latest)
        enriched['Bias'] = bias
        return enriched
    except Exception as e:
        print(f'Error enriching {ticker}: {e}')
        return []

def enrich_csv(input_csv, output_csv):
    base_df = pd.read_csv(input_csv)
    enriched_rows = []
    for _, row in base_df.iterrows():
        ticker = row['Ticker']
        enriched = enrich_row(ticker)
        if enriched:
            enriched_rows.append(enriched)
    final_df = pd.DataFrame(enriched_rows)
    final_df.to_csv(output_csv, index=False)
    print(f'✅ Final enriched CSV saved to: {output_csv}')

if __name__ == '__main__':
    enrich_csv('daily_results.csv', 'enriched_signals.csv')
