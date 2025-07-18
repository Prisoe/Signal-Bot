# Signal-Bot

Signal-Bot contains several standalone utilities for screening stocks and generating trading signals.

## Installation

Use Python 3 and install the required packages with pip:

```bash
pip install yfinance pandas numpy ta-lib mplfinance opencv-python
```

## Scripts

- **screener.py** – Downloads the most active NASDAQ tickers from Yahoo Finance and filters them by price, volume and volatility. A CSV is saved and optionally emailed. Run with:

  ```bash
  python screener.py
  ```

- **strategy_tester.py** – Adds technical indicators and applies a basic filter to determine long/short bias for each ticker. Can be imported by other modules.

- **analysis_engine.py** – Helper functions that calculate TA‑Lib indicators and detect basic chart patterns using OpenCV. Used internally by other scripts.

- **backtester.py** – Downloads historical prices, applies strategies from `strategy_tester.py` and evaluates the performance. Example:

  ```bash
  python backtester.py
  ```

- **build_ml_training_data.py** – Reads OHLCV CSV files from `historical_data/`, applies all strategies and creates labelled data for machine learning.

- **final_enricher.py** – Fetches the latest data for each ticker in an input CSV and enriches it with additional signals and labels:

  ```bash
  python final_enricher.py
  ```

- **pattern_scanner.py** – Scans ticker data for candlestick and visual patterns. Returns a summary of detected patterns.

##Typical workflow

- **Run screener.py**
Downloads the most active NASDAQ tickers, filters them by price/volume/volatility, and writes a CSV report. Environment variables EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECEIVER must be set for emailing the results (see lines 23‑30 in screener.py).

- **Run final_enricher.py**
Takes the screener’s CSV and enriches each ticker with recent data, technical signals, and pattern detection, producing enriched_signals.csv.

- **Run backtester.py (optional)**
Evaluates trading signals over a specified historical period. The script downloads data, applies strategies from strategy_tester.py, and outputs backtest statistics and per‑ticker CSVs.

- **Run build_ml_training_data.py (optional)**
Processes historical OHLCV files under historical_data/, runs all strategies to label the data, and saves combined datasets for machine‑learning.

- **Use pattern_scanner.py (optional utility)**
Given a dictionary of ticker dataframes, it detects candlestick and visual patterns. It doesn’t run standalone—import and call run_pattern_scanner() when needed. strategy_tester.py and analysis_engine.py supply the indicator calculations and pattern functions used by the above scripts. They aren’t typically executed on their own.

**Summary**
The project doesn’t enforce a strict sequence, but a common order is:

- screener.py → generate daily CSV and email.

- final_enricher.py → add recent data, TA-Lib/OpenCV patterns, and labels.

- Optionally evaluate with backtester.py.

- Optionally build a training dataset with build_ml_training_data.py.

- Call functions from pattern_scanner.py, strategy_tester.py, and analysis_engine.py as needed within the above steps.

