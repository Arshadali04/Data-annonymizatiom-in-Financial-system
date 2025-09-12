import pandas as pd
data=pd.read_csv("bank_details.csv")
def generalize_age(age):
    if age < 20:
        return  "15-19";
    elif age < 25 and age >= 20:  
        return "20-24";
    elif age < 30 and age >= 25:
        return "25-29";
    elif age < 35  and age >= 30:
        return "30-34";
    elif age < 40 and age >= 35:
        return "35-39";
    elif age < 45 and age >= 40:
        return "40-44";
    elif age < 50 and age >= 45:
        return "45-49";
    elif age < 55 and age >= 50:
        return "50-54";
    elif age >= 55:
        return "55+"; 


if __name__ == "__main__":
    data["age"] = data["age"].apply(generalize_age)
    data.to_csv("anonymized_bank_transactions.csv", index=False)
    print("Anonymization complete. Output saved to anonymized_bank_transactions.csv")
