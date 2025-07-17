import pandas as pd
from unittest.mock import patch
from screener import process_ticker


class DummyTicker:
    def __init__(self, ticker):
        self.ticker = ticker
        self.info = {
            'fiftyTwoWeekHigh': 50,
            'fiftyTwoWeekLow': 10,
            'sector': 'Tech',
        }

    def history(self, period="21d", interval="1d"):
        data = {
            'Open': [10] * 21,
            'High': [11] * 21,
            'Low': [9] * 21,
            'Close': [10] * 21,
            'Volume': [200000] * 21,
        }
        return pd.DataFrame(data)


@patch('screener.yf.Ticker', return_value=DummyTicker('FAKE'))
def test_process_ticker_returns_data(mock_yf):
    result = process_ticker('FAKE')
    assert result is not None
    assert result['Ticker'] == 'FAKE'
    expected_keys = {
        'Current Price',
        'Volume',
        'ATR',
        'Price Action %',
        'Volatility %',
        'RSI 14',
        'VWAP Deviation %',
        'Gap %',
        'Volume Surge %',
        '52W High',
        '52W Low',
        'Sector',
        'News Link',
    }
    assert expected_keys.issubset(result.keys())

