import pandas as pd

data=pd.read_csv("bank_transactions.csv")
def generalize_age(age):
    if age < 35:
        return "35-";
    elif age < 40:
        return "35-39";
    elif age < 45:
        return "40-44";
    elif age < 50:
        return "45-49";
    elif age < 55:
        return "50-54";
    else:
        return "55+";


if __name__ == "__main__":
    data["CustomerDOB"] = pd.to_datetime(data["CustomerDOB"], format="%Y-%m-%d", errors='coerce')
    today = pd.to_datetime('2025-09-11')
    data["age"] = ((today - data["CustomerDOB"]).dt.days / 365.25).astype('Int64', errors='ignore')
    data["age"] = data["age"].apply(generalize_age)
    data = data.drop(columns=["CustomerDOB"])
    data.to_csv("anonymized_bank_transactions.csv", index=False)
    print("Anonymization complete. Output saved to anonymized_bank_transactions.csv")
