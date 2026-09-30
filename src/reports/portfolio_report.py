"""
NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
Portfolio Summary Report

Combines:
    - Portfolio scoring
    - Cluster profiling
    - Outlier detection
    - Portfolio statistics
    - Sector information

Output:
    reports/portfolio/portfolio_summary.pdf
"""

import os
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "reports",
    "portfolio"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "portfolio_summary.pdf"
)

PORTFOLIO_FILE = os.path.join(
    BASE_DIR,
    "output",
    "portfolio_scoring.csv"
)

TOP_FILE = os.path.join(
    BASE_DIR,
    "output",
    "top_ranked_companies.csv"
)

CLUSTER_FILE = os.path.join(
    BASE_DIR,
    "output",
    "cluster_profiles.csv"
)

OUTLIER_FILE = os.path.join(
    BASE_DIR,
    "output",
    "outlier_report.csv"
)

STATS_FILE = os.path.join(
    BASE_DIR,
    "output",
    "portfolio_stats.csv"
)

SECTOR_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "sectors.xlsx"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("NIFTY 100 - PORTFOLIO SUMMARY REPORT")
print("=" * 70)

print("Loading portfolio scoring data...")

portfolio = pd.read_csv(
    PORTFOLIO_FILE
)

print(
    f"Portfolio companies: "
    f"{portfolio['company_id'].nunique()}"
)

print("Loading cluster profiles...")

if os.path.exists(CLUSTER_FILE):
    clusters = pd.read_csv(CLUSTER_FILE)
else:
    clusters = pd.DataFrame()

print("Loading outlier data...")

if os.path.exists(OUTLIER_FILE):
    outliers = pd.read_csv(OUTLIER_FILE)
else:
    outliers = pd.DataFrame()

print("Loading portfolio statistics...")

if os.path.exists(STATS_FILE):
    stats = pd.read_csv(STATS_FILE)
else:
    stats = pd.DataFrame()

print("Loading sector data...")

sectors = pd.read_excel(
    SECTOR_FILE
)


# ============================================================
# MERGE SECTOR INFORMATION
# ============================================================

portfolio["company_id"] = (
    portfolio["company_id"]
    .astype(str)
    .str.strip()
)

sectors["company_id"] = (
    sectors["company_id"]
    .astype(str)
    .str.strip()
)

sector_columns = [
    "company_id",
    "broad_sector",
    "sub_sector",
]

available_sector_columns = [
    col
    for col in sector_columns
    if col in sectors.columns
]

portfolio = portfolio.merge(
    sectors[available_sector_columns],
    on="company_id",
    how="left"
)


# ============================================================
# SUMMARY VALUES
# ============================================================

total_companies = portfolio["company_id"].nunique()

strong_count = (
    portfolio["investment_category"]
    .eq("Strong")
    .sum()
)

good_count = (
    portfolio["investment_category"]
    .eq("Good")
    .sum()
)

moderate_count = (
    portfolio["investment_category"]
    .eq("Moderate")
    .sum()
)

weak_count = (
    portfolio["investment_category"]
    .eq("Weak")
    .sum()
)

high_risk_count = (
    portfolio["investment_category"]
    .eq("High Risk")
    .sum()
)

average_score = (
    portfolio["investment_score"]
    .mean()
)

median_score = (
    portfolio["investment_score"]
    .median()
)

cluster_count = (
    portfolio["cluster_id"]
    .nunique()
)

outlier_count = (
    outliers["company_id"].nunique()
    if not outliers.empty
    and "company_id" in outliers.columns
    else 0
)


# ============================================================
# REPORTLAB STYLES
# ============================================================

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ReportTitle",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=20,
    leading=24,
    spaceAfter=20,
)

heading_style = ParagraphStyle(
    "Heading",
    parent=styles["Heading2"],
    fontSize=14,
    leading=18,
    spaceBefore=12,
    spaceAfter=8,
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontSize=9,
    leading=13,
)

small_style = ParagraphStyle(
    "Small",
    parent=styles["BodyText"],
    fontSize=8,
    leading=11,
)


# ============================================================
# PDF DOCUMENT
# ============================================================

doc = SimpleDocTemplate(
    OUTPUT_FILE,
    pagesize=A4,
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36,
)

story = []


# ============================================================
# TITLE
# ============================================================

story.append(
    Paragraph(
        "Nifty 100 Portfolio Summary Report",
        title_style
    )
)

story.append(
    Paragraph(
        "Financial Intelligence & Investment Ranking",
        ParagraphStyle(
            "Subtitle",
            parent=body_style,
            alignment=TA_CENTER,
            fontSize=10,
            spaceAfter=20,
        )
    )
)


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

