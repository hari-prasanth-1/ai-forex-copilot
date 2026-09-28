import pandas as pd

from market_data.indicators import atr, ema, macd, rsi


def test_ema_has_expected_warmup():
    values = pd.Series(range(1, 31), dtype=float)
    result = ema(values, 20)
    assert result.iloc[:19].isna().all()
    assert result.iloc[19:].notna().all()


def test_rsi_is_bounded():
    values = pd.Series(range(1, 40), dtype=float)
    result = rsi(values, 14).dropna()
    assert ((result >= 0) & (result <= 100)).all()


def test_rsi_handles_zero_loss_as_overbought():
    values = pd.Series(range(1, 40), dtype=float)
    assert rsi(values, 14).iloc[-1] == 100.0


def test_macd_shape():
    values = pd.Series(range(1, 60), dtype=float)
    result = macd(values)
    assert list(result.columns) == ["macd", "signal", "histogram"]


def test_atr_is_non_negative():
    close = pd.Series([100, 101, 100, 102, 103, 102, 104], dtype=float)
    high = close + 1
    low = close - 1
    result = atr(high, low, close, 3).dropna()
    assert (result >= 0).all()
