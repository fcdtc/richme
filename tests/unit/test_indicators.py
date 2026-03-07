"""Quick test for indicators module."""

import sys
sys.path.insert(0, '/Users/congfei/github/richme')

import pandas as pd
from backend.services.indicators import (
    calculate_ma,
    calculate_macd,
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_all_indicators,
    get_indicator_library
)


def test_indicators():
    """Test all indicator calculations."""
    print(f"Using library: {get_indicator_library()}")

    # Generate test data
    import numpy as np
    np.random.seed(42)
    prices = pd.Series(np.random.uniform(1.0, 2.0, 100).cumsum())

    # Test MA
    ma = calculate_ma(prices, [5, 10, 30])
    print(f"MA5: {ma.get('ma5', 'N/A')}")
    assert all(f'ma{p}' in ma for p in [5, 10, 30])

    # Test MACD
    macd = calculate_macd(prices)
    print(f"MACD DIF: {macd['dif']:.4f}, DEA: {macd['dea']:.4f}, BAR: {macd['bar']:.4f}")
    assert 'dif' in macd
    assert 'dea' in macd
    assert 'bar' in macd

    # Test RSI
    rsi = calculate_rsi(prices)
    print(f"RSI: {rsi:.2f}")
    assert 0 <= rsi <= 100

    # Test Bollinger Bands
    bb = calculate_bollinger_bands(prices)
    print(f"Bollinger: Upper {bb['upper']:.4f}, Middle {bb['middle']:.4f}, Lower {bb['lower']:.4f}")
    assert bb['upper'] >= bb['middle'] >= bb['lower']

    # Test all indicators
    all_indicators = calculate_all_indicators(prices)
    assert 'ma' in all_indicators
    assert 'macd' in all_indicators
    assert 'rsi' in all_indicators
    assert 'bollinger' in all_indicators

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    test_indicators()
