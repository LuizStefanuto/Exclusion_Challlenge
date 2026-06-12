from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"

MATURITY_DAYS = 45
BIN_OUTPUT_CSV = ROOT_DIR / "bin_segment_mature_45d_rates.csv"
CHANNEL_OUTPUT_CSV = ROOT_DIR / "channel_segment_mature_45d_rates.csv"
SEGMENT_OUTPUT_CSV = ROOT_DIR / "segment_mature_45d_baselines.csv"


def load_mature_dataset():
    df = pd.read_csv(
        DATASET_PATH,
        usecols=["UserCardBIN", "Channel", "Segment", "Approved", "Fraud", "TransactionDate"],
        dtype={"UserCardBIN": str, "Channel": str},
    )
    df = df.dropna(subset=["UserCardBIN", "Channel", "Segment", "Approved", "Fraud", "TransactionDate"]).copy()
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce")
    df["Approved"] = pd.to_numeric(df["Approved"], errors="coerce")
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce")
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], errors="coerce")
    df = df.dropna(subset=["Segment", "Approved", "Fraud", "TransactionDate"]).copy()

    df["Segment"] = df["Segment"].astype(int)
    df["Approved"] = df["Approved"].astype(int)
    df["Fraud"] = df["Fraud"].astype(int)

    as_of_date = df["TransactionDate"].max()
    mature_cutoff = as_of_date - pd.Timedelta(days=MATURITY_DAYS)
    mature_df = df.loc[df["TransactionDate"] <= mature_cutoff].copy()
    return mature_df, as_of_date, mature_cutoff


def build_entity_segment_rates(df, entity_col):
    summary = (
        df.groupby([entity_col, "Segment"], as_index=False)
        .agg(
            mature_rows=("Approved", "size"),
            approved_rows=("Approved", "sum"),
            fraud_rows=("Fraud", "sum"),
        )
        .sort_values([entity_col, "Segment"], ascending=[True, True])
        .reset_index(drop=True)
    )
    summary["approval_rate"] = summary["approved_rows"] / summary["mature_rows"]
    summary["fraud_rate_on_approved"] = summary["fraud_rows"] / summary["approved_rows"]
    summary.loc[summary["approved_rows"] == 0, "fraud_rate_on_approved"] = pd.NA
    return summary


def build_segment_baselines(df):
    baselines = (
        df.groupby("Segment", as_index=False)
        .agg(
            mature_rows=("Approved", "size"),
            approved_rows=("Approved", "sum"),
            fraud_rows=("Fraud", "sum"),
        )
        .sort_values("Segment")
        .reset_index(drop=True)
    )
    baselines["approval_rate"] = baselines["approved_rows"] / baselines["mature_rows"]
    baselines["fraud_rate_on_approved"] = baselines["fraud_rows"] / baselines["approved_rows"]
    baselines.loc[baselines["approved_rows"] == 0, "fraud_rate_on_approved"] = pd.NA
    return baselines


def main():
    mature_df, as_of_date, mature_cutoff = load_mature_dataset()

    bin_summary = build_entity_segment_rates(mature_df, "UserCardBIN")
    channel_summary = build_entity_segment_rates(mature_df, "Channel")
    segment_baselines = build_segment_baselines(mature_df)

    bin_summary.to_csv(BIN_OUTPUT_CSV, index=False)
    channel_summary.to_csv(CHANNEL_OUTPUT_CSV, index=False)
    segment_baselines.to_csv(SEGMENT_OUTPUT_CSV, index=False)

    print(f"As-of date: {as_of_date}")
    print(f"Mature cutoff ({MATURITY_DAYS} days): {mature_cutoff}")
    print(f"Mature rows kept: {len(mature_df):,}")
    print(f"BIN x Segment rows written: {len(bin_summary):,}")
    print(f"Channel x Segment rows written: {len(channel_summary):,}")
    print(f"Segment baseline rows written: {len(segment_baselines):,}")
    print(f"BIN output: {BIN_OUTPUT_CSV}")
    print(f"Channel output: {CHANNEL_OUTPUT_CSV}")
    print(f"Segment baseline output: {SEGMENT_OUTPUT_CSV}")


if __name__ == "__main__":
    main()
