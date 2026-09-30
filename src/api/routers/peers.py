from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/peers", tags=["Peers"])

DATA_FILE = Path("output/peer_comparison.csv")


@router.get("/{ticker}")
def get_peers(ticker: str):

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="peer_comparison.csv not found"
        )

    df = pd.read_csv(DATA_FILE)

    if "company_id" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="company_id column not found"
        )

    result = df[
        df["company_id"]
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
