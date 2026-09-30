from pathlib import Path

import pandas as pd

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"

COMPANIES_FILE = RAW_DIR / "companies.xlsx"
SECTORS_FILE = RAW_DIR / "sectors.xlsx"

OUTPUT_DIR = BASE_DIR / "output" / "sector_reports"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("NIFTY 100 SECTOR REPORT GENERATOR")
print("=" * 70)

print()
print("Database/project directory:")
print(BASE_DIR)

print()
print("Companies file:")
print(COMPANIES_FILE)

print()
print("Sectors file:")
print(SECTORS_FILE)

print()
print("Output directory:")
print(OUTPUT_DIR)


# ============================================================
# CHECK INPUT FILES
# ============================================================

if not COMPANIES_FILE.exists():
    raise FileNotFoundError(
        f"Companies file not found:\n{COMPANIES_FILE}"
    )

if not SECTORS_FILE.exists():
    raise FileNotFoundError(
        f"Sectors file not found:\n{SECTORS_FILE}"
    )


# ============================================================
# LOAD COMPANIES
# ============================================================

companies = pd.read_excel(
    COMPANIES_FILE,
    header=1
)


# ============================================================
# LOAD SECTORS
# ============================================================

sectors = pd.read_excel(
    SECTORS_FILE,
    header=None
)


# ============================================================
# CLEAN SECTOR DATA
# ============================================================

sectors = sectors.iloc[1:].copy()

sectors.columns = [
    "sector_id",
    "company_id",
    "sector",
    "industry",
    "weight",
    "market_cap_category"
]


# ============================================================
# CLEAN VALUES
# ============================================================

sectors["company_id"] = (
    sectors["company_id"]
    .astype(str)
    .str.strip()
)

sectors["sector"] = (
    sectors["sector"]
    .astype(str)
    .str.strip()
)

sectors["industry"] = (
    sectors["industry"]
    .astype(str)
    .str.strip()
)

sectors["market_cap_category"] = (
    sectors["market_cap_category"]
    .astype(str)
    .str.strip()
)

sectors["weight"] = pd.to_numeric(
    sectors["weight"],
    errors="coerce"
)


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

sectors = sectors[
    sectors["company_id"].notna()
].copy()

sectors = sectors[
    sectors["sector"].notna()
].copy()

sectors = sectors[
    sectors["company_id"].str.lower() != "nan"
].copy()

sectors = sectors[
    sectors["sector"].str.lower() != "nan"
].copy()


# ============================================================
# DATA INFORMATION
# ============================================================

print()
print("=" * 70)
print("DATA VALIDATION")
print("=" * 70)

print()
print("Companies columns:")
print(companies.columns.tolist())

print()
print("Sector columns:")
print(sectors.columns.tolist())

print()
print("Total companies:")
print(len(sectors))

print()
print("Sectors found:")

for sector_name in sorted(
    sectors["sector"].unique()
):
    print(" -", sector_name)


# ============================================================
# PDF STYLES
# ============================================================

styles = getSampleStyleSheet()

title_style = styles["Title"]

normal_style = styles["BodyText"]


# ============================================================
# GENERATE SECTOR REPORTS
# ============================================================

print()
print("=" * 70)
print("GENERATING SECTOR REPORTS")
print("=" * 70)

generated = 0
failed = 0


for sector_name, group in sectors.groupby(
    "sector",
    dropna=True
):

    try:

        # ----------------------------------------------------
        # SAFE FILE NAME
        # ----------------------------------------------------

        safe_name = (
            str(sector_name)
            .strip()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace("&", "and")
            .replace(":", "_")
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # ALL PDF FILES GO INTO output/sector_reports
        # ----------------------------------------------------

        output_file = (
            OUTPUT_DIR /
            f"{safe_name}_report.pdf"
        )


        print()
        print(
            f"Generating: {sector_name}"
        )


        # ----------------------------------------------------
        # PDF DOCUMENT
        # ----------------------------------------------------

        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )


        story = []


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        story.append(
            Paragraph(
                f"{sector_name} Sector Intelligence Report",
                title_style
            )
        )

        story.append(
            Spacer(1, 15)
        )


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        company_count = len(group)

        industry_count = (
            group["industry"]
            .nunique()
        )

        total_weight = (
            group["weight"]
            .fillna(0)
            .sum()
        )


        story.append(
            Paragraph(
                f"<b>Total Companies:</b> "
                f"{company_count}",
                normal_style
            )
        )

        story.append(
            Spacer(1, 5)
        )

        story.append(
            Paragraph(
                f"<b>Industries:</b> "
                f"{industry_count}",
                normal_style
            )
        )

        story.append(
            Spacer(1, 5)
        )

        story.append(
            Paragraph(
                f"<b>Total Sector Weight:</b> "
                f"{total_weight:.2f}",
                normal_style
            )
        )

        story.append(
            Spacer(1, 15)
        )


        # ----------------------------------------------------
        # COMPANY TABLE
        # ----------------------------------------------------

        table_data = [
            [
                "Company ID",
                "Industry",
                "Weight %",
                "Market Cap"
            ]
        ]


        for _, row in group.iterrows():

            if pd.isna(row["weight"]):
                weight_text = "N/A"
            else:
                weight_text = (
                    f"{float(row['weight']):.2f}"
                )


            table_data.append(
                [
                    str(row["company_id"]),
                    str(row["industry"]),
                    weight_text,
                    str(row["market_cap_category"])
                ]
            )


        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[
                80,
                150,
                70,
                100
            ]
        )


        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.grey
                    ),

                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
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
                        "MIDDLE"
                    ),

                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, 0),
                        7
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        7
                    )
                ]
            )
        )


        story.append(table)


        # ----------------------------------------------------
        # BUILD PDF
        # ----------------------------------------------------

        doc.build(story)


        generated += 1


        print(
            "Created:",
            output_file
        )


    except Exception as e:

        failed += 1

        print()
        print(
            f"FAILED: {sector_name}"
        )

        print(
            "Error:",
            e
        )


# ============================================================
# FINAL VALIDATION
# ============================================================

pdf_files = list(
    OUTPUT_DIR.glob("*.pdf")
)

expected_sectors = (
    sectors["sector"].nunique()
)


print()
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

print()
print(
    "Expected sector reports:",
    expected_sectors
)

print(
    "PDF files found:",
    len(pdf_files)
)

print(
    "Successfully generated:",
    generated
)

print(
    "Failed:",
    failed
)

print()
print("Output directory:")
print(OUTPUT_DIR)


# ============================================================
# LIST GENERATED FILES
# ============================================================

print()
print("Generated files:")

for pdf in sorted(pdf_files):

    print(
        f" - {pdf.name} "
        f"({pdf.stat().st_size} bytes)"
    )


# ============================================================
# COMPLETION
# ============================================================

print()
print("=" * 70)

if (
    failed == 0
    and len(pdf_files) == expected_sectors
):

    print(
        "SECTOR REPORT GENERATION COMPLETED SUCCESSFULLY"
    )

else:

    print(
        "SECTOR REPORT GENERATION COMPLETED - REVIEW REQUIRED"
    )

print("=" * 70)