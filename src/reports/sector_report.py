from pathlib import Path

import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output"
SECTOR_REPORT_DIR = OUTPUT_DIR / "sector_reports"

SECTOR_REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUT FILE
# ============================================================

SECTOR_FILE = OUTPUT_DIR / "sector_concentration.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_sector_data():

    if not SECTOR_FILE.exists():
        print(
            f"Sector data file not found: {SECTOR_FILE}"
        )
        return pd.DataFrame()

    try:
        df = pd.read_csv(SECTOR_FILE)
    except Exception as e:
        print(
            f"Could not read sector data: {e}"
        )
        return pd.DataFrame()

    df.columns = [
        str(col).strip().lower()
        for col in df.columns
    ]

    return df


# ============================================================
# FIND SECTOR COLUMN
# ============================================================

def find_column(df, possible_names):

    for name in possible_names:

        if name in df.columns:
            return name

    return None


# ============================================================
# CREATE SECTOR REPORT
# ============================================================

def create_sector_report(
    sector_name,
    sector_df
):

    safe_name = (
        str(sector_name)
        .strip()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    output_file = (
        SECTOR_REPORT_DIR
        / f"{safe_name}_sector_report.pdf"
    )

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    story = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            f"Nifty 100 Financial Intelligence Platform",
            title_style
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            f"Sector Report: {sector_name}",
            heading_style
        )
    )

    story.append(
        Spacer(1, 15)
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    company_col = find_column(
        sector_df,
        [
            "company_id",
            "company",
            "ticker",
            "symbol"
        ]
    )

    weight_col = find_column(
        sector_df,
        [
            "weight",
            "sector_weight",
            "portfolio_weight"
        ]
    )

    industry_col = find_column(
        sector_df,
        [
            "industry"
        ]
    )

    company_count = (
        sector_df[company_col].nunique()
        if company_col
        else len(sector_df)
    )

    total_weight = None

    if weight_col:

        weights = pd.to_numeric(
            sector_df[weight_col],
            errors="coerce"
        )

        total_weight = weights.sum()

    story.append(
        Paragraph(
            f"<b>Companies:</b> {company_count}",
            body_style
        )
    )

    if total_weight is not None:

        story.append(
            Paragraph(
                f"<b>Total Weight:</b> "
                f"{total_weight:.2f}%",
                body_style
            )
        )

    if industry_col:

        industry_count = (
            sector_df[industry_col]
            .dropna()
            .nunique()
        )

        story.append(
            Paragraph(
                f"<b>Industries:</b> "
                f"{industry_count}",
                body_style
            )
        )

    story.append(
        Spacer(1, 15)
    )

    # --------------------------------------------------------
    # COMPANY TABLE
    # --------------------------------------------------------

    table_data = []

    headers = []

    if company_col:
        headers.append("Company")

    if industry_col:
        headers.append("Industry")

    if weight_col:
        headers.append("Weight")

    if headers:
        table_data.append(headers)

        for _, row in sector_df.iterrows():

            values = []

            if company_col:
                values.append(
                    str(row.get(company_col, ""))
                )

            if industry_col:
                values.append(
                    str(row.get(industry_col, ""))
                )

            if weight_col:

                value = pd.to_numeric(
                    row.get(weight_col),
                    errors="coerce"
                )

                if pd.notna(value):
                    values.append(
                        f"{value:.2f}%"
                    )
                else:
                    values.append("N/A")

            table_data.append(values)

    if len(table_data) > 1:

        table = Table(
            table_data,
            repeatRows=1
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.black
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                ]
            )
        )

        story.append(table)

    else:

        story.append(
            Paragraph(
                "No company-level data available.",
                body_style
            )
        )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Generated by the Nifty 100 Financial "
            "Intelligence Platform.",
            body_style
        )
    )

    doc.build(story)

    return output_file


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SECTOR REPORT GENERATION")
    print("=" * 70)

    df = load_sector_data()

    if df.empty:

        print(
            "No sector data available."
        )

        return

    sector_col = find_column(
        df,
        [
            "sector",
            "sector_name",
            "industrials"
        ]
    )

    if not sector_col:

        print(
            "Sector column not found."
        )

        print(
            "Available columns:",
            df.columns.tolist()
        )

        return

    df[sector_col] = (
        df[sector_col]
        .astype(str)
        .str.strip()
    )

    sectors = (
        df[sector_col]
        .dropna()
        .unique()
        .tolist()
    )

    generated = 0

    for sector in sorted(sectors):

        if not sector or sector.lower() == "nan":
            continue

        sector_df = df[
            df[sector_col] == sector
        ].copy()

        try:

            output_file = create_sector_report(
                sector,
                sector_df
            )

            print(
                f"Generated: {output_file}"
            )

            generated += 1

        except Exception as e:

            print(
                f"Failed for {sector}: {e}"
            )

    print()
    print(
        f"Sector reports generated: {generated}"
    )

    print(
        f"Output directory: "
        f"{SECTOR_REPORT_DIR}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()python src\reports\sector_report.py