story.append(
    Paragraph(
        "1. Executive Summary",
        heading_style
    )
)

summary_text = f"""
This report summarizes the financial intelligence analysis of
<b>{total_companies}</b> Nifty 100 companies. The analysis combines
financial performance, growth, profitability, leverage, cash-flow
indicators, clustering results and sector-level outlier detection.

The portfolio contains <b>{cluster_count}</b> financial clusters.
The average investment score is <b>{average_score:.2f}/100</b>,
while the median score is <b>{median_score:.2f}/100</b>.
A total of <b>{outlier_count}</b> companies were identified as
sector-level financial outliers.
"""

story.append(
    Paragraph(
        summary_text,
        body_style
    )
)

story.append(Spacer(1, 12))


# ============================================================
# KPI TABLE
# ============================================================

story.append(
    Paragraph(
        "Portfolio Classification",
        heading_style
    )
)

kpi_data = [
    ["Category", "Companies"],
    ["Strong", str(strong_count)],
    ["Good", str(good_count)],
    ["Moderate", str(moderate_count)],
    ["Weak", str(weak_count)],
    ["High Risk", str(high_risk_count)],
]

kpi_table = Table(
    kpi_data,
    colWidths=[3.5 * inch, 1.5 * inch]
)

kpi_table.setStyle(
    TableStyle(
        [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "ALIGN",
                (1, 1),
                (1, -1),
                "CENTER",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9,
            ),
        ]
    )
)

story.append(kpi_table)

story.append(PageBreak())


# ============================================================
# TOP RANKED COMPANIES
# ============================================================

story.append(
    Paragraph(
        "2. Top Ranked Companies",
        heading_style
    )
)

top20 = (
    portfolio
    .sort_values(
        "investment_score",
        ascending=False
    )
    .head(20)
)

top_data = [
    [
        "Rank",
        "Company",
        "Cluster",
        "Score",
        "Category",
    ]
]

for _, row in top20.iterrows():

    cluster_name = str(
        row.get(
            "cluster_name",
            "N/A"
        )
    )

    category = str(
        row.get(
            "investment_category",
            "N/A"
        )
    )

    top_data.append(
        [
            str(row["rank"]),
            str(row["company_id"]),
            cluster_name,
            f"{float(row['investment_score']):.2f}",
            category,
        ]
    )

top_table = Table(
    top_data,
    colWidths=[
        0.45 * inch,
        0.85 * inch,
        2.25 * inch,
        0.65 * inch,
        0.85 * inch,
    ]
)

top_table.setStyle(
    TableStyle(
        [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.grey,
            ),
            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "CENTER",
            ),
            (
                "ALIGN",
                (3, 1),
                (3, -1),
                "CENTER",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5,
            ),
        ]
    )
)

story.append(top_table)

story.append(PageBreak())


# ============================================================
# CLUSTER OVERVIEW
# ============================================================

story.append(
    Paragraph(
        "3. Cluster Overview",
        heading_style
    )
)

cluster_summary = (
    portfolio
    .groupby(
        ["cluster_id", "cluster_name"],
        as_index=False
    )
    .agg(
        company_count=("company_id", "nunique"),
        average_score=("investment_score", "mean"),
    )
    .sort_values(
        "average_score",
        ascending=False
    )
)

cluster_data = [
    [
        "Cluster",
        "Name",
        "Companies",
        "Avg Score",
    ]
]

for _, row in cluster_summary.iterrows():

    cluster_data.append(
        [
            str(row["cluster_id"]),
            str(row["cluster_name"]),
            str(row["company_count"]),
            f"{row['average_score']:.2f}",
        ]
    )

cluster_table = Table(
    cluster_data,
    colWidths=[
        0.6 * inch,
        2.8 * inch,
        1.0 * inch,
        1.0 * inch,
    ]
)

cluster_table.setStyle(
    TableStyle(
        [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.grey,
            ),
            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "CENTER",
            ),
            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "CENTER",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
        ]
    )
)

story.append(cluster_table)

story.append(Spacer(1, 15))

for _, row in cluster_summary.iterrows():

    paragraph = f"""
    <b>{row['cluster_name']}</b> contains
    {int(row['company_count'])} companies with an average
    investment score of {row['average_score']:.2f}.
    """

    story.append(
        Paragraph(
            paragraph,
            body_style
        )
    )

    story.append(
        Spacer(1, 5)
    )


story.append(PageBreak())


# ============================================================
# OUTLIER ANALYSIS
# ============================================================

story.append(
    Paragraph(
        "4. Sector-Wise Outlier Analysis",
        heading_style
    )
)

