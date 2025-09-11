import pandas as pd

data=pd.read_csv("bank_transactions.csv")
def generalize_age(age):
    if age < 15:
        return "10-15";
    elif age < 20:
        return "15-20";
    elif age < 25:
        return "20-25";
    elif age < 30:
        return "25-30";
    elif age < 35:
        return "30-35";
    else:
        return "35+";


if __name__ == "__main__":
    data["CustomerDOB"] = pd.to_datetime(data["CustomerDOB"], format="%Y-%m-%d", errors='coerce')
    today = pd.to_datetime('2025-09-11')
    data["age"] = ((today - data["CustomerDOB"]).dt.days / 365.25).astype('Int64', errors='ignore')
    data["age"] = data["age"].apply(generalize_age)
    data = data.drop(columns=["CustomerDOB"])
    data.to_csv("anonymized_bank_transactions.csv", index=False)
    print("Anonymization complete. Output saved to anonymized_bank_transactions.csv")