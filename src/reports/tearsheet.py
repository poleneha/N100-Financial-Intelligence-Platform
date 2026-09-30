import os
import sqlite3
from pathlib import Path

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "db" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "output" / "tearsheets"

REPORT_DATA_FILE = BASE_DIR / "output" / "report_data.xlsx"
SCREENER_FILE = BASE_DIR / "output" / "screener_output.xlsx"
CASHFLOW_FILE = BASE_DIR / "output" / "cashflow_intelligence.xlsx"


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PAGE SETTINGS
# ============================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 15 * mm
RIGHT_MARGIN = 15 * mm
TOP_MARGIN = 15 * mm
BOTTOM_MARGIN = 15 * mm


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=26,
    alignment=TA_CENTER,
    spaceAfter=8,
)

SUBTITLE_STYLE = ParagraphStyle(
    "SubtitleCustom",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    alignment=TA_CENTER,
    spaceAfter=14,
)

SECTION_STYLE = ParagraphStyle(
    "SectionCustom",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    spaceBefore=8,
    spaceAfter=7,
)

SUBSECTION_STYLE = ParagraphStyle(
    "SubsectionCustom",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=13,
    spaceBefore=5,
    spaceAfter=5,
)

BODY_STYLE = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=12,
    alignment=TA_LEFT,
)

SMALL_STYLE = ParagraphStyle(
    "SmallCustom",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=7,
    leading=9,
)

TABLE_HEADER_STYLE = ParagraphStyle(
    "TableHeader",
    parent=styles["BodyText"],
    fontName="Helvetica-Bold",
    fontSize=7,
    leading=9,
)

TABLE_BODY_STYLE = ParagraphStyle(
    "TableBody",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=7,
    leading=9,
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(
        str(DB_PATH)
    )


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    try:
        if pd.isna(value):
            return None

        return float(value)

    except Exception:
        return None


def format_number(value, decimals=2):
    number = safe_float(value)

    if number is None:
        return "N/A"

    return f"{number:,.{decimals}f}"


def format_percent(value, decimals=2):
    number = safe_float(value)

    if number is None:
        return "N/A"

    return f"{number:.{decimals}f}%"


def format_text(value):
    if value is None:
        return "N/A"

    if pd.isna(value):
        return "N/A"

    text = str(value).strip()

    if not text:
        return "N/A"

    return text


def paragraph(text, style=BODY_STYLE):
    return Paragraph(
        str(text),
        style
    )


# ============================================================
# LOAD COMPANY
# ============================================================

def load_company(company_id):

    conn = get_connection()

    query = """
        SELECT *
        FROM companies
        WHERE UPPER(TRIM(id)) = UPPER(TRIM(?))
        LIMIT 1
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    if df.empty:
        return None

    return df.iloc[0].to_dict()


# ============================================================
# LOAD RATIOS
# ============================================================

def load_ratios(company_id):

    conn = get_connection()

    query = """
        SELECT *
        FROM financial_ratios
        WHERE UPPER(TRIM(company_id)) = UPPER(TRIM(?))
        ORDER BY year DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# ============================================================
# LOAD PROFIT & LOSS
# ============================================================

def load_profit_loss(company_id):

    conn = get_connection()

    query = """
        SELECT *
        FROM profitandloss
        WHERE UPPER(TRIM(company_id)) = UPPER(TRIM(?))
        ORDER BY year DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# ============================================================
# LOAD BALANCE SHEET
# ============================================================

def load_balance_sheet(company_id):

    conn = get_connection()

    query = """
        SELECT *
        FROM balancesheet
        WHERE UPPER(TRIM(company_id)) = UPPER(TRIM(?))
        ORDER BY year DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# ============================================================
# LOAD CASH FLOW
# ============================================================

def load_cash_flow(company_id):

    conn = get_connection()

    query = """
        SELECT *
        FROM cashflow
        WHERE UPPER(TRIM(company_id)) = UPPER(TRIM(?))
        ORDER BY year DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# ============================================================
# LOAD SECTOR
# ============================================================

def load_sector(company_id):

    conn = get_connection()

    query = """
        SELECT *
        FROM sectors
        WHERE UPPER(TRIM(abb)) = UPPER(TRIM(?))
        LIMIT 1
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    if df.empty:
        return {}

    return df.iloc[0].to_dict()


# ============================================================
# LOAD PEER GROUP
# ============================================================

def load_peer_group(company_id):

    conn = get_connection()

    query = """
        SELECT
            private_banks AS peer_group,
            hdfcbank AS company_id,
            "true.1" AS is_benchmark
        FROM peer_groups
        WHERE UPPER(TRIM(hdfcbank)) = UPPER(TRIM(?))
        LIMIT 1
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    if df.empty:
        return {}

    return df.iloc[0].to_dict()


# ============================================================
# LOAD PROS & CONS
# ============================================================

def load_pros_cons(company_id):

    conn = get_connection()

    query = """
        SELECT
            company_id,
            pros,
            cons
        FROM prosandcons
        WHERE UPPER(TRIM(company_id)) = UPPER(TRIM(?))
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,)
    )

    conn.close()

    return df


