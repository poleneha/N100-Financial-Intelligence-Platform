import pandas as pd
import re
import os


os.makedirs("output", exist_ok=True)


# Example analysis data
data = pd.DataFrame({

    "company_id":[1,2,3],

    "compounded_sales_growth":[
        "10 Years: 21%",
        "5 Years: 15%",
        "8 Years: 12%"
    ]

})


records = []
failures = []


pattern = r"(\d+)\s*Years?:?\s*([\d.]+)%"


for _, row in data.iterrows():

    text = row["compounded_sales_growth"]

    match = re.search(pattern, text)

    if match:

        records.append({

            "company_id": row["company_id"],

            "metric_type":
            "compounded_sales_growth",

            "period_years":
            int(match.group(1)),

            "value_pct":
            float(match.group(2))

        })

    else:

        failures.append({

            "company_id":
            row["company_id"],

            "text":
            text

        })


pd.DataFrame(records).to_csv(
    "output/analysis_parsed.csv",
    index=False
)


pd.DataFrame(failures).to_csv(
    "output/parse_failures.csv",
    index=False
)


print("NLP Parsing completed")