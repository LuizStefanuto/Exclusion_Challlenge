from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"
FRAUD_MATURITY_CSV = CHALLENGE_DIR / "multivariate_reports" / "segment_vs_fraud_maturity_sensitivity.csv"
OUTPUT_CSV = ROOT_DIR / "bin_channel_segment_fraud.csv"
FRAUD_MATURITY_CUTOFF_DAYS = 45


def main():
    df = pd.read_csv(DATASET_PATH, usecols=["UserCardBIN", "Channel", "Segment", "Fraud"])
    df = df.dropna(subset=["UserCardBIN", "Channel", "Segment"]).copy()
    df["UserCardBIN"] = df["UserCardBIN"].astype(str)
    df["Channel"] = df["Channel"].astype(str)
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce")
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce")
    df = df.dropna(subset=["Segment"]).copy()
    df["Segment"] = df["Segment"].astype(int)

    maturity_baselines = pd.read_csv(FRAUD_MATURITY_CSV)
    maturity_row = maturity_baselines.loc[
        maturity_baselines["cutoff_days"] == FRAUD_MATURITY_CUTOFF_DAYS
    ]
    if maturity_row.empty:
        raise ValueError(
            f"No maturity row found for cutoff_days == {FRAUD_MATURITY_CUTOFF_DAYS}."
        )
    maturity_row = maturity_row.iloc[0]
    overall_fraud_rate = float(maturity_row["overall_fraud_rate_pct"]) / 100.0

    segment_relative = {
        1: float(maturity_row["segment_1_relative_rate"]),
        2: float(maturity_row["segment_2_relative_rate"]),
        3: float(maturity_row["segment_3_relative_rate"]),
        4: float(maturity_row["segment_4_relative_rate"]),
    }

    segment_counts = (
        df.groupby(["UserCardBIN", "Channel", "Segment"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[1, 2, 3, 4], fill_value=0)
        .reset_index()
    )
    segment_counts = segment_counts.rename(
        columns={
            1: "segment_1_rows",
            2: "segment_2_rows",
            3: "segment_3_rows",
            4: "segment_4_rows",
        }
    )
    segment_counts["rows"] = (
        segment_counts["segment_1_rows"]
        + segment_counts["segment_2_rows"]
        + segment_counts["segment_3_rows"]
        + segment_counts["segment_4_rows"]
    )
    for segment in [1, 2, 3, 4]:
        segment_counts[f"segment_{segment}_weight"] = (
            segment_counts[f"segment_{segment}_rows"] / segment_counts["rows"]
        )

    summary = (
        df.groupby(["UserCardBIN", "Channel"])["Fraud"]
        .agg(fraud_rows="sum", observed_fraud_rate="mean")
        .reset_index()
    )
    summary["fraud_rows"] = summary["fraud_rows"].fillna(0).astype(int)
    summary["overall_fraud_rate_45d"] = overall_fraud_rate
    summary["observed_fraud_relative"] = (
        summary["observed_fraud_rate"] / overall_fraud_rate
    )
    segment_counts = segment_counts.merge(
        summary,
        how="left",
        on=["UserCardBIN", "Channel"],
    )
    for segment in [1, 2, 3, 4]:
        segment_counts[f"segment_{segment}_fraud_relative"] = segment_relative[segment]
        segment_counts[f"segment_{segment}_weighted_fraud_relative"] = (
            segment_counts[f"segment_{segment}_weight"]
            * segment_counts[f"segment_{segment}_fraud_relative"]
        )
    segment_counts["expected_fraud_relative"] = (
        segment_counts["segment_1_weighted_fraud_relative"]
        + segment_counts["segment_2_weighted_fraud_relative"]
        + segment_counts["segment_3_weighted_fraud_relative"]
        + segment_counts["segment_4_weighted_fraud_relative"]
    )
    segment_counts["fraud_relative_gap"] = (
        segment_counts["observed_fraud_relative"] - segment_counts["expected_fraud_relative"]
    )
    segment_counts["fraud_relative_index"] = (
        segment_counts["observed_fraud_relative"] / segment_counts["expected_fraud_relative"]
    )

    ordered_columns = [
        "UserCardBIN",
        "Channel",
        "rows",
        "fraud_rows",
        "observed_fraud_rate",
        "overall_fraud_rate_45d",
        "observed_fraud_relative",
        "segment_1_rows",
        "segment_2_rows",
        "segment_3_rows",
        "segment_4_rows",
        "segment_1_weight",
        "segment_2_weight",
        "segment_3_weight",
        "segment_4_weight",
        "segment_1_fraud_relative",
        "segment_2_fraud_relative",
        "segment_3_fraud_relative",
        "segment_4_fraud_relative",
        "segment_1_weighted_fraud_relative",
        "segment_2_weighted_fraud_relative",
        "segment_3_weighted_fraud_relative",
        "segment_4_weighted_fraud_relative",
        "expected_fraud_relative",
        "fraud_relative_gap",
        "fraud_relative_index",
    ]

    output = segment_counts[ordered_columns].sort_values(
        by=["rows", "UserCardBIN", "Channel"],
        ascending=[False, True, True],
    )
    output.to_csv(OUTPUT_CSV, index=False)

    print(f"Rows exported: {len(output):,}")
    print(f"Output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
