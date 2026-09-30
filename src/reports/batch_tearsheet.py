import os
import sys
import pandas as pd


sys.path.append(
    "src/reports"
)


from tearsheet import generate_tearsheet



os.makedirs(
    "reports/tearsheets",
    exist_ok=True
)



companies = pd.read_excel(
    "data/raw/companies.xlsx",
    header=1
)



company_ids = (
    companies["id"]
    .astype(str)
    .tolist()
)



print(
    "Companies found:",
    len(company_ids)
)



count = 0
failed = []



for company in company_ids:

    try:

        generate_tearsheet(company)

        count += 1


    except Exception as e:

        print(
            "Failed:",
            company,
            e
        )

        failed.append(company)



print()
print(
    "Batch completed"
)

print(
    "Generated:",
    count
)


print(
    "Failed companies:"
)

print(
    failed
)