from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/market-cap", tags=["Valuation"])

DATA_FILE = Path("output/market_cap.csv")


@router.get("/{ticker}")
def get_valuation(ticker: str):

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="market_cap.csv not found"
        )

    df = pd.read_csv(DATA_FILE)

    ticker_col = None

    for col in ["company_id", "ticker", "symbol"]:
        if col in df.columns:
            ticker_col = col
            break

    if ticker_col is None:
        raise HTTPException(
            status_code=500,
            detail="Ticker/company column not found"
        )

    result = df[
        df[ticker_col]
        .astype(str)
        .str.upper()
        == ticker.upper()
    ]

    result = result.replace({float("nan"): None})

    return {
        "ticker": ticker.upper(),
        "count": len(result),
        "results": result.to_dict(orient="records")
    }
