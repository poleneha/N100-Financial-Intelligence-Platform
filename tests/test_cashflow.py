from src.analytics.cashflow_kpis import *

def test_fcf_positive():
    assert free_cash_flow(100, -50) == 50

def test_fcf_negative():
    assert free_cash_flow(-100, -50) == -150

def test_capex_intensity():
    assert capex_intensity(-50, 1000) == 5

def test_fcf_conversion_normal():
    assert fcf_conversion(50, 100) == 50

def test_fcf_conversion_zero_op():
    assert fcf_conversion(50, 0) is None

def test_cfo_quality_high():
    assert cfo_quality(200, 100) == "High Quality"