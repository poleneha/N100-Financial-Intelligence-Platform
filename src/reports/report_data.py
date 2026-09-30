import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# REPORT DATA LOADER
# NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "db" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return sqlite3.connect(
        str(DB_PATH)
    )


# ============================================================
# SAFE TEXT CLEANING
# ============================================================

def clean_company_ids(df, column="company_id"):

    if column in df.columns:

        df[column] = (
            df[column]
            .astype(str)
            .str.upper()
            .str.strip()
        )

    return df


# ============================================================
# COMPANY MASTER
# ============================================================

def load_companies():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM companies
            """,
            conn
        )

    finally:

        conn.close()

    # Actual companies table uses id
    if "id" in df.columns:

        df["company_id"] = (
            df["id"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

    return df


# ============================================================
# FINANCIAL RATIOS
# ============================================================

def load_financial_ratios():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM financial_ratios
            """,
            conn
        )

    finally:

        conn.close()

    df = clean_company_ids(
        df,
        "company_id"
    )

    # Remove duplicate company/year records
    if {
        "company_id",
        "year"
    }.issubset(df.columns):

        df = df.drop_duplicates(
            subset=[
                "company_id",
                "year"
            ],
            keep="last"
        )

    return df


# ============================================================
# PROFIT & LOSS
# ============================================================

def load_profit_loss():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM profitandloss
            """,
            conn
        )

    finally:

        conn.close()

    return clean_company_ids(
        df,
        "company_id"
    )


# ============================================================
# BALANCE SHEET
# ============================================================

def load_balance_sheet():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM balancesheet
            """,
            conn
        )

    finally:

        conn.close()

    return clean_company_ids(
        df,
        "company_id"
    )


# ============================================================
# CASH FLOW
# ============================================================

def load_cash_flow():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM cashflow
            """,
            conn
        )

    finally:

        conn.close()

    return clean_company_ids(
        df,
        "company_id"
    )


# ============================================================
# SECTORS
# ============================================================

def load_sectors():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM sectors
            """,
            conn
        )

    finally:

        conn.close()

    return df


# ============================================================
# PEER GROUPS
# ============================================================

