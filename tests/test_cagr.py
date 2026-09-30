from src.analytics.cagr import calculate_cagr

def test_cagr_normal():
    assert round(calculate_cagr(100, 200, 5), 2) > 0

def test_cagr_zero_base():
    assert calculate_cagr(0, 200, 5) is None

def test_cagr_turnaround():
    assert calculate_cagr(-100, 200, 5) is None

def test_cagr_decline():
    assert calculate_cagr(100, -200, 5) is None

def test_cagr_both_negative():
    assert calculate_cagr(-100, -200, 5) is None

def test_cagr_insufficient():
    assert calculate_cagr(100, 200, 0) is None