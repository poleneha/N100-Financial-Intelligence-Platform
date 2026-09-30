import pandas as pd
import os

os.makedirs("output", exist_ok=True)


def generate_capital_report():

    input_file = "output/capital_allocation.csv"
    cashflow_file = "output/cashflow_intelligence.xlsx"


    df = pd.read_csv(input_file)


    print("Columns:")
    print(df.columns.tolist())


    # Convert year properly
    df["year"] = df["year"].astype(str)


    # Latest year summary

    latest_year = df["year"].max()

    latest = df[
        df["year"] == latest_year
    ]


    # Pattern distribution

    summary = (
        latest["pattern_label"]
        .value_counts()
        .reset_index()
    )

    summary.columns = [
        "pattern",
        "company_count"
    ]


    summary.to_csv(
        "output/capital_pattern_summary.csv",
        index=False
    )


    # Detect pattern changes

    df = df.sort_values(
        ["company_id", "year"]
    )


    df["previous_pattern"] = (
        df.groupby("company_id")["pattern_label"]
        .shift(1)
    )


    changes = df[
        (df["previous_pattern"].notna()) &
        (df["previous_pattern"] != df["pattern_label"])
    ]


    changes = changes[
        [
            "company_id",
            "year",
            "previous_pattern",
            "pattern_label"
        ]
    ]


    changes.columns = [
        "company_id",
        "year",
        "old_pattern",
        "new_pattern"
    ]


    changes.to_csv(
        "output/pattern_changes.csv",
        index=False
    )


    # Add capital allocation to cashflow file

    cashflow = pd.read_excel(
        cashflow_file
    )


    allocation = latest[
        [
            "company_id",
            "pattern_label"
        ]
    ]


    allocation = allocation.rename(
        columns={
            "pattern_label":
            "capital_allocation_pattern"
        }
    )


    cashflow = cashflow.merge(
        allocation,
        on="company_id",
        how="left"
    )


    cashflow.to_excel(
        "output/cashflow_intelligence.xlsx",
        index=False
    )


    print("Capital Allocation Report Generated")
    print("Pattern changes:", len(changes))
    print("Companies:", cashflow["company_id"].nunique())


if __name__ == "__main__":
    generate_capital_report()