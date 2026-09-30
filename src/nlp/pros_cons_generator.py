import pandas as pd
import os


os.makedirs("output", exist_ok=True)


def add_result(results, company, rule_id, signal_type, text, confidence):

    if confidence > 60:
        results.append({
            "company_id": company,
            "type": signal_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": confidence
        })


def generate_pros_cons():

    input_file = "data/raw/financial_ratios.xlsx"

    df = pd.read_excel(input_file, header=1)

    print("Financial file shape:", df.shape)

    # Find company column automatically
    possible_cols = [
        "company_id",
        "company",
        "Company",
        "ticker",
        "symbol",
        "name"
    ]

    company_col = None

    for col in df.columns:
        if col in possible_cols:
            company_col = col
            break

    if company_col is None:
        company_col = df.columns[1]

    df.rename(columns={company_col: "company_id"}, inplace=True)


    # Clean company names
    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace('"', '', regex=False)
        .str.replace("'", '', regex=False)
        .str.replace(" ", '', regex=False)
    )


    results = []


    for company, data in df.groupby("company_id"):

        latest = data.sort_values(data.columns[0]).iloc[-1]


        def get_value(col):
            if col in latest.index:
                try:
                    return float(latest[col])
                except:
                    return 0
            return 0


        roe = get_value("return_on_equity_pct")
        debt = get_value("debt_to_equity")
        icr = get_value("interest_coverage")
        opm = get_value("operating_profit_margin_pct")
        fcf = get_value("free_cash_flow_cr")
        npm = get_value("net_profit_margin_pct")


        # PRO RULES

        if roe > 20:
            add_result(results, company,
                       "PRO1", "pro",
                       "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                       90)


        if fcf > 0:
            add_result(results, company,
                       "PRO2", "pro",
                       "Strong free cash flow generation signals healthy business fundamentals",
                       80)


        if debt == 0:
            add_result(results, company,
                       "PRO3", "pro",
                       "Debt-free balance sheet provides financial flexibility",
                       90)


        if opm > 25:
            add_result(results, company,
                       "PRO5", "pro",
                       "Operating profit margin above 25% indicates strong pricing power",
                       85)


        if icr > 10:
            add_result(results, company,
                       "PRO7", "pro",
                       "Very high interest coverage ratio reflects low financial stress",
                       80)


        # CON RULES

        if debt > 2:
            add_result(results, company,
                       "CON1", "con",
                       "High debt-to-equity ratio requires monitoring",
                       85)


        if icr < 1.5:
            add_result(results, company,
                       "CON6", "con",
                       "Interest coverage below 1.5x indicates debt servicing risk",
                       85)


        if roe < 10:
            add_result(results, company,
                       "CON10", "con",
                       "Low return on equity indicates weak capital efficiency",
                       70)


        if npm < 0:
            add_result(results, company,
                       "CON4", "con",
                       "Company reported negative profitability",
                       80)



    # FORCE MINIMUM ONE PRO AND ONE CON

    companies = df["company_id"].unique()

    for company in companies:

        company_types = [
            x["type"]
            for x in results
            if x["company_id"] == company
        ]


        if "pro" not in company_types:

            results.append({
                "company_id": company,
                "type": "pro",
                "rule_id": "DEFAULT_PRO",
                "text": "Company shows positive financial characteristics",
                "confidence_pct": 65
            })


        if "con" not in company_types:

            results.append({
                "company_id": company,
                "type": "con",
                "rule_id": "DEFAULT_CON",
                "text": "Company requires financial monitoring",
                "confidence_pct": 65
            })


    output = pd.DataFrame(results)


    output.to_csv(
        "output/pros_cons_generated.csv",
        index=False
    )


    print("Generated successfully")
    print(output["type"].value_counts())
    print("Companies:", output["company_id"].nunique())


if __name__ == "__main__":
    generate_pros_cons()