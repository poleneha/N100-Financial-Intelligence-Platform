from fastapi import APIRouter, HTTPException
import sqlite3

router = APIRouter(prefix="/companies", tags=["Companies"])

DB_PATH = "data/db/nifty100.db"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------
# FIND COMPANY
# ---------------------------------------------------------

def find_company(conn, ticker):
    return conn.execute(
        """
        SELECT *
        FROM companies
        WHERE UPPER(TRIM(id)) = UPPER(TRIM(?))
           OR UPPER(TRIM(company_name)) = UPPER(TRIM(?))
        LIMIT 1
        """,
        (ticker, ticker)
    ).fetchone()


# ---------------------------------------------------------
# GET ALL COMPANIES
# ---------------------------------------------------------

@router.get("")
def get_companies(search: str | None = None):

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM companies
        ORDER BY company_name
        """
    ).fetchall()

    results = []

    for row in rows:

        item = dict(row)

        if search:

            text = (
                str(item.get("id", "")) +
                " " +
                str(item.get("company_name", ""))
            ).lower()

            if search.lower() not in text:
                continue

        results.append(item)

    conn.close()

    return {
        "count": len(results),
        "data": results
    }


# ---------------------------------------------------------
# GET SINGLE COMPANY
# ---------------------------------------------------------

@router.get("/{ticker}")
def get_company(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    result = dict(company)

    # Latest financial ratios
    ratios = conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
        """,
        (company["id"],)
    ).fetchone()

    result["latest_ratios"] = (
        dict(ratios)
        if ratios
        else None
    )

    conn.close()

    return result


# ---------------------------------------------------------
# PROFIT & LOSS
# ---------------------------------------------------------

@router.get("/{ticker}/pl")
def get_company_pl(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    rows = conn.execute(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
        """,
        (company["id"],)
    ).fetchall()

    conn.close()

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "count": len(rows),
        "history": [
            dict(row)
            for row in rows
        ]
    }


# ---------------------------------------------------------
# BALANCE SHEET
# ---------------------------------------------------------

@router.get("/{ticker}/bs")
def get_company_bs(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    rows = conn.execute(
        """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
        """,
        (company["id"],)
    ).fetchall()

    conn.close()

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "count": len(rows),
        "history": [
            dict(row)
            for row in rows
        ]
    }


# ---------------------------------------------------------
# CASH FLOW
# ---------------------------------------------------------

@router.get("/{ticker}/cashflow")
def get_company_cashflow(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    rows = conn.execute(
        """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
        """,
        (company["id"],)
    ).fetchall()

    conn.close()

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "count": len(rows),
        "history": [
            dict(row)
            for row in rows
        ]
    }


# ---------------------------------------------------------
# FINANCIAL RATIOS
# ---------------------------------------------------------

@router.get("/{ticker}/ratios")
def get_company_ratios(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    rows = conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        """,
        (company["id"],)
    ).fetchall()

    conn.close()

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "count": len(rows),
        "history": [
            dict(row)
            for row in rows
        ]
    }


# ---------------------------------------------------------
# SECTOR
# ---------------------------------------------------------

@router.get("/{ticker}/sector")
def get_company_sector(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    company_id = company["id"]

    # -----------------------------------------------------
    # Check actual sectors table columns
    # -----------------------------------------------------

    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(sectors)"
        ).fetchall()
    ]

    sector_row = None

    # -----------------------------------------------------
    # Normal database structure
    # -----------------------------------------------------

    if "company_id" in columns:

        sector_row = conn.execute(
            """
            SELECT *
            FROM sectors
            WHERE UPPER(TRIM(company_id)) = UPPER(TRIM(?))
            LIMIT 1
            """,
            (company_id,)
        ).fetchone()

    # -----------------------------------------------------
    # Your current database has bad imported column names:
    #
    # 1
    # abb
    # industrials
    # capital_goods
    # 0.81
    # large_cap
    #
    # The ticker is stored in column "abb".
    # -----------------------------------------------------

    elif "abb" in columns:

        sector_row = conn.execute(
            """
            SELECT *
            FROM sectors
            WHERE UPPER(TRIM(abb)) = UPPER(TRIM(?))
            LIMIT 1
            """,
            (company_id,)
        ).fetchone()

    # -----------------------------------------------------
    # Generic fallback:
    # detect the column containing company IDs
    # -----------------------------------------------------

    else:

        for column in columns:

            try:

                test = conn.execute(
                    f"""
                    SELECT *
                    FROM sectors
                    WHERE UPPER(TRIM("{column}")) = UPPER(TRIM(?))
                    LIMIT 1
                    """,
                    (company_id,)
                ).fetchone()

                if test:

                    sector_row = test
                    break

            except sqlite3.Error:

                continue

    # -----------------------------------------------------
    # Convert result to clean API response
    # -----------------------------------------------------

    sector_result = {}

    if sector_row:

        raw = dict(sector_row)

        # Your imported table structure:
        #
        # id      -> raw["1"]
        # ticker  -> raw["abb"]
        # sector  -> raw["industrials"]
        # industry -> raw["capital_goods"]
        # weight -> raw["0.81"]
        # market cap -> raw["large_cap"]

        if "abb" in raw:

            sector_result = {
                "sector": raw.get("industrials"),
                "industry": raw.get("capital_goods"),
                "weight": raw.get("0.81"),
                "market_cap_category": raw.get("large_cap")
            }

        else:

            # Normal structure fallback

            sector_result = {
                "sector": raw.get("sector"),
                "industry": raw.get("industry"),
                "weight": raw.get("weight"),
                "market_cap_category": raw.get(
                    "market_cap_category"
                )
            }

            # Remove missing values

            sector_result = {
                key: value
                for key, value in sector_result.items()
                if value is not None
            }

    conn.close()

    return {
        "company_id": company_id,
        "company_name": company["company_name"],
        "sector": sector_result
    }


