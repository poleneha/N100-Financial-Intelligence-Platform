import pandas as pd
import sqlite3
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = "data/db/nifty100.db"
OUTPUT_FILE = "output/peer_comparison.xlsx"


# ============================================================
# CONNECT TO DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)


# ============================================================
# LOAD FINANCIAL RATIOS
# ============================================================

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)


# ============================================================
# LOAD PEER GROUPS
# ============================================================

groups = pd.read_sql(
    "SELECT * FROM peer_groups",
    conn
)


conn.close()


print("=" * 70)
print("PEER COMPARISON ANALYSIS")
print("=" * 70)

print()
print("Financial ratios shape:", ratios.shape)
print("Peer groups shape:", groups.shape)


# ============================================================
# FIX PEER GROUP COLUMN NAMES
# ============================================================

groups.columns = [
    "peer_group_id",
    "peer_group_name",
    "company_id",
    "is_benchmark"
]


# ============================================================
# CLEAN COMPANY IDs
# ============================================================

ratios["company_id"] = (
    ratios["company_id"]
    .astype(str)
    .str.upper()
    .str.strip()
)

groups["company_id"] = (
    groups["company_id"]
    .astype(str)
    .str.upper()
    .str.strip()
)


# ============================================================
# CLEAN YEAR
# ============================================================

ratios["year"] = (
    ratios["year"]
    .astype(str)
    .str.strip()
)


# ============================================================
# FINANCIAL METRICS
# ============================================================

metrics = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
    "composite_quality_score"
]


# ============================================================
# SELECT MAR 2024 DATA
# ============================================================

latest = ratios[
    ratios["year"].str.upper() == "MAR 2024"
].copy()


print()
print(
    "Mar 2024 rows before deduplication:",
    len(latest)
)

print(
    "Unique companies before deduplication:",
    latest["company_id"].nunique()
)


# ============================================================
# CHECK AVAILABLE METRICS
# ============================================================

available_metrics = [
    column
    for column in metrics
    if column in latest.columns
]


# ============================================================
# DATA COMPLETENESS
#
# Some companies have multiple Mar 2024 rows.
# We select the row containing the most financial data.
# ============================================================

latest["_data_completeness"] = (
    latest[available_metrics]
    .notna()
    .sum(axis=1)
)


# ============================================================
# SORT BY COMPANY AND DATA COMPLETENESS
# ============================================================

latest = latest.sort_values(
    by=[
        "company_id",
        "_data_completeness"
    ],
    ascending=[
        True,
        False
    ]
)


# ============================================================
# KEEP ONE FINANCIAL RECORD PER COMPANY
# ============================================================

latest = latest.drop_duplicates(
    subset=["company_id"],
    keep="first"
)


# Remove temporary column
latest = latest.drop(
    columns=["_data_completeness"]
)


print(
    "Rows after financial deduplication:",
    len(latest)
)

print(
    "Unique companies after financial deduplication:",
    latest["company_id"].nunique()
)


# ============================================================
# CLEAN PEER GROUP DATA
#
# A company should belong to only one peer group.
# If duplicate peer-group records exist, keep the first one.
# ============================================================

groups = groups.sort_values(
    by=[
        "company_id",
        "is_benchmark"
    ],
    ascending=[
        True,
        False
    ]
)


groups = groups.drop_duplicates(
    subset=["company_id"],
    keep="first"
)


print()
print(
    "Unique peer-group companies:",
    groups["company_id"].nunique()
)


# ============================================================
# MERGE FINANCIAL DATA WITH PEER GROUPS
# ============================================================

data = latest.merge(
    groups[
        [
            "peer_group_name",
            "company_id",
            "is_benchmark"
        ]
    ],
    on="company_id",
    how="inner",
    validate="one_to_one"
)


print()
print(
    "Companies matched to peer groups:",
    len(data)
)

print(
    "Unique matched companies:",
    data["company_id"].nunique()
)


# ============================================================
# FINAL SAFETY DEDUPLICATION
# ============================================================

data = data.drop_duplicates(
    subset=["company_id"],
    keep="first"
)


print(
    "Rows after final deduplication:",
    len(data)
)


# ============================================================
# CREATE EXCEL WRITER
# ============================================================

writer = pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
)


# ============================================================
# CREATE ONE SHEET FOR EACH PEER GROUP
# ============================================================

peer_group_names = (
    data["peer_group_name"]
    .dropna()
    .astype(str)
    .unique()
)


for group in peer_group_names:

    print()
    print(
        "Creating sheet:",
        group
    )


    # --------------------------------------------------------
    # FILTER PEER GROUP
    # --------------------------------------------------------

    sheet = data[
        data["peer_group_name"] == group
    ].copy()


    # --------------------------------------------------------
    # SELECT OUTPUT COLUMNS
    # --------------------------------------------------------

    columns = [
        "company_id",
        "year",
        "is_benchmark"
    ]


    columns += [
        metric
        for metric in metrics
        if metric in sheet.columns
    ]


    sheet = sheet[columns]


    # --------------------------------------------------------
    # SORT BENCHMARK FIRST
    # --------------------------------------------------------

    sheet = sheet.sort_values(
        by=[
            "is_benchmark",
            "company_id"
        ],
        ascending=[
            False,
            True
        ]
    )


    # --------------------------------------------------------
    # WRITE SHEET
    # --------------------------------------------------------

    sheet.to_excel(
        writer,
        sheet_name=str(group)[:31],
        index=False
    )


# ============================================================
# CLOSE WRITER
# ============================================================

writer.close()


print()
print(
    "Excel workbook created:"
)

print(
    OUTPUT_FILE
)


