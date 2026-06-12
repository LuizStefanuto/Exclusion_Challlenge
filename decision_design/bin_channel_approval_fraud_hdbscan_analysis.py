from datetime import datetime
from html import escape
from pathlib import Path

import hdbscan
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parent
APPROVAL_CSV = ROOT_DIR / "bin_channel_segment_approval.csv"
FRAUD_CSV = ROOT_DIR / "bin_channel_segment_fraud.csv"
OUTPUT_HTML = ROOT_DIR / "bin_channel_approval_fraud_hdbscan_analysis.html"
OUTPUT_CSV = ROOT_DIR / "bin_channel_approval_fraud_hdbscan_clusters.csv"

HIGH_VOLUME_MIN_ROWS = 100
HDBSCAN_MIN_CLUSTER_SIZE = 25
HDBSCAN_MIN_SAMPLES = 10

DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
TEXT = "#333333"
BACKGROUND = "#FAFAFA"
GRID = "rgba(0, 0, 0, 0.06)"
PALETTE = [
    "#4A90D9",
    "#E8A87C",
    "#5DA271",
    "#C06C84",
    "#6C5B7B",
    "#F0A202",
    "#2A9D8F",
]
NOISE_COLOR = "#B0B7C3"

REPORT_STYLE = """
    <style>
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 1320px;
            margin: 0 auto;
            padding: 24px;
            background: #f0f2f5;
            color: #1a1a2e;
        }
        h1 {
            color: #1a1a2e;
            font-size: 1.85em;
            font-weight: 600;
            margin-bottom: 6px;
            padding-bottom: 12px;
            border-bottom: 3px solid #4A90D9;
        }
        .subtitle {
            color: #666;
            font-size: 0.95em;
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 16px 18px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border-left: 4px solid #4A90D9;
        }
        .stat-label {
            color: #888;
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .stat-value {
            color: #1a1a2e;
            font-size: 1.35em;
            font-weight: 600;
            line-height: 1.25;
        }
        .panel, .observations {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin: 20px 0;
            overflow: hidden;
        }
        .section-header {
            padding: 16px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-header::before {
            content: '';
            width: 4px;
            height: 20px;
            background: #4A90D9;
            border-radius: 2px;
        }
        .section-title {
            font-weight: 600;
            color: #333;
            font-size: 1.05em;
        }
        .table-wrap {
            padding: 18px 20px 22px 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.94em;
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }
        th {
            color: #555;
            font-weight: 600;
            background: #fafbfd;
        }
        .observations {
            padding: 20px 24px;
        }
        .observations h2 {
            color: #333;
            font-size: 1.1em;
            font-weight: 600;
            margin: 0 0 12px 0;
        }
        .observations ul {
            margin: 0;
            padding-left: 20px;
            line-height: 1.9;
        }
        .badge {
            display: inline-block;
            background: #EEF4FA;
            color: #4A90D9;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 500;
            margin-right: 4px;
        }
    </style>
"""


def format_int(value):
    return f"{int(value):,}"


def format_float(value, decimals=3):
    return f"{float(value):.{decimals}f}"


def render_stats(cards):
    parts = ['<div class="stats-grid">']
    for label, value in cards:
        parts.append(
            f"""
            <div class="stat-card">
                <div class="stat-label">{escape(str(label))}</div>
                <div class="stat-value">{escape(str(value))}</div>
            </div>
            """
        )
    parts.append("</div>")
    return "".join(parts)


def render_table(title, dataframe):
    headers = "".join(f"<th>{escape(str(column))}</th>" for column in dataframe.columns)
    body_rows = []
    for row in dataframe.itertuples(index=False):
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        body_rows.append(f"<tr>{cells}</tr>")
    body_html = "".join(body_rows)
    return f"""
    <div class="panel">
        <div class="section-header">
            <div class="section-title">{escape(title)}</div>
        </div>
        <div class="table-wrap">
            <table>
                <thead><tr>{headers}</tr></thead>
                <tbody>{body_html}</tbody>
            </table>
        </div>
    </div>
    """


def render_observations(items):
    rows = "".join(
        f'<li><span class="badge">Observation</span> {escape(item)}</li>' for item in items
    )
    return f"""
    <div class="observations">
        <h2>Key Observations</h2>
        <ul>{rows}</ul>
    </div>
    """


