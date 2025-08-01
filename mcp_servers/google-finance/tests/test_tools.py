import pytest
from tools.get_stock_price import get_stock_price

def test_get_stock_price():
    result = get_stock_price("AAPL")
    assert "price" in result or "error" in result