def load_peer_groups():

    conn = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM peer_groups
            """,
            conn
        )

    finally:

        conn.close()

    # Actual schema:
    #
    # 1
    # private_banks
    # hdfcbank
    # true.1

    if len(df.columns) == 4:

        df.columns = [
            "peer_group_id",
            "peer_group_name",
            "company_id",
            "is_benchmark"
        ]

    df = clean_company_ids(
        df,
        "company_id"
    )

    return df


# ============================================================
# PROS & CONS
# ============================================================

def load_pros_cons():

    conn = get_connection()

    try:

        # Actual database schema:
        #
        # id
        # company_id
        # pros
        # cons

        df = pd.read_sql_query(
            """
            SELECT
                id,
                company_id,
                pros,
                cons
            FROM prosandcons
            """,
            conn
        )

    finally:

        conn.close()

    df = clean_company_ids(
        df,
        "company_id"
    )

    return df


# ============================================================
# SCREENER OUTPUT
# ============================================================

def load_screener():

    file_path = (
        OUTPUT_DIR /
        "screener_output.xlsx"
    )

    if not file_path.exists():

        print(
            "WARNING: screener_output.xlsx not found"
        )

        return pd.DataFrame()

    try:

        df = pd.read_excel(
            file_path,
            sheet_name="All_Companies"
        )

    except Exception as e:

        print(
            f"WARNING: Could not load screener: {e}"
        )

        return pd.DataFrame()

    if "company_id" in df.columns:

        df = clean_company_ids(
            df,
            "company_id"
        )

    return df


# ============================================================
# CASH FLOW INTELLIGENCE
# ============================================================

def load_cashflow_intelligence():

    file_path = (
        OUTPUT_DIR /
        "cashflow_intelligence.xlsx"
    )

    if not file_path.exists():

        print(
            "WARNING: cashflow_intelligence.xlsx not found"
        )

        return pd.DataFrame()

    try:

        df = pd.read_excel(
            file_path,
            sheet_name="Cashflow_Intelligence"
        )

    except Exception as e:

        print(
            f"WARNING: Could not load cashflow intelligence: {e}"
        )

        return pd.DataFrame()

    if "company_id" in df.columns:

        df = clean_company_ids(
            df,
            "company_id"
        )

    return df


# ============================================================
# CAPITAL ALLOCATION
# ============================================================

def load_capital_allocation():

    file_path = (
        OUTPUT_DIR /
        "capital_allocation.csv"
    )

    if not file_path.exists():

        print(
            "WARNING: capital_allocation.csv not found"
        )

        return pd.DataFrame()

    try:

        df = pd.read_csv(
            file_path
        )

    except Exception as e:

        print(
            f"WARNING: Could not load capital allocation: {e}"
        )

        return pd.DataFrame()

    if "company_id" in df.columns:

        df = clean_company_ids(
            df,
            "company_id"
        )

    return df


# ============================================================
# LOAD ALL DATA
# ============================================================

def load_all_data():

    print("=" * 70)

    print(
        "LOADING REPORT DATA"
    )

    print("=" * 70)

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    data = {

        "companies":
            load_companies(),

        "ratios":
            load_financial_ratios(),

        "profit_loss":
            load_profit_loss(),

        "balance_sheet":
            load_balance_sheet(),

        "cash_flow":
            load_cash_flow(),

        "sectors":
            load_sectors(),

        "peer_groups":
            load_peer_groups(),

        "pros_cons":
            load_pros_cons(),

        "screener":
            load_screener(),

        "cashflow_intelligence":
            load_cashflow_intelligence(),

        "capital_allocation":
            load_capital_allocation()
    }

    print()

    print(
        "=" * 70
    )

    print(
        "DATASET VALIDATION"
    )

    print(
        "=" * 70
    )

    for name, df in data.items():

        if isinstance(
            df,
            pd.DataFrame
        ):

            print(
                f"{name:<25}"
                f" rows={len(df):<6}"
                f" columns={len(df.columns)}"
            )

    print()

    print(
        "REPORT DATA LOADED SUCCESSFULLY"
    )

    return data


# ============================================================
# COMPANY LOOKUP
# ============================================================

def get_company_data(
    data,
    company_id
):

    company_id = (
        str(company_id)
        .upper()
        .strip()
    )

    result = {}


    # ========================================================
    # COMPANY
    # ========================================================

    companies = data[
        "companies"
    ]

    if (
        not companies.empty
        and "company_id" in companies.columns
    ):

        company_match = companies[
            companies["company_id"]
            == company_id
        ]

    else:

        company_match = pd.DataFrame()

    result["company"] = (
        company_match.iloc[0].to_dict()
        if not company_match.empty
        else {}
    )


    # ========================================================
    # FINANCIAL RATIOS
    # ========================================================

    ratios = data[
        "ratios"
    ]

    company_ratios = ratios[
        ratios["company_id"]
        == company_id
    ].copy()

    if not company_ratios.empty:

        historical = company_ratios[
            ~company_ratios[
                "year"
            ]
            .astype(str)
            .str.upper()
            .eq("TTM")
        ]

        if not historical.empty:

            company_ratios = (
                historical
                .sort_values(
                    "year"
                )
                .tail(1)
            )

    result["ratios"] = (
        company_ratios.iloc[0].to_dict()
        if not company_ratios.empty
        else {}
    )


    # ========================================================
    # PROFIT & LOSS
    # ========================================================

    pl = data[
        "profit_loss"
    ]

    result["profit_loss"] = pl[
        pl["company_id"]
        == company_id
    ].copy()


    # ========================================================
    # BALANCE SHEET
    # ========================================================

    bs = data[
        "balance_sheet"
    ]

    result["balance_sheet"] = bs[
        bs["company_id"]
        == company_id
    ].copy()


    # ========================================================
    # CASH FLOW
    # ========================================================

    cf = data[
        "cash_flow"
    ]

    result["cash_flow"] = cf[
        cf["company_id"]
        == company_id
    ].copy()


    # ========================================================
    # SECTOR
    # ========================================================

    sectors = data[
        "sectors"
    ]

    sector_match = pd.DataFrame()

    if not sectors.empty:

        possible_columns = [
            "company_id",
            "abb",
            "id"
        ]

        company_column = next(
            (
                c
                for c in possible_columns
                if c in sectors.columns
            ),
            None
        )

        if company_column:

            sector_ids = (
                sectors[
                    company_column
                ]
                .astype(str)
                .str.upper()
                .str.strip()
            )

            sector_match = sectors[
                sector_ids
                == company_id
            ]

    result["sector"] = (
        sector_match.iloc[0].to_dict()
        if not sector_match.empty
        else {}
    )


    # ========================================================
    # PEER GROUP
    # ========================================================

    peers = data[
        "peer_groups"
    ]

    peer_match = peers[
        peers["company_id"]
        == company_id
    ]

    result["peer_group"] = (
        peer_match.iloc[0].to_dict()
        if not peer_match.empty
        else {}
    )


    # ========================================================
    # PROS & CONS
    # ========================================================

    pros_cons = data[
        "pros_cons"
    ]

    pros_cons_match = pros_cons[
        pros_cons["company_id"]
        == company_id
    ].copy()

    result["pros_cons"] = (
        pros_cons_match
    )


    # ========================================================
    # SCREENER
    # ========================================================

    screener = data[
        "screener"
    ]

    if (
        not screener.empty
        and "company_id"
        in screener.columns
    ):

        screener_ids = (
            screener[
                "company_id"
            ]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        screener_match = screener[
            screener_ids
            == company_id
        ]

        result["screener"] = (
            screener_match.iloc[0].to_dict()
            if not screener_match.empty
            else {}
        )

    else:

        result["screener"] = {}


    # ========================================================
    # CASH FLOW INTELLIGENCE
    # ========================================================

    cashflow_intel = data[
        "cashflow_intelligence"
    ]

    if (
        not cashflow_intel.empty
        and "company_id"
        in cashflow_intel.columns
    ):

        ids = (
            cashflow_intel[
                "company_id"
            ]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        match = cashflow_intel[
            ids
            == company_id
        ]

        result[
            "cashflow_intelligence"
        ] = (
            match.iloc[0].to_dict()
            if not match.empty
            else {}
        )

    else:

        result[
            "cashflow_intelligence"
        ] = {}


    # ========================================================
    # CAPITAL ALLOCATION
    # ========================================================

    allocation = data[
        "capital_allocation"
    ]

    if (
        not allocation.empty
        and "company_id"
        in allocation.columns
    ):

        ids = (
            allocation[
                "company_id"
            ]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        match = allocation[
            ids
            == company_id
        ]

        result[
            "capital_allocation"
        ] = (
            match.iloc[0].to_dict()
            if not match.empty
            else {}
        )

    else:

        result[
            "capital_allocation"
        ] = {}


    return result


# ============================================================
# REPORT DATA SUMMARY
# ============================================================

def print_company_summary(
    report,
    company_id
):

    print()

    print(
        "=" * 70
    )

    print(
        f"COMPANY REPORT DATA: {company_id}"
    )

    print(
        "=" * 70
    )


    # --------------------------------------------------------
    # Company
    # --------------------------------------------------------

    company = report.get(
        "company",
        {}
    )

    print(
        "Company:",
        company.get(
            "company_name",
            "Not Available"
        )
    )


    # --------------------------------------------------------
    # Sector
    # --------------------------------------------------------

    sector = report.get(
        "sector",
        {}
    )

    sector_name = (
        sector.get(
            "sector"
        )
        or sector.get(
            "industrials"
        )
        or "Not Available"
    )

    print(
        "Sector:",
        sector_name
    )


    # --------------------------------------------------------
    # Peer group
    # --------------------------------------------------------

    peer = report.get(
        "peer_group",
        {}
    )

    print(
        "Peer Group:",
        peer.get(
            "peer_group_name",
            "Not Available"
        )
    )


    # --------------------------------------------------------
    # Screener
    # --------------------------------------------------------

    screener = report.get(
        "screener",
        {}
    )

    print(
        "Screener Category:",
        screener.get(
            "category",
            "Not Available"
        )
    )

    print(
        "Screener Score:",
        screener.get(
            "composite_quality_score",
            "Not Available"
        )
    )


    # --------------------------------------------------------
    # Cash Flow
    # --------------------------------------------------------

    cashflow = report.get(
        "cashflow_intelligence",
        {}
    )

    print(
        "CFO Quality:",
        cashflow.get(
            "cfo_quality",
            "Not Available"
        )
    )

    print(
        "Capital Allocation:",
        cashflow.get(
            "capital_allocation_pattern",
            "Not Available"
        )
    )


    # --------------------------------------------------------
    # Pros & Cons
    # --------------------------------------------------------

    pc = report.get(
        "pros_cons"
    )

    if isinstance(
        pc,
        pd.DataFrame
    ):

        print(
            "Pros/Cons rows:",
            len(pc)
        )

    else:

        print(
            "Pros/Cons rows: 0"
        )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    data = load_all_data()

    test_company = "TCS"

    report = get_company_data(
        data,
        test_company
    )

    print_company_summary(
        report,
        test_company
    )

    print()

    print(
        "=" * 70
    )

    print(
        "REPORT DATA TEST COMPLETED"
    )

    print(
        "=" * 70
    )