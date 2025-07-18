# all_in_one_workflow.py
import os
import pandas as pd

from screener import main as run_screener
from final_enricher import enrich_csv
from backtester import backtest
from build_ml_training_data import main as build_dataset

def run_full_pipeline():
    # 1. Run the screener (writes csv_results/daily_results.csv).
    run_screener()

    # 2. Enrich the screener output with recent data and TA patterns.
    input_csv = "csv_results/daily_results.csv"
    enriched_csv = "csv_results/enriched_signals.csv"
    enrich_csv(input_csv, enriched_csv)

    # 3. Backtest each ticker found in the enriched CSV.
    df = pd.read_csv(enriched_csv)
    tickers = df["Ticker"].unique().tolist()
    stats = backtest(tickers, start="2022-01-01", end="2023-01-01")

    # 4. Save summary metrics.
    os.makedirs("results", exist_ok=True)
    stats.to_csv("results/backtest_summary.csv", index=False)
    print(stats)

    # 5. Optional: build ML dataset from historical_data/*.csv.
    build_dataset()

if __name__ == "__main__":
    run_full_pipeline()
