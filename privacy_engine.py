from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import hashlib
from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd
from faker import Faker


DEFAULT_K = 10
DEFAULT_L = 2
DEFAULT_BALANCE_STEP = 10000

AGE_COL = "Age"
BAL_COL = "Balance_INR"
NAME_COL = "Name"
PHONE_COL = "Phone"
EMAIL_COL = "Email"
UPI_COL = "UPI_ID"
BANK_COL = "Bank"
IFSC_COL = "IFSC"
ACC_COL = "Account_Number"
AADHAAR_COL = "Aadhaar_Number"
CITY_COL = "City"
GENDER_COL = "Gender"
STATE_COL = "State"
BAL_RANGE_COL = "Balance_Range"

faker = Faker("en_IN")
_name_map: Dict[str, str] = {}
_email_map: Dict[str, str] = {}


CITY_STATE_MAP: Dict[str, str] = {
    "ahmedabad": "Gujarat",
    "bengaluru": "Karnataka",
    "bangalore": "Karnataka",
    "chennai": "Tamil Nadu",
    "delhi": "Delhi",
    "hyderabad": "Telangana",
    "kolkata": "West Bengal",
    "mumbai": "Maharashtra",
    "pune": "Maharashtra",
    "jaipur": "Rajasthan",
    "lucknow": "Uttar Pradesh",
    "patna": "Bihar",
    "bhopal": "Madhya Pradesh",
    "chandigarh": "Chandigarh",
    "kochi": "Kerala",
    "surat": "Gujarat",
    "nagpur": "Maharashtra",
    "indore": "Madhya Pradesh",
    "noida": "Uttar Pradesh",
    "gurgaon": "Haryana",
    "gurugram": "Haryana",
}


