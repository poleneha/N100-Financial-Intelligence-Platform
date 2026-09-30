import re

def normalize_year(year):
    if year is None:
        return None
    try:
        return int(str(year).strip())
    except:
        return None

def normalize_ticker(ticker):
    if ticker is None:
        return ""
    ticker = str(ticker).strip().upper()
    ticker = re.sub(r'[^A-Z0-9]', '', ticker)
    return ticker

if __name__ == "__main__":
    print(normalize_year("2024"))
    print(normalize_ticker("tcs.ns"))