# ============================================================
# LOAD WORKBOOK FOR FORMATTING
# ============================================================

wb = load_workbook(
    OUTPUT_FILE
)


# ============================================================
# EXCEL STYLES
# ============================================================

green = PatternFill(
    start_color="C6EFCE",
    end_color="C6EFCE",
    fill_type="solid"
)

yellow = PatternFill(
    start_color="FFEB9C",
    end_color="FFEB9C",
    fill_type="solid"
)

red = PatternFill(
    start_color="FFC7CE",
    end_color="FFC7CE",
    fill_type="solid"
)


# ============================================================
# FORMAT ALL WORKSHEETS
# ============================================================

for ws in wb.worksheets:

    # --------------------------------------------------------
    # FREEZE HEADER
    # --------------------------------------------------------

    ws.freeze_panes = "A2"


    # --------------------------------------------------------
    # HEADER FORMATTING
    # --------------------------------------------------------

    for cell in ws[1]:

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )


    # --------------------------------------------------------
    # COLUMN WIDTH
    # --------------------------------------------------------

    for column_cells in ws.columns:

        max_length = 0

        column_letter = (
            column_cells[0].column_letter
        )


        for cell in column_cells:

            if cell.value is not None:

                max_length = max(
                    max_length,
                    len(str(cell.value))
                )


        ws.column_dimensions[
            column_letter
        ].width = min(
            max(max_length + 2, 14),
            25
        )


    # --------------------------------------------------------
    # FIND BENCHMARK COLUMN
    # --------------------------------------------------------

    headers = [
        cell.value
        for cell in ws[1]
    ]


    benchmark_column = None


    if "is_benchmark" in headers:

        benchmark_column = (
            headers.index("is_benchmark") + 1
        )


    # --------------------------------------------------------
    # HIGHLIGHT BENCHMARK
    # --------------------------------------------------------

    if benchmark_column is not None:

        for row_number in range(
            2,
            ws.max_row + 1
        ):

            benchmark_value = ws.cell(
                row=row_number,
                column=benchmark_column
            ).value


            # Handle 1 / 0, True / False and text values
            is_benchmark = (
                str(benchmark_value)
                .strip()
                .lower()
                in [
                    "1",
                    "true",
                    "yes"
                ]
            )


            if is_benchmark:

                for column_number in range(
                    1,
                    ws.max_column + 1
                ):

                    ws.cell(
                        row=row_number,
                        column=column_number
                    ).fill = yellow


    # --------------------------------------------------------
    # NUMBER FORMATTING
    # --------------------------------------------------------

    for row in ws.iter_rows(
        min_row=2
    ):

        for cell in row:

            if isinstance(
                cell.value,
                float
            ):

                cell.number_format = "0.00"


    # --------------------------------------------------------
    # CENTER BASIC COLUMNS
    # --------------------------------------------------------

    for row in ws.iter_rows(
        min_row=2
    ):

        for cell in row:

            if cell.column <= 3:

                cell.alignment = Alignment(
                    horizontal="center"
                )


# ============================================================
# SAVE FORMATTED WORKBOOK
# ============================================================

wb.save(
    OUTPUT_FILE
)


# ============================================================
# FINAL VALIDATION
# ============================================================

excel_file = pd.ExcelFile(
    OUTPUT_FILE
)


all_sheets = []


for sheet_name in excel_file.sheet_names:

    sheet_df = pd.read_excel(
        OUTPUT_FILE,
        sheet_name=sheet_name
    )


    # Add peer group name for validation
    sheet_df["peer_group_name"] = sheet_name


    all_sheets.append(
        sheet_df
    )


# ============================================================
# COMBINE ALL PEER GROUP SHEETS
# ============================================================

all_data = pd.concat(
    all_sheets,
    ignore_index=True
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print()
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

print()

print(
    "Total rows:",
    len(all_data)
)

print(
    "Unique companies:",
    all_data["company_id"].nunique()
)

print(
    "Duplicate company rows:",
    all_data["company_id"].duplicated().sum()
)

print(
    "Missing company IDs:",
    all_data["company_id"].isna().sum()
)

print(
    "Peer groups:",
    len(excel_file.sheet_names)
)


# ============================================================
# COMPANIES PER PEER GROUP
# ============================================================

print()
print(
    "Companies per peer group:"
)


group_counts = (
    all_data
    .groupby("peer_group_name")["company_id"]
    .nunique()
    .sort_values(
        ascending=False
    )
)


print(
    group_counts.to_string()
)


# ============================================================
# DUPLICATE COMPANY CHECK
# ============================================================

duplicates = all_data[
    all_data["company_id"].duplicated(
        keep=False
    )
].sort_values(
    "company_id"
)


print()


if len(duplicates) > 0:

    print(
        "WARNING: Duplicate companies found:"
    )

    print(
        duplicates[
            [
                "company_id",
                "peer_group_name"
            ]
        ].to_string(
            index=False
        )
    )

else:

    print(
        "Duplicate check: PASSED"
    )


# ============================================================
# SHEETS CREATED
# ============================================================

print()
print(
    "Sheets created:"
)


for sheet_name in excel_file.sheet_names:

    print(
        " -",
        sheet_name
    )


# ============================================================
# FINAL COMPLETION MESSAGE
# ============================================================

print()
print("=" * 70)
print("PEER COMPARISON COMPLETED SUCCESSFULLY")
print("=" * 70)

print()

print(
    "Companies:",
    all_data["company_id"].nunique()
)

print(
    "Rows:",
    len(all_data)
)

print(
    "Saved:",
    OUTPUT_FILE
)

print()