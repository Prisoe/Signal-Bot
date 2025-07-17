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

