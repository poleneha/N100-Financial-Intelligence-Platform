from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/sectors", tags=["Sectors"])

DATA_FILE = Path("output/financial_ratios.xlsx")


def load_data():
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="financial_ratios.xlsx not found"
        )

    return pd.read_excel(DATA_FILE)


@router.get("")
def get_sectors():
    df = load_data()

    sector_col = None

    for col in ["broad_sector", "sector", "Sector"]:
        if col in df.columns:
            sector_col = col
            break

    if sector_col is None:
        raise HTTPException(
            status_code=500,
            detail="Sector column not found"
        )

    sectors = (
        df[sector_col]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    sectors = sorted([s for s in sectors if s])

    return {
        "count": len(sectors),
        "sectors": sectors
    }


@router.get("/{sector}/companies")
def get_sector_companies(sector: str):
    df = load_data()

    sector_col = None

    for col in ["broad_sector", "sector", "Sector"]:
        if col in df.columns:
            sector_col = col
            break

    if sector_col is None:
        raise HTTPException(
            status_code=500,
            detail="Sector column not found"
        )

    df = df[
        df[sector_col]
        .astype(str)
        .str.contains(sector, case=False, na=False)
    ]

    if "year" in df.columns:
        df = (
            df.sort_values("year")
            .groupby("company_id", as_index=False)
            .tail(1)
        )

    df = df.replace({float("nan"): None})

    return {
        "sector": sector,
        "count": len(df),
        "results": df.to_dict(orient="records")
    }