# ---------------------------------------------------------
# PEERS
# ---------------------------------------------------------

@router.get("/{ticker}/peers")
def get_company_peers(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    company_id = company["id"]

    # -----------------------------------------------------
    # Get peer_groups columns
    # -----------------------------------------------------

    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(peer_groups)"
        ).fetchall()
    ]

    peers = []

    peer_group = None

    # -----------------------------------------------------
    # Your current peer_groups table:
    #
    # id
    # private_banks
    # hdfcbank
    # true.1
    #
    # The actual data is:
    #
    # IT Services | TCS | 1
    # IT Services | INFY | 0
    # -----------------------------------------------------

    if "hdfcbank" in columns and "private_banks" in columns:

        peer_row = conn.execute(
            """
            SELECT *
            FROM peer_groups
            WHERE UPPER(TRIM(hdfcbank)) = UPPER(TRIM(?))
            LIMIT 1
            """,
            (company_id,)
        ).fetchone()

        if peer_row:

            peer_group = peer_row["private_banks"]

            rows = conn.execute(
                """
                SELECT *
                FROM peer_groups
                WHERE private_banks = ?
                """,
                (peer_group,)
            ).fetchall()

            for row in rows:

                row_company_id = row["hdfcbank"]

                # Do not return the selected company itself
                if row_company_id.upper() == company_id.upper():
                    continue

                peer_company = conn.execute(
                    """
                    SELECT *
                    FROM companies
                    WHERE UPPER(TRIM(id)) = UPPER(TRIM(?))
                    LIMIT 1
                    """,
                    (row_company_id,)
                ).fetchone()

                if not peer_company:
                    continue

                peer = {
                    "company_id": row_company_id,
                    "peer_group": peer_group,
                    "is_primary": bool(row["true.1"]),
                    "company_name": peer_company["company_name"],
                    "company_logo": peer_company["company_logo"],
                    "book_value": peer_company["book_value"],
                    "roce_percentage": peer_company[
                        "roce_percentage"
                    ],
                    "roe_percentage": peer_company[
                        "roe_percentage"
                    ]
                }

                peers.append(peer)

    conn.close()

    return {
        "company_id": company_id,
        "company_name": company["company_name"],
        "peer_group": peer_group,
        "count": len(peers),
        "peers": peers
    }


# ---------------------------------------------------------
# PROS & CONS
# ---------------------------------------------------------

@router.get("/{ticker}/pros-cons")
def get_company_pros_cons(ticker: str):

    conn = get_db()

    company = find_company(conn, ticker)

    if not company:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found"
        )

    company_id = company["id"]

    # -----------------------------------------------------
    # Your database table is called prosandcons
    # NOT pros_cons
    #
    # Columns:
    # id
    # company_id
    # pros
    # cons
    # -----------------------------------------------------

    rows = conn.execute(
        """
        SELECT company_id, pros, cons
        FROM prosandcons
        WHERE UPPER(TRIM(company_id)) = UPPER(TRIM(?))
        ORDER BY id
        """,
        (company_id,)
    ).fetchall()

    pros = []
    cons = []

    for row in rows:

        row_company_id = row["company_id"]

        if row["pros"]:

            pros.append({
                "company_id": row_company_id,
                "text": row["pros"]
            })

        if row["cons"]:

            cons.append({
                "company_id": row_company_id,
                "text": row["cons"]
            })

    conn.close()

    return {
        "company_id": company_id,
        "company_name": company["company_name"],
        "count": len(rows),
        "pros_count": len(pros),
        "cons_count": len(cons),
        "pros": pros,
        "cons": cons
    }