import pandas as pd

def check_missing_values(df):
    return df.isnull().sum()

def check_duplicates(df):
    return df.duplicated().sum()

def validate(df, table_name):
    print(f"\nValidating {table_name}")
    print("Missing Values:")
    print(check_missing_values(df))
    print("Duplicate Rows:", check_duplicates(df))

if __name__ == "__main__":
    sample = pd.DataFrame({
        "A": [1, 2, None, 2],
        "B": [10, 20, 30, 20]
    })

    validate(sample, "Sample Table")