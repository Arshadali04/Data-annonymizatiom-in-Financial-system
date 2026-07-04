from __future__ import annotations

import pandas as pd
import streamlit as st

from privacy_engine import PrivacyConfig, anonymize_dataframe, dataframe_to_csv_bytes


st.set_page_config(page_title="Financial Data Anonymizer", page_icon="🔐", layout="wide")

st.title("Data Anonymization in Financial Systems")
st.caption("Placement-ready privacy pipeline with k-anonymity, l-diversity, and utility analytics")

uploaded_file = st.file_uploader("Upload input CSV", type=["csv"])
privacy_level = st.selectbox("Select privacy level", options=["Low", "Medium", "High"], index=1)

if privacy_level == "Low":
    st.info("Low Privacy: K=5, L=2, Balance Range=5000")
elif privacy_level == "Medium":
    st.info("Medium Privacy: K=10, L=2, Balance Range=10000")
else:
    st.info("High Privacy: K=15, L=3, Balance Range=20000")

if uploaded_file is not None:
    try:
        original_df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Unable to read file: {exc}")
        st.stop()

    st.subheader("Original Data Preview")
    st.write(f"Total Records Uploaded: {len(original_df)}")
    st.write(f"Total Columns: {len(original_df.columns)}")
    st.dataframe(original_df.head(20), use_container_width=True)

    if st.button("Run Anonymization", type="primary"):
        config = PrivacyConfig.from_level(privacy_level.lower())

        try:
            anonymized_df, l_report_df, metrics_df, utility_df = anonymize_dataframe(original_df, config)
        except Exception as exc:
            st.error(f"Anonymization failed: {exc}")
            st.stop()

        st.success("Anonymization completed")

        st.info(
        """
            Generated Files:
            - anonymized_bankdetails.csv
            - privacy_metrics.csv
            - data_utility_report.csv
            - l_diversity_report.csv
        """
        )

        st.subheader("Anonymized Data Preview")
        st.dataframe(anonymized_df.head(20), use_container_width=True)

        st.subheader("Privacy Metrics Dashboard")
        st.write("### Active Privacy Configuration")

        st.write(
            {
                "Privacy Level": config.privacy_level,
                "K-Anonymity": config.k,
                "L-Diversity": config.l,
                "Balance Range Step": config.balance_step,
            }
        )
        metrics = metrics_df.iloc[0].to_dict()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Records", int(metrics.get("total_records", 0)))
        col2.metric("Records Modified", int(metrics.get("records_modified", 0)))
        col3.metric("Sensitive Fields Protected", int(metrics.get("sensitive_fields_protected", 0)))

        col4, col5, col6 = st.columns(3)
        col4.metric(
            "Re-identification Risk Reduction",
            f"{float(metrics.get('reidentification_risk_reduction_pct', 0.0)):.2f}%",
        )
        col5.metric("K-Anonymity Compliant", str(bool(metrics.get("k_anonymity_compliant", False))))
        col6.metric("L-Diversity Compliant", str(bool(metrics.get("l_diversity_compliant", False))))

        st.subheader("L-Diversity Validation Report")
        st.dataframe(l_report_df, use_container_width=True)

        st.subheader("Data Utility Analysis")
        st.dataframe(utility_df, use_container_width=True)

        st.download_button(
            label="Download Anonymized CSV",
            data=dataframe_to_csv_bytes(anonymized_df),
            file_name="anonymized_bankdetails.csv",
            mime="text/csv",
        )

        st.download_button(
            label="Download Privacy Metrics CSV",
            data=dataframe_to_csv_bytes(metrics_df),
            file_name="privacy_metrics.csv",
            mime="text/csv",
        )

        st.download_button(
            label="Download Utility Report CSV",
            data=dataframe_to_csv_bytes(utility_df),
            file_name="data_utility_report.csv",
            mime="text/csv",
        )

        st.download_button(
            label="Download L-Diversity Report CSV",
            data=dataframe_to_csv_bytes(l_report_df),
            file_name="l_diversity_report.csv",
            mime="text/csv",
        )
else:
    st.info("Upload a CSV file to start anonymization.")
