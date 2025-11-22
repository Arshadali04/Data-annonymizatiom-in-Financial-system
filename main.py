import pandas as pd
import hashlib
from faker import Faker

K = 10

AGE_COL = 'Age'
BAL_COL = 'Balance_INR'
NAME_COL = 'Name'
PHONE_COL = 'Phone'
EMAIL_COL = 'Email'
UPI_COL = 'UPI_ID'
BANK_COL = 'Bank'
IFSC_COL = 'IFSC'
ACC_COL = 'Account_Number'
AADHAAR_COL = 'Aadhaar_Number'
CITY_COL = 'City'

faker = Faker('en_IN')
_name_map = {}
_email_map = {}

def generalize_city_to_region(val, n_regions=8):
    if pd.isna(val):
        return val
    s = str(val).strip().lower()
    if not s:
        return "Region_Unknown"
    try:
        h = hashlib.sha256(s.encode()).hexdigest()
        idx = int(h, 16) % n_regions
        return f"Region_{idx+1}"
    except Exception:
        return "Region_Unknown"

def pseudonymize_number(val):
    if pd.isna(val):
        return val
    try:
        s = ''.join(ch for ch in str(val) if ch.isdigit())
        if not s:
            return val
        h = hashlib.sha256(s.encode()).hexdigest()
        digits = ''.join(str(int(ch, 16) % 10) for ch in h)
        return digits[:len(s)]
    except Exception:
        return val

def pseudonymize_upi(val):
    if pd.isna(val):
        return val
    try:
        s = str(val).strip()
        if '@' not in s:
            h = hashlib.sha256(s.encode()).hexdigest()[:10]
            return 'upi_' + h
        user, handle = s.split('@', 1)
        h = hashlib.sha256(user.encode()).hexdigest()[:8]
        return 'user_' + h + '@' + handle
    except Exception:
        return val

