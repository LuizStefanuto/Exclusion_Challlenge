from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
INPUT_PATH = ROOT_DIR / "combined_deposits.csv"
CLEANED_OUTPUT_PATH = ROOT_DIR / "combined_deposits_cleaned.csv"
FRAUD_ZERO_WITH_DATE_OUTPUT = ROOT_DIR / "fraud_0_with_detection_date.csv"
DECLINED_FRAUD_OUTPUT = ROOT_DIR / "approved_0_fraud_1.csv"
FRAUD_ONE_WITHOUT_DATE_OUTPUT = ROOT_DIR / "fraud_1_without_detection_date.csv"
FRAUD_DATE_BEFORE_TRANSACTION_OUTPUT = ROOT_DIR / "fraud_detection_before_transaction.csv"


def main():
    df = pd.read_csv(INPUT_PATH)

    null_segment_rows = df[df["Segment"].isna()].copy()
    fraud_zero_with_date = df[
        (df["Fraud"].fillna(0) == 0) & (df["FraudDetectionDate"].notna())
    ].copy()

    removal_mask = df["Segment"].isna() | (
        (df["Fraud"].fillna(0) == 0) & (df["FraudDetectionDate"].notna())
    )
    cleaned_df = df.loc[~removal_mask].copy()

    transaction_date = pd.to_datetime(cleaned_df["TransactionDate"], errors="coerce")
    fraud_detection_date = pd.to_datetime(cleaned_df["FraudDetectionDate"], errors="coerce")

    declined_with_fraud = cleaned_df[
        (cleaned_df["Approved"].fillna(0) == 0) & (cleaned_df["Fraud"].fillna(0) == 1)
    ].copy()
    fraud_one_without_date = cleaned_df[
        (cleaned_df["Fraud"].fillna(0) == 1) & (cleaned_df["FraudDetectionDate"].isna())
    ].copy()
    fraud_date_before_transaction = cleaned_df[
        fraud_detection_date.notna()
        & transaction_date.notna()
        & (fraud_detection_date < transaction_date)
    ].copy()

    cleaned_df.to_csv(CLEANED_OUTPUT_PATH, index=False)
    fraud_zero_with_date.to_csv(FRAUD_ZERO_WITH_DATE_OUTPUT, index=False)
    declined_with_fraud.to_csv(DECLINED_FRAUD_OUTPUT, index=False)
    fraud_one_without_date.to_csv(FRAUD_ONE_WITHOUT_DATE_OUTPUT, index=False)
    fraud_date_before_transaction.to_csv(FRAUD_DATE_BEFORE_TRANSACTION_OUTPUT, index=False)

    print(f"Input file: {INPUT_PATH}")
    print(f"Output cleaned file: {CLEANED_OUTPUT_PATH}")
    print(f"Original rows: {len(df):,}")
    print(f"Rows removed for null Segment: {len(null_segment_rows):,}")
    print(
        "Rows removed for Fraud = 0 and FraudDetectionDate populated: "
        f"{len(fraud_zero_with_date):,}"
    )
    print(f"Cleaned rows: {len(cleaned_df):,}")
    print(
        "Rows with Fraud = 0 and FraudDetectionDate populated saved to: "
        f"{FRAUD_ZERO_WITH_DATE_OUTPUT}"
    )
    print(f"Rows with Approved = 0 and Fraud = 1: {len(declined_with_fraud):,}")
    print(f"Output file: {DECLINED_FRAUD_OUTPUT}")
    print(
        "Rows with Fraud = 1 and FraudDetectionDate missing: "
        f"{len(fraud_one_without_date):,}"
    )
    print(f"Output file: {FRAUD_ONE_WITHOUT_DATE_OUTPUT}")
    print(
        "Rows with FraudDetectionDate earlier than TransactionDate: "
        f"{len(fraud_date_before_transaction):,}"
    )
    print(f"Output file: {FRAUD_DATE_BEFORE_TRANSACTION_OUTPUT}")


if __name__ == "__main__":
    main()
