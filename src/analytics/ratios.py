# =========================================
# Financial Ratios Module (FINAL FIXED)
# =========================================

def return_on_equity(net_profit, equity):
    # ❌ Negative equity → invalid
    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def return_on_assets(net_profit, total_assets):
    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100


# ✅ FIX: accept optional 3rd parameter
def debt_to_equity(total_debt, equity, *args):
    if equity == 0:
        return None

    return total_debt / equity


def interest_coverage(operating_profit, interest_expense):
    if interest_expense == 0:
        return None

    return operating_profit / interest_expense


def net_profit_margin(net_profit, sales):
    if sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    if sales == 0:
        return None

    return (operating_profit / sales) * 100


# ✅ FIXED OUTPUT LABELS
def cfo_quality(cfo, net_profit):
    if net_profit == 0:
        return None

    ratio = cfo / net_profit

    if ratio > 1:
        return "High Quality"
    elif ratio >= 0.5:
        return "Moderate"
    else:
        return "Accrual Risk"