# ============================================================
# LOAD SCREENER
# ============================================================

def load_screener(company_id):

    if not SCREENER_FILE.exists():
        return {}

    try:

        df = pd.read_excel(
            SCREENER_FILE,
            sheet_name="All_Companies"
        )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        row = df[
            df["company_id"] == company_id.upper().strip()
        ]

        if row.empty:
            return {}

        return row.iloc[0].to_dict()

    except Exception:
        return {}


# ============================================================
# LOAD CASH FLOW INTELLIGENCE
# ============================================================

def load_cashflow_intelligence(company_id):

    if not CASHFLOW_FILE.exists():
        return {}

    try:

        df = pd.read_excel(
            CASHFLOW_FILE,
            sheet_name="Cashflow_Intelligence"
        )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        row = df[
            df["company_id"] == company_id.upper().strip()
        ]

        if row.empty:
            return {}

        return row.iloc[0].to_dict()

    except Exception:
        return {}


# ============================================================
# FIND LATEST ROW
# ============================================================

def latest_row(df):

    if df is None or df.empty:
        return {}

    return df.iloc[0].to_dict()


# ============================================================
# KPI TABLE
# ============================================================

def create_kpi_table(
    company,
    ratios,
    screener,
    cashflow
):

    latest_ratio = latest_row(ratios)

    rows = [
        [
            paragraph("Metric", TABLE_HEADER_STYLE),
            paragraph("Value", TABLE_HEADER_STYLE),
        ],
        [
            paragraph("ROE", TABLE_BODY_STYLE),
            paragraph(
                format_percent(
                    latest_ratio.get(
                        "return_on_equity_pct"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("ROA", TABLE_BODY_STYLE),
            paragraph(
                format_percent(
                    latest_ratio.get(
                        "return_on_assets_pct"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Debt / Equity", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    latest_ratio.get(
                        "debt_to_equity"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Interest Coverage", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    latest_ratio.get(
                        "interest_coverage"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Composite Quality Score", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    screener.get(
                        "composite_quality_score"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("CFO Quality", TABLE_BODY_STYLE),
            paragraph(
                format_text(
                    cashflow.get(
                        "cfo_quality"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            75 * mm,
            95 * mm,
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F4E78")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    return table


# ============================================================
# FINANCIAL HISTORY TABLE
# ============================================================

def create_financial_history(ratios):

    if ratios.empty:
        return paragraph(
            "No financial ratio history available.",
            BODY_STYLE
        )

    columns = [
        "year",
        "return_on_equity_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
    ]

    available = [
        col
        for col in columns
        if col in ratios.columns
    ]

    data = ratios[available].head(5).copy()

    header_map = {
        "year": "Year",
        "return_on_equity_pct": "ROE %",
        "return_on_assets_pct": "ROA %",
        "debt_to_equity": "D/E",
        "operating_profit_margin_pct": "OPM %",
        "net_profit_margin_pct": "NPM %",
    }

    rows = [
        [
            paragraph(
                header_map.get(col, col),
                TABLE_HEADER_STYLE
            )
            for col in available
        ]
    ]

    for _, row in data.iterrows():

        current = []

        for col in available:

            value = row[col]

            if col == "year":
                text = format_text(value)

            elif col == "debt_to_equity":
                text = format_number(value)

            else:
                text = format_percent(value)

            current.append(
                paragraph(
                    text,
                    TABLE_BODY_STYLE
                )
            )

        rows.append(current)

    widths = [
        25 * mm,
        28 * mm,
        28 * mm,
        25 * mm,
        28 * mm,
        28 * mm,
    ]

    widths = widths[:len(available)]

    table = Table(
        rows,
        colWidths=widths,
        repeatRows=1
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F4E78")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
            ]
        )
    )

    return table


# ============================================================
# CASH FLOW TABLE
# ============================================================

def create_cashflow_table(cashflow):

    if not cashflow:
        return paragraph(
            "Cash flow intelligence not available.",
            BODY_STYLE
        )

    rows = [
        [
            paragraph("Cash Flow Metric", TABLE_HEADER_STYLE),
            paragraph("Value", TABLE_HEADER_STYLE),
        ],
        [
            paragraph("CFO", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    cashflow.get("cfo")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("PAT", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    cashflow.get("pat")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("CFO / PAT", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    cashflow.get("cfo_pat_ratio")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("CapEx", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    cashflow.get("capex_cr")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Free Cash Flow", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    cashflow.get("free_cash_flow_cr")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("CapEx Intensity", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    cashflow.get("capex_intensity")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Capital Allocation", TABLE_BODY_STYLE),
            paragraph(
                format_text(
                    cashflow.get(
                        "capital_allocation_pattern"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            75 * mm,
            95 * mm,
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#548235")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
            ]
        )
    )

    return table


# ============================================================
# PROS & CONS
# ============================================================

def create_pros_cons_table(pros_cons):

    if pros_cons.empty:

        return paragraph(
            "No pros/cons information available.",
            BODY_STYLE
        )

    pros = []
    cons = []

    for _, row in pros_cons.iterrows():

        pro_text = format_text(
            row.get("pros")
        )

        con_text = format_text(
            row.get("cons")
        )

        if pro_text != "N/A":
            pros.append(pro_text)

        if con_text != "N/A":
            cons.append(con_text)

            max_rows = max(
        len(pros),
        len(cons),
        1
    )

    rows = [
        [
            paragraph("Pros", TABLE_HEADER_STYLE),
            paragraph("Cons", TABLE_HEADER_STYLE),
        ]
    ]

    for i in range(max_rows):

        pro = (
            pros[i]
            if i < len(pros)
            else "N/A"
        )

        con = (
            cons[i]
            if i < len(cons)
            else "N/A"
        )

        rows.append(
            [
                paragraph(
                    "• " + pro,
                    TABLE_BODY_STYLE
                ),
                paragraph(
                    "• " + con,
                    TABLE_BODY_STYLE
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            85 * mm,
            85 * mm,
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.HexColor("#548235")
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    colors.HexColor("#C00000")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
            ]
        )
    )

    return table


# ============================================================
# PAGE HEADER / FOOTER
# ============================================================

def add_page_number(canvas, doc):

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.drawString(
        LEFT_MARGIN,
        8 * mm,
        "Nifty 100 Financial Intelligence Platform"
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        8 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# ============================================================
# BUILD REPORT
# ============================================================

def build_report(company_id):

    company = load_company(
        company_id
    )

    if company is None:
        print(
            f"Company not found: {company_id}"
        )
        return False

    ratios = load_ratios(
        company_id
    )

    profit_loss = load_profit_loss(
        company_id
    )

    balance_sheet = load_balance_sheet(
        company_id
    )

    cash_flow = load_cash_flow(
        company_id
    )

    sector = load_sector(
        company_id
    )

    peer_group = load_peer_group(
        company_id
    )

    pros_cons = load_pros_cons(
        company_id
    )

    screener = load_screener(
        company_id
    )

    cashflow_intelligence = (
        load_cashflow_intelligence(
            company_id
        )
    )

    company_name = format_text(
        company.get("company_name")
    )

    safe_company_id = (
        str(company_id)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    output_file = (
        OUTPUT_DIR /
        f"{safe_company_id}_tearsheet.pdf"
    )

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=f"{company_name} Tearsheet",
        author="Nifty 100 Financial Intelligence Platform",
    )

    story = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    story.append(
        paragraph(
            company_name,
            TITLE_STYLE
        )
    )

    story.append(
        paragraph(
            f"Company ID: {company_id}",
            SUBTITLE_STYLE
        )
    )

    # --------------------------------------------------------
    # COMPANY OVERVIEW
    # --------------------------------------------------------

    story.append(
        paragraph(
            "Company Overview",
            SECTION_STYLE
        )
    )

    overview_rows = [
        [
            paragraph("Company", TABLE_HEADER_STYLE),
            paragraph(
                company_name,
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Sector", TABLE_HEADER_STYLE),
            paragraph(
                format_text(
                    sector.get(
                        "industrials"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Industry", TABLE_HEADER_STYLE),
            paragraph(
                format_text(
                    sector.get(
                        "capital_goods"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Peer Group", TABLE_HEADER_STYLE),
            paragraph(
                format_text(
                    peer_group.get(
                        "peer_group"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Screener Category", TABLE_HEADER_STYLE),
            paragraph(
                format_text(
                    screener.get(
                        "category"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
    ]

    overview_table = Table(
        overview_rows,
        colWidths=[
            60 * mm,
            110 * mm,
        ]
    )

    overview_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#D9EAF7")
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
            ]
        )
    )

    story.append(
        overview_table
    )

    story.append(
        Spacer(
            1,
            8 * mm
        )
    )

    # --------------------------------------------------------
    # KPI SECTION
    # --------------------------------------------------------

    story.append(
        paragraph(
            "Key Financial Indicators",
            SECTION_STYLE
        )
    )

    story.append(
        create_kpi_table(
            company,
            ratios,
            screener,
            cashflow_intelligence
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # --------------------------------------------------------
    # FINANCIAL HISTORY
    # --------------------------------------------------------

    story.append(
        paragraph(
            "Financial Ratio History",
            SECTION_STYLE
        )
    )

    story.append(
        create_financial_history(
            ratios
        )
    )

    story.append(
        PageBreak()
    )

    # --------------------------------------------------------
    # CASH FLOW INTELLIGENCE
    # --------------------------------------------------------

    story.append(
        paragraph(
            "Cash Flow Intelligence",
            SECTION_STYLE
        )
    )

    story.append(
        create_cashflow_table(
            cashflow_intelligence
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # --------------------------------------------------------
    # PROFIT & LOSS SUMMARY
    # --------------------------------------------------------

    story.append(
        paragraph(
            "Profit & Loss Summary",
            SECTION_STYLE
        )
    )

    latest_pl = latest_row(
        profit_loss
    )

    pl_rows = [
        [
            paragraph("Metric", TABLE_HEADER_STYLE),
            paragraph("Value", TABLE_HEADER_STYLE),
        ],
        [
            paragraph("Sales", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    latest_pl.get("sales")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Operating Profit", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    latest_pl.get(
                        "operating_profit"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Net Profit", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    latest_pl.get(
                        "net_profit"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("EPS", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    latest_pl.get("eps")
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph("Dividend Payout", TABLE_BODY_STYLE),
            paragraph(
                format_number(
                    latest_pl.get(
                        "dividend_payout"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
    ]

    pl_table = Table(
        pl_rows,
        colWidths=[
            75 * mm,
            95 * mm,
        ]
    )

    pl_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#7F6000")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),
            ]
        )
    )

    story.append(
        pl_table
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # --------------------------------------------------------
    # PROS & CONS
    # --------------------------------------------------------

    story.append(
        paragraph(
            "Pros & Cons",
            SECTION_STYLE
        )
    )

    story.append(
        create_pros_cons_table(
            pros_cons
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # --------------------------------------------------------
    # INVESTMENT SIGNALS
    # --------------------------------------------------------

    story.append(
        paragraph(
            "Investment Intelligence",
            SECTION_STYLE
        )
    )

    signal_rows = [
        [
            paragraph(
                "Signal",
                TABLE_HEADER_STYLE
            ),
            paragraph(
                "Assessment",
                TABLE_HEADER_STYLE
            ),
        ],
        [
            paragraph(
                "Quality Category",
                TABLE_BODY_STYLE
            ),
            paragraph(
                format_text(
                    screener.get(
                        "category"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph(
                "Quality Score",
                TABLE_BODY_STYLE
            ),
            paragraph(
                format_number(
                    screener.get(
                        "composite_quality_score"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph(
                "ROE Reliability",
                TABLE_BODY_STYLE
            ),
            paragraph(
                format_text(
                    screener.get(
                        "roe_reliability"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph(
                "CFO Quality",
                TABLE_BODY_STYLE
            ),
            paragraph(
                format_text(
                    cashflow_intelligence.get(
                        "cfo_quality"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
        [
            paragraph(
                "Capital Allocation",
                TABLE_BODY_STYLE
            ),
            paragraph(
                format_text(
                    cashflow_intelligence.get(
                        "capital_allocation_pattern"
                    )
                ),
                TABLE_BODY_STYLE
            ),
        ],
    ]

    signal_table = Table(
        signal_rows,
        colWidths=[
            75 * mm,
            95 * mm,
        ]
    )

    signal_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#7030A0")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),
            ]
        )
    )

    story.append(
        signal_table
    )

    # --------------------------------------------------------
    # DISCLAIMER
    # --------------------------------------------------------

    story.append(
        Spacer(
            1,
            12 * mm
        )
    )

    story.append(
        paragraph(
            "<b>Disclaimer:</b> This tearsheet is generated "
            "from the project's financial datasets and analytical "
            "models. It is intended for research and educational "
            "purposes and should not be treated as investment advice.",
            SMALL_STYLE
        )
    )

    # --------------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------------

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )

    print(
        f"Generated: {output_file}"
    )

    return True


# ============================================================
# GENERATE ALL TEARSHEETS
# ============================================================

def get_company_ids():

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT DISTINCT
            TRIM(id) AS company_id
        FROM companies
        WHERE id IS NOT NULL
          AND TRIM(id) != ''
        ORDER BY id
        """,
        conn
    )

    conn.close()

    return df["company_id"].tolist()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("NIFTY 100 TEARSHEET GENERATOR")
    print("=" * 70)

    print()
    print("Database:")
    print(DB_PATH)

    print()
    print("Output directory:")
    print(OUTPUT_DIR)

    if not DB_PATH.exists():

        print()
        print(
            "ERROR: Database not found."
        )

        raise SystemExit(1)

    company_ids = get_company_ids()

    print()
    print(
        f"Companies found: {len(company_ids)}"
    )

    success = 0
    failed = 0

    print()
    print("=" * 70)
    print("GENERATING TEARSHEETS")
    print("=" * 70)

    for company_id in company_ids:

        try:

            print(
                f"Generating: {company_id}"
            )

            result = build_report(
                company_id
            )

            if result:
                success += 1
            else:
                failed += 1

        except Exception as e:

            failed += 1

            print(
                f"ERROR {company_id}: {e}"
            )

    print()
    print("=" * 70)
    print("FINAL VALIDATION")
    print("=" * 70)

    pdf_files = list(
        OUTPUT_DIR.glob("*.pdf")
    )

    print(
        f"PDF files generated: {len(pdf_files)}"
    )

    print(
        f"Successful: {success}"
    )

    print(
        f"Failed: {failed}"
    )

    print()
    print(
        "Output:",
        OUTPUT_DIR
    )

    print()
    print("=" * 70)
    print("TEARSHEET GENERATION COMPLETED")
    print("=" * 70)