if outliers.empty:

    story.append(
        Paragraph(
            "No sector-level outliers were detected.",
            body_style
        )
    )

else:

    outlier_data = [
        [
            "Company",
            "Sector",
            "Metric",
            "Value",
            "Z-Score",
            "Severity",
        ]
    ]

    for _, row in outliers.iterrows():

        outlier_data.append(
            [
                str(
                    row.get(
                        "company_id",
                        "N/A"
                    )
                ),
                str(
                    row.get(
                        "broad_sector",
                        "N/A"
                    )
                ),
                str(
                    row.get(
                        "metric",
                        "N/A"
                    )
                ),
                f"{float(row.get('value', 0)):.2f}",
                f"{float(row.get('z_score', 0)):.2f}",
                str(
                    row.get(
                        "severity",
                        "N/A"
                    )
                ),
            ]
        )

    outlier_table = Table(
        outlier_data,
        colWidths=[
            0.8 * inch,
            1.0 * inch,
            1.25 * inch,
            0.7 * inch,
            0.7 * inch,
            0.7 * inch,
        ]
    )

    outlier_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
            ]
        )
    )

    story.append(outlier_table)


story.append(Spacer(1, 15))

story.append(
    Paragraph(
        f"""
        The analysis identified <b>{outlier_count}</b>
        sector-level outlier companies. These observations should
        be reviewed separately because extreme financial ratios
        can materially influence portfolio rankings and cluster
        characteristics.
        """,
        body_style
    )
)


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

story.append(PageBreak())

story.append(
    Paragraph(
        "5. Portfolio Statistics",
        heading_style
    )
)

if not stats.empty:

    stats_data = [
        [
            "KPI",
            "P10",
            "P50",
            "P90",
            "Mean",
            "Std",
        ]
    ]

    for _, row in stats.iterrows():

        def fmt(value):
            try:
                return f"{float(value):.2f}"
            except Exception:
                return "N/A"

        stats_data.append(
            [
                str(row.get("kpi", "N/A")),
                fmt(row.get("P10")),
                fmt(row.get("P50")),
                fmt(row.get("P90")),
                fmt(row.get("Mean")),
                fmt(row.get("Std")),
            ]
        )

    stats_table = Table(
        stats_data,
        colWidths=[
            1.7 * inch,
            0.75 * inch,
            0.75 * inch,
            0.75 * inch,
            0.85 * inch,
            0.75 * inch,
        ]
    )

    stats_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
            ]
        )
    )

    story.append(stats_table)

else:

    story.append(
        Paragraph(
            "Portfolio statistics file was not available.",
            body_style
        )
    )


# ============================================================
# KEY INSIGHTS
# ============================================================

story.append(Spacer(1, 20))

story.append(
    Paragraph(
        "6. Key Insights",
        heading_style
    )
)

best_company = (
    portfolio
    .sort_values(
        "investment_score",
        ascending=False
    )
    .iloc[0]
)

highest_cluster = (
    cluster_summary.iloc[0]
)

insights = [
    f"The highest-ranked company is "
    f"<b>{best_company['company_id']}</b> with an investment "
    f"score of <b>{best_company['investment_score']:.2f}</b>.",

    f"The highest-scoring cluster by average investment score "
    f"is <b>{highest_cluster['cluster_name']}</b>.",

    f"The portfolio contains "
    f"<b>{strong_count}</b> Strong and "
    f"<b>{good_count}</b> Good investment candidates.",

    f"<b>{moderate_count}</b> companies are classified as "
    f"Moderate, indicating that additional company-level "
    f"analysis may be useful before making an investment decision.",

    f"<b>{high_risk_count}</b> companies are classified as "
    f"High Risk based on the scoring framework.",

    f"<b>{outlier_count}</b> sector-level financial outliers "
    f"were detected and should receive additional review.",
]

for insight in insights:

    story.append(
        Paragraph(
            "• " + insight,
            body_style
        )
    )

    story.append(
        Spacer(1, 7)
    )


# ============================================================
# DISCLAIMER
# ============================================================

story.append(Spacer(1, 20))

story.append(
    Paragraph(
        """
        <b>Note:</b> This report is an analytical output of the
        Nifty 100 Financial Intelligence Platform. Investment
        scores are based on the project's defined financial
        scoring methodology and should not be interpreted as
        personalized financial advice or a guarantee of future
        investment performance.
        """,
        small_style
    )
)


# ============================================================
# BUILD PDF
# ============================================================

print("\nGenerating Portfolio Summary PDF...")

doc.build(story)

print(
    f"Generated: {OUTPUT_FILE}"
)

print("\n" + "=" * 70)
print("PORTFOLIO REPORT GENERATION COMPLETED")
print("=" * 70)