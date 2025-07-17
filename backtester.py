import os
import yfinance as yf
import pandas as pd
import numpy as np
from strategy_tester import run_all_strategies


def download_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch historical price data from Yahoo Finance."""
    df = yf.download(ticker, start=start, end=end, progress=False).reset_index()
    df.columns = [c.lower() for c in df.columns]
    df['Ticker'] = ticker
    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    final_df, _, _ = run_all_strategies(df)
    return pd.merge(df, final_df[['date', 'Ticker', 'Bias']], on=['date', 'Ticker'], how='left')


def backtest_signals(signals: pd.DataFrame) -> pd.DataFrame:
    signals = signals.sort_values('date').reset_index(drop=True)
    signals['next_close'] = signals['close'].shift(-1)
    signals['market_return'] = signals['next_close'] / signals['close'] - 1
    position = signals['Bias'].map({'Long': 1, 'Short': -1}).fillna(0)
    signals['strategy_return'] = position * signals['market_return']
    signals['strategy_return'].fillna(0, inplace=True)
    signals['equity_curve'] = (1 + signals['strategy_return']).cumprod()
    return signals


def summary_stats(df: pd.DataFrame) -> dict:
    total_return = df['equity_curve'].iloc[-2] - 1 if len(df) > 1 else 0
    win_rate = (df['strategy_return'] > 0).mean()
    sharpe = 0.0
    if df['strategy_return'].std() != 0:
        sharpe = df['strategy_return'].mean() / df['strategy_return'].std() * np.sqrt(252)
    return {
        'Total Return': round(total_return, 4),
        'Win Rate': round(win_rate, 4),
        'Sharpe Ratio': round(sharpe, 4)
    }


def backtest(tickers, start, end, output_dir='backtests'):
    os.makedirs(output_dir, exist_ok=True)
    results = []
    for ticker in tickers:
        price_df = download_data(ticker, start, end)
        signals = generate_signals(price_df)
        tested = backtest_signals(signals)
        stats = summary_stats(tested)
        stats['Ticker'] = ticker
        results.append(stats)
        tested.to_csv(os.path.join(output_dir, f'{ticker}_backtest.csv'), index=False)
    pd.DataFrame(results).to_csv(os.path.join(output_dir, 'summary.csv'), index=False)
    return pd.DataFrame(results)


if __name__ == '__main__':
    tickers = ['AAPL', 'MSFT']
    stats = backtest(tickers, start='2022-01-01', end='2023-01-01')
    print(stats)
