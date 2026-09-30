import pandas as pd
import os


# Create output folder
os.makedirs(
    "output",
    exist_ok=True
)


# Sample valuation data
data = pd.DataFrame({

    "company_id": [1,2,3,4,5],

    "company_name": [
        "TCS",
        "Reliance",
        "Infosys",
        "ITC",
        "HDFC Bank"
    ],

    "sector": [
        "IT",
        "Energy",
        "IT",
        "FMCG",
        "Banking"
    ],

    "P/E": [
        60,
        10,
        24,
        30,
        20
    ],

    "P/B": [
        5,
        3,
        4,
        6,
        2
    ],

    "EV/EBITDA": [
        18,
        12,
        16,
        20,
        10
    ],

    "FCF_yield_pct": [
        3.5,
        5.2,
        4.1,
        2.8,
        6.0
    ]

})


# Sector median PE

data["5yr_median_PE"] = (
    data.groupby("sector")["P/E"]
    .transform("median")
)


# PE comparison

data["PE_vs_sector_median_pct"] = (
    (data["P/E"] - data["5yr_median_PE"])
    /
    data["5yr_median_PE"]
) * 100


# Valuation flag

def valuation_flag(row):

    if row["P/E"] > row["5yr_median_PE"] * 1.5:
        return "Caution"

    elif row["P/E"] < row["5yr_median_PE"] * 0.7:
        return "Discount"

    else:
        return "Fair"


data["flag"] = data.apply(
    valuation_flag,
    axis=1
)


# Save Excel

data.to_excel(
    "output/valuation_summary.xlsx",
    index=False
)


# Save flags CSV

data[
    data["flag"] != "Fair"
].to_csv(
    "output/valuation_flags.csv",
    index=False
)


print("Valuation files generated successfully")