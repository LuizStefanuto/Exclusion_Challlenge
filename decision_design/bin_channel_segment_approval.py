from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"
APPROVAL_SUMMARY_CSV = CHALLENGE_DIR / "bivariate_reports" / "segment_vs_approved_summary.csv"
OUTPUT_CSV = ROOT_DIR / "bin_channel_segment_approval.csv"


def main():
    df = pd.read_csv(DATASET_PATH, usecols=["UserCardBIN", "Channel", "Segment", "Approved"])
    df = df.dropna(subset=["UserCardBIN", "Channel", "Segment"]).copy()
    df["UserCardBIN"] = df["UserCardBIN"].astype(str)
    df["Channel"] = df["Channel"].astype(str)
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce")
    df["Approved"] = pd.to_numeric(df["Approved"], errors="coerce")
    df = df.dropna(subset=["Segment"]).copy()
    df["Segment"] = df["Segment"].astype(int)

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

    approval_subset = df.dropna(subset=["Approved"]).copy()
    approval_subset["Approved"] = approval_subset["Approved"].astype(int)
    overall_approval_rate = approval_subset["Approved"].mean()

    approval_summary_by_node = (
        approval_subset.groupby(["UserCardBIN", "Channel"])["Approved"]
        .agg(approved_rows="sum", observed_approval_rate="mean")
        .reset_index()
    )
    approval_summary_by_node["observed_approval_relative"] = (
        approval_summary_by_node["observed_approval_rate"] / overall_approval_rate
    )

    segment_counts = segment_counts.merge(
        approval_summary_by_node,
        how="left",
        on=["UserCardBIN", "Channel"],
    )

    approval_summary = pd.read_csv(APPROVAL_SUMMARY_CSV, usecols=["Segment", "approval_rate_index"])
    approval_relative = {
        int(row["Segment"]): float(row["approval_rate_index"])
        for _, row in approval_summary.iterrows()
    }

    for segment in [1, 2, 3, 4]:
        segment_counts[f"segment_{segment}_approval_relative"] = approval_relative[segment]
        segment_counts[f"segment_{segment}_weighted_approval_relative"] = (
            segment_counts[f"segment_{segment}_weight"]
            * segment_counts[f"segment_{segment}_approval_relative"]
        )

    segment_counts["expected_approval_relative"] = (
        segment_counts["segment_1_weighted_approval_relative"]
        + segment_counts["segment_2_weighted_approval_relative"]
        + segment_counts["segment_3_weighted_approval_relative"]
        + segment_counts["segment_4_weighted_approval_relative"]
    )
    segment_counts["approval_relative_gap"] = (
        segment_counts["observed_approval_relative"] - segment_counts["expected_approval_relative"]
    )
    segment_counts["approval_relative_index"] = (
        segment_counts["observed_approval_relative"] / segment_counts["expected_approval_relative"]
    )

    ordered_columns = [
        "UserCardBIN",
        "Channel",
        "rows",
        "approved_rows",
        "observed_approval_rate",
        "observed_approval_relative",
        "segment_1_rows",
        "segment_2_rows",
        "segment_3_rows",
        "segment_4_rows",
        "segment_1_weight",
        "segment_2_weight",
        "segment_3_weight",
        "segment_4_weight",
        "segment_1_approval_relative",
        "segment_2_approval_relative",
        "segment_3_approval_relative",
        "segment_4_approval_relative",
        "segment_1_weighted_approval_relative",
        "segment_2_weighted_approval_relative",
        "segment_3_weighted_approval_relative",
        "segment_4_weighted_approval_relative",
        "expected_approval_relative",
        "approval_relative_gap",
        "approval_relative_index",
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
