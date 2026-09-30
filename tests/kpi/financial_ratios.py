def return_on_equity(profit, equity):
    if equity <= 0:
        return None
    return (profit / equity) * 100


def interest_coverage(operating_profit, interest):
    if interest == 0:
        return None
    return operating_profit / interest