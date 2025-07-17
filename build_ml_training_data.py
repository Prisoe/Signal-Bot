import os
import pandas as pd
import time
from strategy_tester import run_all_strategies

HISTORICAL_DIR = 'historical_data'
RESULTS_DIR = 'ml_dataset'
os.makedirs(RESULTS_DIR, exist_ok=True)

def add_future_returns(df, days=[1,2,3], threshold=0.02):
    for d in days:
        df[f'Return_{d}d'] = df['close'].shift(-d) / df['close'] - 1
    df['Label'] = ((df[[f'Return_{d}d' for d in days]] > threshold).any(axis=1)).astype(int)
    return df

def clean_malformed_ohlcv(df):
    df.columns = df.iloc[0].tolist()
    df = df.drop([0,1,2]).reset_index(drop=True)
    if 'Price' in df.columns:
        df.rename(columns={'Price':'Date'}, inplace=True)
    df.columns = [c.strip().lower().replace(' ','_') for c in df.columns]
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    for col in ['open','high','low','close','volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['date','open','high','low','close','volume'])
    return df

def clean_standard_ohlcv(df):
    df.columns = [c.strip().lower().replace(' ','_') for c in df.columns]
    if 't' in df.columns:
        df.rename(columns={'t':'date'}, inplace=True)
    keep = ['date','open','high','low','close','volume']
    df = df[[c for c in keep if c in df.columns]]
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    for col in ['open','high','low','close','volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['date','open','high','low','close','volume'])
    return df

def process_ticker_csv(file_path):
    try:
        df = pd.read_csv(file_path, header=None)
        if df.iloc[0,0].strip().lower() == 'price':
            df = clean_malformed_ohlcv(df)
        else:
            df = pd.read_csv(file_path)
            df = clean_standard_ohlcv(df)
        required = {'date','open','high','low','close','volume'}
        if not required.issubset(df.columns):
            raise ValueError(f'{file_path} missing OHLCV columns')
        ticker = os.path.basename(file_path).replace('.csv','')
        df['Ticker'] = ticker
        df = df.sort_values('date')
        if df.shape[0] < 50:
            return None
        df = add_future_returns(df)
        final_df, filtered_df, strategy_results = run_all_strategies(df)
        return final_df, filtered_df, strategy_results
    except Exception as e:
        print(f'❌ Error processing {file_path}: {e}')
        return None

def main():
    all_strategy_data = []
    all_filtered_data = []
    all_combined_strategies = []
    print(f'📁 Reading files from: {HISTORICAL_DIR}')
    for file in os.listdir(HISTORICAL_DIR):
        if file.endswith('.csv'):
            path = os.path.join(HISTORICAL_DIR, file)
            print(f'🔍 Processing {file}...')
            result = process_ticker_csv(path)
            if result is not None:
                final_df, filtered_df, strategy_results = result
                all_strategy_data.append(final_df)
                all_filtered_data.append(filtered_df)
                for strat_df in strategy_results:
                    strat_df['Ticker File'] = file
                    all_combined_strategies.append(strat_df)
            time.sleep(0.2)
    if all_strategy_data:
        combined_strategies = pd.concat(all_strategy_data, ignore_index=True)
        strategies_path = os.path.join(RESULTS_DIR, 'combined_strategy_setups.csv')
        combined_strategies.to_csv(strategies_path, index=False)
        print(f'✅ Saved combined strategy setups to {strategies_path}')
    if all_combined_strategies:
        all_strategies_path = os.path.join('results', 'combined_all_strategy_signals.csv')
        pd.concat(all_combined_strategies, ignore_index=True).to_csv(all_strategies_path, index=False)
        print(f'✅ Saved combined strategy signals to {all_strategies_path}')

if __name__ == '__main__':
    main()
