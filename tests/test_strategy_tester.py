import pandas as pd
from strategy_tester import add_technical_indicators


def test_add_technical_indicators_adds_columns():
    data = {
        'close': list(range(10, 40)),
        'high': list(range(12, 42)),
        'low': list(range(8, 38)),
        'volume': [1000 + i for i in range(30)],
    }
    df = pd.DataFrame(data)
    result = add_technical_indicators(df.copy())
    expected_columns = [
        'MACD Line',
        'MACD Signal Line',
        '9 EMA',
        '20 EMA',
        'RSI 14',
        'VWAP',
        'VWAP Deviation %',
        'Price Action %',
        'Volume Surge %',
        'Volatility %',
    ]
    for col in expected_columns:
        assert col in result.columns, f"{col} not in DataFrame"
    assert len(result) == len(df)

