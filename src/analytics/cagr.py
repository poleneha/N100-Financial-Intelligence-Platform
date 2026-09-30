def calculate_cagr(start_value, end_value, years):
    """
    Returns only CAGR value.
    """

    if years <= 0:
        return None

    if start_value == 0:
        return None

    if start_value > 0 and end_value > 0:
        return ((end_value / start_value) ** (1 / years) - 1) * 100

    if start_value > 0 and end_value <= 0:
        return None

    if start_value < 0 and end_value > 0:
        return None

    if start_value < 0 and end_value < 0:
        return None

    return None



def cagr_flag(start_value, end_value, years):
    """
    Returns CAGR edge case flag.
    """

    if years <= 0:
        return "INSUFFICIENT"

    if start_value == 0:
        return "ZERO_BASE"

    if start_value > 0 and end_value > 0:
        return "NORMAL"

    if start_value > 0 and end_value <= 0:
        return "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return "BOTH_NEGATIVE"

    return "INSUFFICIENT"