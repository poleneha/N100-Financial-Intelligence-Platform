import pandas as pd
import os


os.makedirs("output", exist_ok=True)


def generate_capital_report():

    input_file = "output/capital_allocation.csv"

    cashflow_file = "output/cashflow_intelligence.xlsx"


    df = pd.read_csv(input_file)


    print("Columns:")
    print(df.columns.tolist())


    # Latest year distribution

    if "year" in df.columns:

        latest_year = df["year"].max()

        latest = df[
            df["year"] == latest_year
        ]

    else:

        latest = df.copy()



    # Distribution summary

    if "pattern" in latest.columns:

        summary = (
            latest["pattern"]
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


    # Year over year pattern changes

    changes = []


    if (
        "company_id" in df.columns
        and "year" in df.columns
        and "pattern" in df.columns
    ):

        df = df.sort_values(
            ["company_id", "year"]
        )


        df["previous_pattern"] = (
            df.groupby("company_id")["pattern"]
            .shift(1)
        )


        changed = df[
            (df["previous_pattern"].notna()) &
            (df["previous_pattern"] != df["pattern"])
        ]


        for _, row in changed.iterrows():

            changes.append({

                "company_id": row["company_id"],

                "year": row["year"],

                "old_pattern": row["previous_pattern"],

                "new_pattern": row["pattern"]

            })


    pd.DataFrame(changes).to_csv(
        "output/pattern_changes.csv",
        index=False
    )


    # Add capital allocation column to cashflow file

    cashflow = pd.read_excel(
        cashflow_file
    )


    if "pattern" in latest.columns:

        allocation = latest[
            ["company_id", "pattern"]
        ].rename(
            columns={
                "pattern":
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
    print("Companies:", cashflow["company_id"].nunique())



if __name__ == "__main__":

    generate_capital_report()