@dataclass
class PrivacyConfig:
    k: int = DEFAULT_K
    l: int = DEFAULT_L
    balance_step: int = DEFAULT_BALANCE_STEP
    privacy_level: str = "medium"

    @classmethod
    def from_level(cls, level: str) -> "PrivacyConfig":
        normalized = (level or "medium").strip().lower()
        if normalized == "low":
            return cls(k=5, l=2, balance_step=5000, privacy_level="low")
        if normalized == "high":
            return cls(k=15, l=3, balance_step=20000, privacy_level="high")
        return cls(k=10, l=2, balance_step=10000, privacy_level="medium")


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [c.strip() for c in normalized.columns]
    for col in normalized.columns:
        if normalized[col].dtype == object:
            normalized[col] = normalized[col].astype(str).str.strip()
            normalized[col] = normalized[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    return normalized


def _amount_to_range(val: object, step: int = DEFAULT_BALANCE_STEP) -> object:
    if pd.isna(val):
        return pd.NA
    try:
        amount = float(str(val).replace(",", ""))
        amount = max(amount, 0)
        lower = int(amount // step * step)
        upper = lower + step
        return f"{lower}-{upper}"
    except (TypeError, ValueError):
        return pd.NA


def _mask_ifsc(val: object) -> object:
    if pd.isna(val):
        return pd.NA
    raw = str(val).strip()
    if len(raw) <= 4:
        return "*" * len(raw)
    return raw[:4] + "*" * (len(raw) - 4)

def _is_valid_aadhaar(val: object) -> bool:
    """
    Validates whether an Aadhaar number contains exactly 12 digits.
    """
    if pd.isna(val):
        return False

    digits = "".join(ch for ch in str(val) if ch.isdigit())
    return len(digits) == 12

def _hash_digits(val: object) -> object:
    if pd.isna(val):
        return pd.NA
    digits = "".join(ch for ch in str(val) if ch.isdigit())
    if not digits:
        return pd.NA
    digest = hashlib.sha256(digits.encode("utf-8")).hexdigest()
    mapped = "".join(str(int(ch, 16) % 10) for ch in digest)
    return mapped[: len(digits)]


def _pseudonymize_upi(val: object) -> object:
    if pd.isna(val):
        return pd.NA
    raw = str(val).strip()
    if "@" not in raw:
        return "upi_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    user, handle = raw.split("@", 1)
    token = hashlib.sha256(user.encode("utf-8")).hexdigest()[:8]
    return f"user_{token}@{handle}"


def _fake_name(val: object) -> object:
    if pd.isna(val):
        return pd.NA
    raw = str(val)
    if raw in _name_map:
        return _name_map[raw]
    fake = faker.name()
    _name_map[raw] = fake
    return fake


def _mask_phone(val: object) -> object:
    """ 
    Masks a phone number while preserving the last 4 digits.

    Purpose:
        Protects personally identifiable information (PII)
        while retaining partial information for verification.

    Example:
        9876543210 -> ******3210

    Returns:
        Masked phone number as a string.
    """
        
    if pd.isna(val):
        return pd.NA
    digits = "".join(ch for ch in str(val) if ch.isdigit())
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]


def _tokenize_email(val: object) -> object:
    """
    Replaces an email address with a unique token.

    Purpose:
        Prevents exposure of real email addresses while
        maintaining consistency across records.

    Example:
        arshad@gmail.com -> email_000001

    Returns:
        Tokenized email identifier.
    """
    if pd.isna(val):
        return pd.NA
    raw = str(val).strip().lower()
    if raw in _email_map:
        return _email_map[raw]
    token = f"email_{len(_email_map) + 1:06d}"
    _email_map[raw] = token
    return token


def map_city_to_state(city: object) -> object:
    """
    Generalizes city information into state-level locations.

    Purpose:
        Reduces location granularity to improve privacy.

    Example:
        Bengaluru -> Karnataka
        Mumbai -> Maharashtra

    Returns:
        Corresponding state name.
    """
    if pd.isna(city):
        return pd.NA
    normalized = str(city).strip().lower()
    if not normalized:
        return pd.NA
    return CITY_STATE_MAP.get(normalized, "Other")


def _build_age_ranges(age_series: pd.Series, k: int) -> Dict[int, str]:
    counts = age_series.value_counts().sort_index().reset_index()
    counts.columns = [AGE_COL, "count"]

    partitions: List[List[int]] = []
    current_ages: List[int] = []
    current_count = 0

    for _, row in counts.iterrows():
        age_value = int(row[AGE_COL])
        current_ages.append(age_value)
        current_count += int(row["count"])
        if current_count >= k and len(current_ages) > 1:
            partitions.append(current_ages)
            current_ages = []
            current_count = 0

    if current_ages:
        if partitions:
            partitions[-1].extend(current_ages)
        else:
            partitions.append(current_ages)

    if not partitions:
        return {}

    age_map: Dict[int, str] = {}
    for partition in partitions:
        minimum = min(partition)
        maximum = max(partition)
        lower = (minimum // 5) * 5
        upper = ((maximum + 4) // 5) * 5
        label = f"{lower}-{upper}"
        for age_value in partition:
            age_map[age_value] = label

    return age_map


def _parse_balance_midpoint(balance_range: object) -> float:
    if pd.isna(balance_range):
        return 0.0
    raw = str(balance_range)
    if "-" not in raw:
        return 0.0
    left, right = raw.split("-", 1)
    try:
        return (float(left) + float(right)) / 2.0
    except ValueError:
        return 0.0


def _parse_age_midpoint(age_range: object) -> float:
    if pd.isna(age_range):
        return 0.0
    raw = str(age_range)
    if "-" not in raw:
        return 0.0
    left, right = raw.split("-", 1)
    try:
        return (float(left) + float(right)) / 2.0
    except ValueError:
        return 0.0


def _distribution_preservation(original: pd.Series, anonymized: pd.Series) -> float:
    original_norm = original.value_counts(normalize=True)
    anonymized_norm = anonymized.value_counts(normalize=True)
    all_keys = sorted(set(original_norm.index).union(set(anonymized_norm.index)))
    tvd = 0.0
    for key in all_keys:
        tvd += abs(float(original_norm.get(key, 0.0)) - float(anonymized_norm.get(key, 0.0)))
    return max(0.0, (1.0 - (0.5 * tvd)) * 100.0)


def _numeric_preservation(original_value: float, anonymized_value: float) -> float:
    denominator = abs(original_value) if original_value != 0 else 1.0
    error = abs(anonymized_value - original_value) / denominator
    return max(0.0, (1.0 - error) * 100.0)


def _calculate_l_diversity_report(anonymized_df: pd.DataFrame, original_df: pd.DataFrame, l_value: int) -> pd.DataFrame:
    qi_columns = [col for col in [AGE_COL, STATE_COL, GENDER_COL] if col in anonymized_df.columns]
    if not qi_columns or BAL_COL not in original_df.columns:
        return pd.DataFrame(
            columns=qi_columns
            + ["record_count", "distinct_account_balance", "l_value", "l_diversity_compliant"]
        )

    analysis_df = anonymized_df[qi_columns].copy()
    analysis_df["Account_Balance"] = pd.to_numeric(original_df[BAL_COL], errors="coerce")

    report = (
        analysis_df.groupby(qi_columns, dropna=False)
        .agg(
            record_count=("Account_Balance", "size"),
            distinct_account_balance=("Account_Balance", pd.Series.nunique),
        )
        .reset_index()
    )
    report["l_value"] = int(l_value)
    report["l_diversity_compliant"] = report["distinct_account_balance"] >= int(l_value)
    return report


def _calculate_privacy_metrics(original_df: pd.DataFrame, anonymized_df: pd.DataFrame, l_report: pd.DataFrame, k: int) -> pd.DataFrame:
    shared_cols = [col for col in anonymized_df.columns if col in original_df.columns]
    row_modified = 0
    if shared_cols:
        original_subset = original_df[shared_cols].fillna("<NA>").astype(str)
        anonymized_subset = anonymized_df[shared_cols].fillna("<NA>").astype(str)
        row_modified = int((original_subset != anonymized_subset).any(axis=1).sum())

    sensitive_fields = [
        col
        for col in [NAME_COL, PHONE_COL, EMAIL_COL, UPI_COL, IFSC_COL, ACC_COL, AADHAAR_COL, CITY_COL, BAL_RANGE_COL]
        if col in anonymized_df.columns
    ]

    original_qi_cols = [col for col in [AGE_COL, CITY_COL, GENDER_COL] if col in original_df.columns]
    anonymized_qi_cols = [col for col in [AGE_COL, STATE_COL, GENDER_COL] if col in anonymized_df.columns]

    unique_before = (
        int(original_df[original_qi_cols].drop_duplicates().shape[0]) if original_qi_cols else int(original_df.shape[0])
    )
    unique_after = (
        int(anonymized_df[anonymized_qi_cols].drop_duplicates().shape[0]) if anonymized_qi_cols else int(anonymized_df.shape[0])
    )

    risk_reduction = 0.0
    if unique_before > 0:
        risk_reduction = max(0.0, (1.0 - (unique_after / unique_before)) * 100.0)

    k_compliance = False
    if AGE_COL in anonymized_df.columns:
        k_group_counts = anonymized_df.groupby(AGE_COL, dropna=False).size()
        k_compliance = bool((k_group_counts >= int(k)).all()) if not k_group_counts.empty else False

    l_compliance = False
    compliant_ratio = 0.0
    if not l_report.empty:
        l_compliance = bool(l_report["l_diversity_compliant"].all())
        compliant_ratio = float(l_report["l_diversity_compliant"].mean() * 100.0)

    metrics = {
        "total_records": int(original_df.shape[0]),
        "records_modified": row_modified,
        "sensitive_fields_protected": int(len(sensitive_fields)),
        "reidentification_risk_reduction_pct": round(risk_reduction, 2),
        "k_anonymity_required": int(k),
        "k_anonymity_compliant": k_compliance,
        "l_diversity_required": int(l_report["l_value"].iloc[0]) if not l_report.empty else DEFAULT_L,
        "l_diversity_compliant": l_compliance,
        "l_diversity_class_compliance_pct": round(compliant_ratio, 2),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_compliance": ("PASS" if k_compliance and l_compliance else "FAIL"),
        "validation_summary":"K-Anonymity and L-Diversity Passed" if k_compliance and l_compliance else "Validation Failed",     
        "privacy_score": round(((100 if k_compliance else 0)+ (100 if l_compliance else 0)+ risk_reduction) / 3,2,),
    }
    return pd.DataFrame([metrics])


def _calculate_utility_report(original_df: pd.DataFrame, anonymized_df: pd.DataFrame) -> pd.DataFrame:
    report_rows: List[Dict[str, object]] = []

    if BAL_COL in original_df.columns and BAL_RANGE_COL in anonymized_df.columns:
        original_balance = pd.to_numeric(original_df[BAL_COL], errors="coerce")
        anonymized_balance = anonymized_df[BAL_RANGE_COL].apply(_parse_balance_midpoint)

        mean_original = float(original_balance.mean())
        mean_anon = float(anonymized_balance.mean())
        median_original = float(original_balance.median())
        median_anon = float(anonymized_balance.median())

        report_rows.append(
            {
                "metric": "mean_balance",
                "original": round(mean_original, 2),
                "anonymized": round(mean_anon, 2),
                "utility_preservation_pct": round(_numeric_preservation(mean_original, mean_anon), 2),
            }
        )
        report_rows.append(
            {
                "metric": "median_balance",
                "original": round(median_original, 2),
                "anonymized": round(median_anon, 2),
                "utility_preservation_pct": round(_numeric_preservation(median_original, median_anon), 2),
            }
        )

    if AGE_COL in original_df.columns and AGE_COL in anonymized_df.columns:
        original_age_bins = pd.to_numeric(original_df[AGE_COL], errors="coerce").dropna().astype(int) // 10
        anonymized_age_bins = anonymized_df[AGE_COL].apply(_parse_age_midpoint).astype(float) // 10
        preservation = _distribution_preservation(original_age_bins, anonymized_age_bins)
        report_rows.append(
            {
                "metric": "age_distribution",
                "original": "Original age bins",
                "anonymized": "Generalized age bins",
                "utility_preservation_pct": round(preservation, 2),
            }
        )

    if GENDER_COL in original_df.columns and GENDER_COL in anonymized_df.columns:
        preservation = _distribution_preservation(
            original_df[GENDER_COL].fillna("Unknown"), anonymized_df[GENDER_COL].fillna("Unknown")
        )
        report_rows.append(
            {
                "metric": "gender_distribution",
                "original": "Original gender distribution",
                "anonymized": "Anonymized gender distribution",
                "utility_preservation_pct": round(preservation, 2),
            }
        )
    if report_rows:
        avg_utility = sum(
        row["utility_preservation_pct"]
        for row in report_rows
        if isinstance(row.get("utility_preservation_pct"), (int, float))
    ) / len(report_rows)

        report_rows.append(
        {
            "metric": "overall_utility_score",
            "original": "-",
            "anonymized": "-",
            "utility_preservation_pct": round(avg_utility, 2),
        }
    )
    return pd.DataFrame(report_rows)


def anonymize_dataframe(df: pd.DataFrame, config: PrivacyConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if config.k <= 0:
        raise ValueError("k must be a positive integer")
    if config.l <= 0:
        raise ValueError("l must be a positive integer")

    original = _normalize_dataframe(df)
    if original.empty:
        raise ValueError("Input dataset is empty")

    required = [AGE_COL, BAL_COL]
    missing = [col for col in required if col not in original.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    working = original.copy()
    working[AGE_COL] = pd.to_numeric(working[AGE_COL], errors="coerce")
    working = working.dropna(subset=[AGE_COL]).reset_index(drop=True)
    original = original.loc[working.index].reset_index(drop=True)
    working[AGE_COL] = working[AGE_COL].astype(int)

    age_map = _build_age_ranges(working[AGE_COL], config.k)
    if not age_map:
        raise ValueError("Could not create age ranges for k-anonymity")
    working[AGE_COL] = working[AGE_COL].map(age_map)

    working[BAL_RANGE_COL] = working[BAL_COL].apply(lambda value: _amount_to_range(value, step=config.balance_step))

    if CITY_COL in working.columns:
        mapped_state = working[CITY_COL].apply(map_city_to_state)
        working[CITY_COL] = mapped_state
        working[STATE_COL] = mapped_state

    if ACC_COL in working.columns:
        working[ACC_COL] = working[ACC_COL].apply(_hash_digits)

    if AADHAAR_COL in working.columns:
        working[AADHAAR_COL] = working[AADHAAR_COL].apply(
            lambda x: _hash_digits(x) if _is_valid_aadhaar(x) else "INVALID_AADHAAR"
        )
        
    if UPI_COL in working.columns:
        working[UPI_COL] = working[UPI_COL].apply(_pseudonymize_upi)

    if IFSC_COL in working.columns:
        working[IFSC_COL] = working[IFSC_COL].apply(_mask_ifsc)

    if NAME_COL in working.columns:
        working[NAME_COL] = working[NAME_COL].apply(_fake_name)

    if PHONE_COL in working.columns:
        working[PHONE_COL] = working[PHONE_COL].apply(_mask_phone)

    if EMAIL_COL in working.columns:
        working[EMAIL_COL] = working[EMAIL_COL].apply(_tokenize_email)

    ordered_cols = [
        "Customer_ID",
        NAME_COL,
        AGE_COL,
        CITY_COL,
        STATE_COL,
        BANK_COL,
        BAL_RANGE_COL,
        ACC_COL,
        AADHAAR_COL,
        UPI_COL,
        IFSC_COL,
        GENDER_COL,
        PHONE_COL,
        EMAIL_COL,
    ]
    final_cols = [col for col in ordered_cols if col in working.columns]
    anonymized = working[final_cols].copy()

    l_report = _calculate_l_diversity_report(anonymized, original, config.l)
    metrics = _calculate_privacy_metrics(original, anonymized, l_report, config.k)
    utility = _calculate_utility_report(original, anonymized)

    return anonymized, l_report, metrics, utility


def run_pipeline(
    input_csv: str | Path,
    output_dir: str | Path = "outputs",
    level: str = "medium",
) -> Dict[str, Path]:
    input_path = Path(input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data = pd.read_csv(input_path)
    config = PrivacyConfig.from_level(level)

    anonymized, l_report, metrics, utility = anonymize_dataframe(data, config)

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    anonymized_path = target_dir / "anonymized_bankdetails.csv"
    l_report_path = target_dir / "l_diversity_report.csv"
    metrics_path = target_dir / "privacy_metrics.csv"
    utility_path = target_dir / "data_utility_report.csv"

    anonymized.to_csv(anonymized_path, index=False)
    l_report.to_csv(l_report_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    utility.to_csv(utility_path, index=False)

    return {
        "anonymized_csv": anonymized_path,
        "l_diversity_report": l_report_path,
        "privacy_metrics": metrics_path,
        "data_utility_report": utility_path,
    }


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
