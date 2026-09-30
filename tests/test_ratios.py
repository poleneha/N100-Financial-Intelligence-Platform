from src.analytics.financial_ratios import *

def test_net_profit_margin_normal():
    assert net_profit_margin(100, 1000) == 10

def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None

def test_roe_normal():
    assert return_on_equity(100, 500) == 20

def test_roe_negative_equity():
    assert return_on_equity(100, -500) is None

def test_debt_to_equity_zero_borrowing():
    assert debt_to_equity(0, 500, 0) == 0

def test_debt_to_equity_normal():
    assert debt_to_equity(500, 500, 0) == 1

def test_interest_coverage_normal():
    assert interest_coverage(200, 100) == 2

def test_interest_coverage_zero_interest():
    assert interest_coverage(200, 0) is None