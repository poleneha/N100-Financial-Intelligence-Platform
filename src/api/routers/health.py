from fastapi import APIRouter
import sqlite3
import time
from pathlib import Path

router = APIRouter()

START_TIME = time.time()

DB_PATH = Path("data/db/nifty100.db")


@router.get("/health")
def health_check():
    counts = {}

    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)

        tables = [
            "companies",
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
            "peer_percentiles",
            "screener_output",
            "capital_allocation",
            "pros_cons_generated",
        ]

        for table in tables:
            try:
                counts[table] = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
            except Exception:
                counts[table] = 0

        conn.close()

    return {
        "status": "ok",
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
        "db_row_counts": counts,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": "1.0.0",
    }
