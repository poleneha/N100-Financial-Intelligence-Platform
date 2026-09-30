from pathlib import Path
import pandas as pd
import subprocess
import sys


# ============================================================
# NIFTY 100 - FINAL SPRINT 5 VALIDATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output"
TEARSHEET_DIR = OUTPUT_DIR / "tearsheets"
SECTOR_DIR = OUTPUT_DIR / "sector_reports"


print()
print("=" * 70)
print("NIFTY 100 - FINAL SPRINT 5 VALIDATION")
print("=" * 70)


# ============================================================
# 1. COMPANY TEARSHEETS
# ============================================================

print()
print("[1] COMPANY TEARSHEETS")

if TEARSHEET_DIR.exists():

    files = list(TEARSHEET_DIR.glob("*.pdf"))

    print("Expected : 92")
    print("Found    :", len(files))

    if len(files) == 92:
        print("STATUS   : PASSED")
    else:
        print("STATUS   : REVIEW REQUIRED")

else:

    print("STATUS   : FAILED - folder not found")


# ============================================================
# 2. SECTOR REPORTS
# ============================================================

print()
print("[2] SECTOR REPORTS")

if SECTOR_DIR.exists():

    files = list(SECTOR_DIR.glob("*.pdf"))

    print("Expected : 10")
    print("Found    :", len(files))

    if len(files) == 10:
        print("STATUS   : PASSED")
    else:
        print("STATUS   : REVIEW REQUIRED")

else:

    print("STATUS   : FAILED - folder not found")


# ============================================================
# 3. CASH FLOW INTELLIGENCE
# ============================================================

print()
print("[3] CASH FLOW INTELLIGENCE")

cashflow_file = OUTPUT_DIR / "cashflow_intelligence.xlsx"

if cashflow_file.exists():

    df = pd.read_excel(
        cashflow_file,
        sheet_name="Cashflow_Intelligence"
    )

    rows = len(df)
    companies = df["company_id"].nunique()
    duplicates = rows - companies

    print("Rows       :", rows)
    print("Companies  :", companies)
    print("Duplicates :", duplicates)

    if "cashflow_data_status" in df.columns:

        print()
        print("Cash Flow Status:")

        print(
            df["cashflow_data_status"]
            .value_counts(dropna=False)
            .to_string()
        )

    if (
        rows == 92
        and companies == 92
        and duplicates == 0
    ):

        print("STATUS     : PASSED")

    else:

        print("STATUS     : REVIEW REQUIRED")

else:

    print("STATUS     : FAILED - file not found")


# ============================================================
# 4. CAPITAL ALLOCATION
# ============================================================

print()
print("[4] CAPITAL ALLOCATION")

capital_file = OUTPUT_DIR / "capital_allocation.csv"

if capital_file.exists():

    df = pd.read_csv(capital_file)

    rows = len(df)
    companies = df["company_id"].nunique()
    duplicates = rows - companies

    print("Rows       :", rows)
    print("Companies  :", companies)
    print("Duplicates :", duplicates)

    print()
    print("Capital Allocation:")

    print(
        df["capital_allocation_pattern"]
        .value_counts(dropna=False)
        .to_string()
    )

    if (
        rows == 92
        and companies == 92
        and duplicates == 0
    ):

        print("STATUS     : PASSED")

    else:

        print("STATUS     : REVIEW REQUIRED")

else:

    print("STATUS     : FAILED - file not found")


# ============================================================
# 5. PEER COMPARISON
# ============================================================

print()
print("[5] PEER COMPARISON")

peer_file = OUTPUT_DIR / "peer_comparison.xlsx"

if peer_file.exists():

    excel = pd.ExcelFile(peer_file)

    print("Sheets     :", len(excel.sheet_names))

    all_data = []

    for sheet in excel.sheet_names:

        try:

            temp = pd.read_excel(
                peer_file,
                sheet_name=sheet
            )

            if not temp.empty:

                all_data.append(temp)

        except Exception as e:

            print(
                f"Warning: could not read sheet {sheet}: {e}"
            )

    if all_data:

        peer_df = pd.concat(
            all_data,
            ignore_index=True
        )

        if "company_id" in peer_df.columns:

            rows = len(peer_df)
            companies = peer_df["company_id"].nunique()
            duplicates = rows - companies

            print("Rows       :", rows)
            print("Companies  :", companies)
            print("Duplicates :", duplicates)

            if (
                rows >= 54
                and companies >= 54
            ):

                print("STATUS     : PASSED")

            else:

                print("STATUS     : REVIEW REQUIRED")

        else:

            print(
                "STATUS     : REVIEW REQUIRED - company_id missing"
            )

    else:

        print(
            "STATUS     : REVIEW REQUIRED - no data found"
        )

else:

    print("STATUS     : FAILED - file not found")


# ============================================================
# 6. REPORT DATA
# ============================================================

print()
print("[6] REPORT DATA")

report_data = BASE_DIR / "src" / "reports" / "report_data.py"

result = subprocess.run(
    [sys.executable, str(report_data)],
    cwd=str(BASE_DIR)
)

if result.returncode == 0:

    print("STATUS     : PASSED")

else:

    print("STATUS     : FAILED")


# ============================================================
# 7. TEARSHEET CODE VALIDATION
# ============================================================

print()
print("[7] TEARSHEET CODE VALIDATION")

tearsheet_file = BASE_DIR / "src" / "reports" / "tearsheet.py"

result = subprocess.run(
    [
        sys.executable,
        "-m",
        "py_compile",
        str(tearsheet_file)
    ],
    cwd=str(BASE_DIR)
)

if result.returncode == 0:

    print("STATUS     : PASSED")

else:

    print("STATUS     : FAILED")


# ============================================================
# 8. SECTOR REPORT CODE VALIDATION
# ============================================================

print()
print("[8] SECTOR REPORT CODE VALIDATION")

sector_file = BASE_DIR / "src" / "reports" / "sector_report.py"

result = subprocess.run(
    [
        sys.executable,
        "-m",
        "py_compile",
        str(sector_file)
    ],
    cwd=str(BASE_DIR)
)

if result.returncode == 0:

    print("STATUS     : PASSED")

else:

    print("STATUS     : FAILED")


# ============================================================
# 9. OUTPUT FILE SUMMARY
# ============================================================

print()
print("[9] OUTPUT FILE SUMMARY")

if OUTPUT_DIR.exists():

    xlsx = list(OUTPUT_DIR.rglob("*.xlsx"))
    csv = list(OUTPUT_DIR.rglob("*.csv"))
    pdf = list(OUTPUT_DIR.rglob("*.pdf"))

    print("Excel files :", len(xlsx))
    print("CSV files   :", len(csv))
    print("PDF files   :", len(pdf))

else:

    print("Output directory not found.")


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 70)
print("SPRINT 5 VALIDATION COMPLETED")
print("=" * 70)

print()
print("Expected major deliverables:")
print("  Company tearsheets : 92")
print("  Sector reports     : 10")
print("  Cashflow companies  : 92")
print("  Capital allocation : 92")

print()
print("PDF total should be:")
print("  92 + 10 = 102")

print()
print("FINAL STATUS: VALIDATION COMPLETED")
print("=" * 70)