def amount_to_range(val, step=10000):
    if pd.isna(val):
        return val
    try:
        v = float(str(val).replace(',', ''))
        if v < 0:
            v = 0
        lower = int(v // step * step)
        upper = lower + step
        return f"{lower}-{upper}"
    except Exception:
        return val

def mask_ifsc(val):
    if pd.isna(val):
        return val
    try:
        s = str(val).strip()
        if len(s) <= 4:
            return '*' * len(s)
        return s[:4] + '*' * (len(s) - 4)
    except Exception:
        return val

def fake_name(val):
    if pd.isna(val):
        return val
    try:
        s = str(val)
        if s in _name_map:
            return _name_map[s]
        n = faker.name()
        _name_map[s] = n
        return n
    except Exception:
        return val

def mask_phone(val):
    if pd.isna(val):
        return val
    try:
        s = ''.join(ch for ch in str(val) if ch.isdigit() or ch == '+')
        if len(s) <= 4:
            return '*' * len(s)
        return '*' * (len(s) - 4) + s[-4:]
    except Exception:
        return val

def tokenize_email(val):
    if pd.isna(val):
        return val
    try:
        s = str(val).strip()
        if s in _email_map:
            return _email_map[s]
        token = f"email_{len(_email_map)+1:06d}"
        _email_map[s] = token
        return token
    except Exception:
        return val

def anonymize_bankdetails(df, k=K):
    try:
        if k is None or k <= 0:
            print("ERROR: k must be a positive integer.")
            return None

        df_an = df.copy()
        df_an.columns = [c.strip() for c in df_an.columns]

        if AGE_COL not in df_an.columns or BAL_COL not in df_an.columns:
            print("FATAL ERROR: Required columns missing.")
            print(df_an.columns)
            return None

        df_an[AGE_COL] = pd.to_numeric(df_an[AGE_COL], errors='coerce')
        df_an = df_an.dropna(subset=[AGE_COL])
        if df_an.empty:
            print("ERROR: No valid Age values after cleaning.")
            return None
        df_an[AGE_COL] = df_an[AGE_COL].astype(int)

        age_counts = df_an[AGE_COL].value_counts().sort_index().reset_index()
        age_counts.columns = [AGE_COL, 'count']

        partitions = []
        current_partition_ages = []
        current_partition_count = 0

        for _, row in age_counts.iterrows():
            current_partition_ages.append(row[AGE_COL])
            current_partition_count += row['count']
            if current_partition_count >= k and len(current_partition_ages) > 1:
                partitions.append(current_partition_ages)
                current_partition_ages = []
                current_partition_count = 0

        if current_partition_ages:
            if partitions:
                partitions[-1].extend(current_partition_ages)
            else:
                partitions.append(current_partition_ages)
        
        if not partitions:
            print("ERROR: Could not form any partitions for k-anonymity.")
            return None

        age_to_range_map = {}
        for part in partitions:
            mn = min(part)
            mx = max(part)
            lower = (mn // 5) * 5
            upper = ((mx + 4) // 5) * 5
            age_range_str = f"{lower}-{upper}"
            for a in part:
                age_to_range_map[a] = age_range_str

        df_an[AGE_COL] = df_an[AGE_COL].map(age_to_range_map)

        df_an['Balance_Range'] = df_an[BAL_COL].apply(lambda v: amount_to_range(v, step=10000))

        if CITY_COL in df_an.columns:
            df_an[CITY_COL] = df_an[CITY_COL].apply(lambda v: generalize_city_to_region(v, n_regions=8))

        if ACC_COL in df_an.columns:
            df_an[ACC_COL] = df_an[ACC_COL].apply(pseudonymize_number)

        if AADHAAR_COL in df_an.columns:
            df_an[AADHAAR_COL] = df_an[AADHAAR_COL].apply(pseudonymize_number)

        if UPI_COL in df_an.columns:
            df_an[UPI_COL] = df_an[UPI_COL].apply(pseudonymize_upi)

        if IFSC_COL in df_an.columns:
            df_an[IFSC_COL] = df_an[IFSC_COL].apply(mask_ifsc)

        if NAME_COL in df_an.columns:
            df_an[NAME_COL] = df_an[NAME_COL].apply(fake_name)

        if PHONE_COL in df_an.columns:
            df_an[PHONE_COL] = df_an[PHONE_COL].apply(mask_phone)

        if EMAIL_COL in df_an.columns:
            df_an[EMAIL_COL] = df_an[EMAIL_COL].apply(tokenize_email)

        out_cols = [
            NAME_COL,
            AGE_COL,
            CITY_COL,
            BANK_COL,
            'Balance_Range',
            ACC_COL,
            AADHAAR_COL,
            UPI_COL,
            IFSC_COL,
            'Gender',
            PHONE_COL,
            EMAIL_COL
        ]
        out_cols = [c for c in out_cols if c in df_an.columns]

        if not out_cols:
            print("ERROR: No output columns available after anonymization.")
            return None

        return df_an[out_cols]
    except Exception as e:
        print(f"Error during anonymization: {e}")
        return None

if __name__ == "__main__":
    try:
        data = pd.read_csv("bankdetails.csv")
    except FileNotFoundError:
        print("Error: 'bankdetails.csv' not found in the current directory.")
    except pd.errors.EmptyDataError:
        print("Error: 'bankdetails.csv' is empty or invalid.")
    except pd.errors.ParserError as e:
        print(f"Error parsing 'bankdetails.csv': {e}")
    except Exception as e:
        print(f"Unexpected error while reading CSV: {e}")
    else:
        anonymized = anonymize_bankdetails(data, K)
        if anonymized is not None:
            try:
                output_filename = "anonymized_bankdetails.csv"
                anonymized.to_csv(output_filename, index=False)
                print(anonymized.head())
            except PermissionError:
                print("Error: Permission denied while writing 'anonymized_bankdetails.csv'. Close the file if it is open.")
            except Exception as e:
                print(f"Unexpected error while writing output CSV: {e}")
