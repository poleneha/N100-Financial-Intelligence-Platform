from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

DATA_FILE = Path("output/portfolio_stats.csv")


@router.get("/stats")
def portfolio_stats():

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="portfolio_stats.csv not found"
        )

    df = pd.read_csv(DATA_FILE)

    df = df.replace({float("nan"): None})

    return {
        "count": len(df),
        "stats": df.to_dict(orient="records")
    }