def build_page(title, subtitle, stats_html, figure_html, tables_html, observations_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    {REPORT_STYLE}
</head>
<body>
    <h1>{escape(title)}</h1>
    <p class="subtitle">{subtitle}</p>
    {stats_html}
    <div class="panel">
        <div class="section-header">
            <div class="section-title">Cluster Chart</div>
        </div>
        {figure_html}
    </div>
    {tables_html}
    {observations_html}
</body>
</html>"""


def main():
    approval = pd.read_csv(APPROVAL_CSV)
    fraud = pd.read_csv(FRAUD_CSV)

    merged = approval.merge(
        fraud[
            [
                "UserCardBIN",
                "Channel",
                "fraud_rows",
                "observed_fraud_rate",
                "overall_fraud_rate_45d",
                "observed_fraud_relative",
                "expected_fraud_relative",
                "fraud_relative_gap",
                "fraud_relative_index",
            ]
        ],
        how="inner",
        on=["UserCardBIN", "Channel"],
    )
    merged = merged.loc[merged["rows"] > HIGH_VOLUME_MIN_ROWS].copy()

    if merged.empty:
        raise ValueError(f"No nodes remain after filtering rows > {HIGH_VOLUME_MIN_ROWS}.")

    X = merged[["approval_relative_gap", "fraud_relative_gap"]].to_numpy()
    model = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
    )
    merged["cluster_label"] = model.fit_predict(X)

    probabilities = pd.Series(model.probabilities_, index=merged.index, name="membership_probability")
    merged["membership_probability"] = probabilities
    cluster_summary = (
        merged.groupby("cluster_label")
        .agg(
            nodes=("cluster_label", "size"),
            median_approval_gap=("approval_relative_gap", "median"),
            median_fraud_gap=("fraud_relative_gap", "median"),
            median_rows=("rows", "median"),
            mean_membership_probability=("membership_probability", "mean"),
        )
        .reset_index()
        .sort_values(["nodes", "cluster_label"], ascending=[False, True])
    )

    non_noise = cluster_summary.loc[cluster_summary["cluster_label"] != -1].copy()
    if non_noise.empty:
        good_cluster_label = None
    else:
        good_candidates = non_noise.loc[
            (non_noise["median_approval_gap"] > 0) & (non_noise["median_fraud_gap"] < 0)
        ].copy()
        if good_candidates.empty:
            good_candidates = non_noise.copy()
        good_candidates["good_score"] = (
            good_candidates["median_approval_gap"] - good_candidates["median_fraud_gap"]
        )
        good_cluster_label = int(
            good_candidates.sort_values(
                ["nodes", "good_score"], ascending=[False, False]
            ).iloc[0]["cluster_label"]
        )

    def cluster_role(label):
        if label == -1:
            return "noise"
        if good_cluster_label is not None and label == good_cluster_label:
            return "good_cluster"
        return "other_cluster"

    merged["cluster_role"] = merged["cluster_label"].map(cluster_role)
    cluster_summary["cluster_role"] = cluster_summary["cluster_label"].map(cluster_role)

    merged.to_csv(OUTPUT_CSV, index=False)

    colors = {}
    palette_iter = iter(PALETTE)
    for label in sorted(merged["cluster_label"].unique()):
        if label == -1:
            colors[label] = NOISE_COLOR
        elif good_cluster_label is not None and label == good_cluster_label:
            colors[label] = "#2A9D8F"
        else:
            colors[label] = next(palette_iter, "#9C6644")

    fig = go.Figure()
    for label in sorted(merged["cluster_label"].unique()):
        subset = merged.loc[merged["cluster_label"] == label]
        name = (
            "Noise"
            if label == -1
            else f"Cluster {label}" + (" (Good Cluster)" if label == good_cluster_label else "")
        )
        fig.add_trace(
            go.Scatter(
                x=subset["approval_relative_gap"],
                y=subset["fraud_relative_gap"],
                mode="markers",
                name=name,
                marker=dict(
                    color=colors[label],
                    size=7,
                    opacity=0.5,
                ),
                customdata=subset[
                    [
                        "UserCardBIN",
                        "Channel",
                        "rows",
                        "approval_relative_gap",
                        "fraud_relative_gap",
                        "membership_probability",
                    ]
                ].values,
                hovertemplate=(
                    "<b>BIN:</b> %{customdata[0]}"
                    "<br><b>Channel:</b> %{customdata[1]}"
                    "<br><b>Rows:</b> %{customdata[2]:,}"
                    "<br><b>Approval gap:</b> %{customdata[3]:.3f}"
                    "<br><b>Fraud gap:</b> %{customdata[4]:.3f}"
                    "<br><b>Membership probability:</b> %{customdata[5]:.3f}"
                    "<extra></extra>"
                ),
            )
        )

    x_min = merged["approval_relative_gap"].min()
    x_max = merged["approval_relative_gap"].max()
    y_min = merged["fraud_relative_gap"].min()
    y_max = merged["fraud_relative_gap"].max()
    fig.add_shape(
        type="line",
        x0=0,
        x1=0,
        y0=y_min,
        y1=y_max,
        line=dict(color="#D9534F", width=2, dash="dash"),
    )
    fig.add_shape(
        type="line",
        x0=x_min,
        x1=x_max,
        y0=0,
        y1=0,
        line=dict(color="#D9534F", width=2, dash="dash"),
    )
    fig.update_layout(
        height=560,
        title_text="",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=60, r=30, t=30, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(
        title_text="Approval relative gap",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        tickcolor="#999",
        ticklen=4,
    )
    fig.update_yaxes(
        title_text="Fraud relative gap",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        tickcolor="#999",
        ticklen=4,
        autorange="reversed",
    )

    cluster_table = cluster_summary.copy()
    cluster_table["cluster_label"] = cluster_table["cluster_label"].map(
        lambda value: "Noise" if value == -1 else f"Cluster {int(value)}"
    )
    cluster_table["median_approval_gap"] = cluster_table["median_approval_gap"].map(
        lambda value: format_float(value, 3)
    )
    cluster_table["median_fraud_gap"] = cluster_table["median_fraud_gap"].map(
        lambda value: format_float(value, 3)
    )
    cluster_table["median_rows"] = cluster_table["median_rows"].map(format_int)
    cluster_table["nodes"] = cluster_table["nodes"].map(format_int)
    cluster_table["mean_membership_probability"] = cluster_table[
        "mean_membership_probability"
    ].map(lambda value: format_float(value, 3))
    cluster_table = cluster_table.rename(
        columns={
            "cluster_label": "Cluster",
            "cluster_role": "Role",
            "nodes": "Nodes",
            "median_approval_gap": "Median Approval Gap",
            "median_fraud_gap": "Median Fraud Gap",
            "median_rows": "Median Rows",
            "mean_membership_probability": "Mean Membership Probability",
        }
    )

    good_cluster_size = 0
    if good_cluster_label is not None:
        good_cluster_size = int(
            cluster_summary.loc[
                cluster_summary["cluster_label"] == good_cluster_label, "nodes"
            ].iloc[0]
        )
    noise_nodes = int((merged["cluster_label"] == -1).sum())
    cluster_count = int(
        len([label for label in merged["cluster_label"].unique() if label != -1])
    )

    stats = [
        ("High-Volume Nodes", format_int(len(merged))),
        ("Clusters Found", format_int(cluster_count)),
        ("Noise Nodes", format_int(noise_nodes)),
        ("Good Cluster Label", "None" if good_cluster_label is None else str(good_cluster_label)),
        ("Good Cluster Size", format_int(good_cluster_size)),
        (
            "HDBSCAN Params",
            f"min_cluster_size={HDBSCAN_MIN_CLUSTER_SIZE}, min_samples={HDBSCAN_MIN_SAMPLES}",
        ),
    ]

    observations = [
        "This HDBSCAN run uses the raw approval and fraud gap pair on the high-volume population only.",
        "The fraud axis is inverted in the chart, so lower still means worse fraud performance.",
        "HDBSCAN keeps the skewed dense good region while allowing sparser nodes to remain as smaller clusters or noise.",
        "The good cluster is identified as the dense cluster whose center sits in the good region: positive approval gap and negative fraud gap.",
        f"The current run finds a main good cluster of {format_int(good_cluster_size)} nodes and labels {format_int(noise_nodes)} nodes as noise or sparse outliers.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> HDBSCAN clustering of approval and fraud gaps for high-volume nodes with more than {HIGH_VOLUME_MIN_ROWS} rows."
    )

    html_content = build_page(
        title="BIN-Channel Approval-Fraud Cluster Analysis (HDBSCAN)",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        tables_html=render_table("Cluster Summary", cluster_table),
        observations_html=render_observations(observations),
    )
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    print(f"HTML report generated: {OUTPUT_HTML}")
    print(f"Cluster CSV generated: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
