from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter()

DATA_FILE = Path("output/financial_ratios.xlsx")


def load_data():
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="financial_ratios.xlsx not found"
        )

    df = pd.read_excel(DATA_FILE)

    if "company_id" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="company_id column not found"
        )

    # Exclude corrupted TTM rows.
    if "year" in df.columns:
        df = df[
            ~df["year"]
            .astype(str)
            .str.upper()
            .eq("TTM")
        ].copy()

        # Extract year number from values such as "Mar 2024"
        df["_year_num"] = pd.to_numeric(
            df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce"
        )

        # Keep latest valid annual row for every company
        df = (
            df.sort_values(["company_id", "_year_num"])
            .groupby("company_id", as_index=False)
            .tail(1)
        )

        df = df.drop(columns=["_year_num"], errors="ignore")

    return df


@router.get("/screener")
def screener(
    min_roe: float | None = Query(None),
    max_de: float | None = Query(None),
    min_fcf: float | None = Query(None),
    sector: str | None = Query(None),
    min_rev_cagr_5yr: float | None = Query(None),
    min_pat_cagr_5yr: float | None = Query(None),
    max_pe: float | None = Query(None),
):
    df = load_data()

    if min_roe is not None and "return_on_equity_pct" in df.columns:
        df = df[
            pd.to_numeric(
                df["return_on_equity_pct"],
                errors="coerce"
            ) >= min_roe
        ]

    if max_de is not None and "debt_to_equity" in df.columns:
        df = df[
            pd.to_numeric(
                df["debt_to_equity"],
                errors="coerce"
            ) <= max_de
        ]

    if min_fcf is not None and "free_cash_flow_cr" in df.columns:
        df = df[
            pd.to_numeric(
                df["free_cash_flow_cr"],
                errors="coerce"
            ) >= min_fcf
        ]

    if sector is not None:
        sector_cols = [
            c for c in df.columns
            if c.lower() in ["sector", "broad_sector"]
        ]

        if sector_cols:
            df = df[
                df[sector_cols[0]]
                .astype(str)
                .str.contains(
                    sector,
                    case=False,
                    na=False
                )
            ]

    if min_rev_cagr_5yr is not None and "revenue_cagr_5yr" in df.columns:
        df = df[
            pd.to_numeric(
                df["revenue_cagr_5yr"],
                errors="coerce"
            ) >= min_rev_cagr_5yr
        ]

    if min_pat_cagr_5yr is not None and "pat_cagr_5yr" in df.columns:
        df = df[
            pd.to_numeric(
                df["pat_cagr_5yr"],
                errors="coerce"
            ) >= min_pat_cagr_5yr
        ]

    if max_pe is not None and "pe" in df.columns:
        df = df[
            pd.to_numeric(
                df["pe"],
                errors="coerce"
            ) <= max_pe
        ]

    df = df.replace({float("nan"): None})

    return {
        "count": len(df),
        "results": df.to_dict(orient="records")
    }
