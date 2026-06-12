from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parent
APPROVAL_CSV = ROOT_DIR / "bin_channel_segment_approval.csv"
FRAUD_CSV = ROOT_DIR / "bin_channel_segment_fraud.csv"
OUTPUT_HTML = ROOT_DIR / "bin_channel_graph_analysis.html"
EDGE_OUTPUT_CSV = ROOT_DIR / "bin_channel_graph_edges.csv"
BIN_OUTPUT_CSV = ROOT_DIR / "bin_graph_summary.csv"
CHANNEL_OUTPUT_CSV = ROOT_DIR / "channel_graph_summary.csv"

HIGH_VOLUME_MIN_ROWS = 100
DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
DISPLAY_TOP_LABELS = 12

BIN_COLOR = "#4A90D9"
CHANNEL_COLOR = "#E8A87C"
EDGE_COLOR = "rgba(217, 83, 79, 0.20)"
TEXT = "#333333"
BACKGROUND = "#FAFAFA"

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
            font-size: 0.93em;
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
            <div class="section-title">Node-Link Graph</div>
        </div>
        {figure_html}
    </div>
    {tables_html}
    {observations_html}
</body>
</html>"""


def scale_sizes(series, min_size, max_size):
    series = series.astype(float)
    if series.nunique() <= 1:
        return pd.Series([0.5 * (min_size + max_size)] * len(series), index=series.index)
    scaled = (series - series.min()) / (series.max() - series.min())
    return min_size + scaled * (max_size - min_size)


def weighted_neighbor_position(group, other_positions):
    mapped = group["neighbor"].map(other_positions)
    if mapped.isna().all():
        return group["current_order"].iloc[0]
    weights = group["rows"].astype(float)
    return (mapped.fillna(group["current_order"].iloc[0]) * weights).sum() / weights.sum()


def compute_bipartite_order(edges, left_col, right_col, iterations=6):
    left_summary = edges.groupby(left_col, as_index=False)["rows"].sum().sort_values("rows", ascending=False)
    right_summary = edges.groupby(right_col, as_index=False)["rows"].sum().sort_values("rows", ascending=False)

    left_order = left_summary[left_col].tolist()
    right_order = right_summary[right_col].tolist()

    left_links = edges[[left_col, right_col, "rows"]].rename(columns={left_col: "node", right_col: "neighbor"})
    right_links = edges[[right_col, left_col, "rows"]].rename(columns={right_col: "node", left_col: "neighbor"})

    for _ in range(iterations):
        right_positions = {value: index for index, value in enumerate(right_order)}
        temp = left_links.copy()
        temp["current_order"] = temp["node"].map({value: index for index, value in enumerate(left_order)})
        left_scores = temp.groupby("node", as_index=False).apply(
            lambda g: pd.Series({"score": weighted_neighbor_position(g, right_positions)}),
            include_groups=False,
        )
        left_order = left_scores.sort_values("score")["node"].tolist()

        left_positions = {value: index for index, value in enumerate(left_order)}
        temp = right_links.copy()
        temp["current_order"] = temp["node"].map({value: index for index, value in enumerate(right_order)})
        right_scores = temp.groupby("node", as_index=False).apply(
            lambda g: pd.Series({"score": weighted_neighbor_position(g, left_positions)}),
            include_groups=False,
        )
        right_order = right_scores.sort_values("score")["node"].tolist()

    return left_order, right_order


def main():
    approval = pd.read_csv(APPROVAL_CSV, dtype={"UserCardBIN": str, "Channel": str})
    fraud = pd.read_csv(FRAUD_CSV, dtype={"UserCardBIN": str, "Channel": str})

    merged = approval.merge(
        fraud[
            [
                "UserCardBIN",
                "Channel",
                "fraud_rows",
                "observed_fraud_rate",
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
    merged["is_concern"] = (
        (merged["approval_relative_gap"] < 0) & (merged["fraud_relative_gap"] > 0)
    )
    merged["severity_score"] = (
        (-merged["approval_relative_gap"]).clip(lower=0)
        + merged["fraud_relative_gap"].clip(lower=0)
    )

    concern = merged.loc[merged["is_concern"]].copy()
    if concern.empty:
        raise ValueError("No concern edges found in the high-volume population.")

    bin_summary = (
        concern.groupby("UserCardBIN", as_index=False)
        .agg(
            concern_edges=("Channel", "nunique"),
            concern_rows=("rows", "sum"),
        )
        .sort_values(["concern_rows", "concern_edges"], ascending=[False, False])
    )
    channel_summary = (
        concern.groupby("Channel", as_index=False)
        .agg(
            concern_edges=("UserCardBIN", "nunique"),
            concern_rows=("rows", "sum"),
        )
        .sort_values(["concern_rows", "concern_edges"], ascending=[False, False])
    )

    left_order, right_order = compute_bipartite_order(concern, "UserCardBIN", "Channel")
    bin_y = {value: index for index, value in enumerate(left_order[::-1])}
    channel_y = {value: index for index, value in enumerate(right_order[::-1])}

    concern["bin_y"] = concern["UserCardBIN"].map(bin_y)
    concern["channel_y"] = concern["Channel"].map(channel_y)
    concern["edge_width"] = scale_sizes(concern["rows"], 1.0, 6.0)
    concern["edge_opacity"] = scale_sizes(concern["severity_score"], 0.18, 0.50)

    bin_summary["y"] = bin_summary["UserCardBIN"].map(bin_y)
    channel_summary["y"] = channel_summary["Channel"].map(channel_y)
    bin_summary["marker_size"] = scale_sizes(bin_summary["concern_rows"], 10, 28)
    channel_summary["marker_size"] = scale_sizes(channel_summary["concern_rows"], 10, 28)

    concern.to_csv(EDGE_OUTPUT_CSV, index=False)
    bin_summary.to_csv(BIN_OUTPUT_CSV, index=False)
    channel_summary.to_csv(CHANNEL_OUTPUT_CSV, index=False)

    fig = go.Figure()

    for row in concern.itertuples(index=False):
        alpha = max(0.12, min(0.55, float(row.edge_opacity)))
        fig.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[row.bin_y, row.channel_y],
                mode="lines",
                line=dict(color=f"rgba(217, 83, 79, {alpha:.3f})", width=float(row.edge_width)),
                hovertemplate=(
                    f"<b>BIN:</b> {escape(str(row.UserCardBIN))}"
                    f"<br><b>Channel:</b> {escape(str(row.Channel))}"
                    f"<br><b>Rows:</b> {format_int(row.rows)}"
                    f"<br><b>Approval gap:</b> {format_float(row.approval_relative_gap, 3)}"
                    f"<br><b>Fraud gap:</b> {format_float(row.fraud_relative_gap, 3)}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    top_bin_labels = set(bin_summary.head(DISPLAY_TOP_LABELS)["UserCardBIN"])
    top_channel_labels = set(channel_summary.head(DISPLAY_TOP_LABELS)["Channel"])

    fig.add_trace(
        go.Scatter(
            x=[0] * len(bin_summary),
            y=bin_summary["y"],
            mode="markers+text",
            text=[value if value in top_bin_labels else "" for value in bin_summary["UserCardBIN"]],
            textposition="middle left",
            marker=dict(
                color=BIN_COLOR,
                size=bin_summary["marker_size"],
                line=dict(color="white", width=1),
            ),
            customdata=bin_summary[["UserCardBIN", "concern_edges", "concern_rows"]].values,
            hovertemplate=(
                "<b>BIN:</b> %{customdata[0]}"
                "<br><b>Concern edges:</b> %{customdata[1]:,}"
                "<br><b>Concern rows:</b> %{customdata[2]:,}<extra></extra>"
            ),
            name="BIN nodes",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[1] * len(channel_summary),
            y=channel_summary["y"],
            mode="markers+text",
            text=[value if value in top_channel_labels else "" for value in channel_summary["Channel"]],
            textposition="middle right",
            marker=dict(
                color=CHANNEL_COLOR,
                size=channel_summary["marker_size"],
                line=dict(color="white", width=1),
            ),
            customdata=channel_summary[["Channel", "concern_edges", "concern_rows"]].values,
            hovertemplate=(
                "<b>Channel:</b> %{customdata[0]}"
                "<br><b>Concern edges:</b> %{customdata[1]:,}"
                "<br><b>Concern rows:</b> %{customdata[2]:,}<extra></extra>"
            ),
            name="Channel nodes",
        )
    )

    fig.add_annotation(
        x=0,
        y=max(bin_summary["y"].max(), channel_summary["y"].max()) + 3,
        text="<b>BIN Nodes</b>",
        showarrow=False,
        font=dict(size=14, color=TEXT),
    )
    fig.add_annotation(
        x=1,
        y=max(bin_summary["y"].max(), channel_summary["y"].max()) + 3,
        text="<b>Channel Nodes</b>",
        showarrow=False,
        font=dict(size=14, color=TEXT),
    )

    fig.update_layout(
        height=max(680, int(max(len(bin_summary), len(channel_summary)) * 8)),
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=120, r=120, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    )
    fig.update_xaxes(visible=False, range=[-0.15, 1.15], fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True)

    top_edges = concern.sort_values(["severity_score", "rows"], ascending=[False, False]).head(15).copy()
    top_edges["rows"] = top_edges["rows"].map(format_int)
    top_edges["approval_relative_gap"] = top_edges["approval_relative_gap"].map(lambda value: format_float(value, 3))
    top_edges["fraud_relative_gap"] = top_edges["fraud_relative_gap"].map(lambda value: format_float(value, 3))
    top_edges = top_edges.rename(
        columns={
            "UserCardBIN": "BIN",
            "Channel": "Channel",
            "rows": "Rows",
            "approval_relative_gap": "Approval Gap",
            "fraud_relative_gap": "Fraud Gap",
        }
    )[["BIN", "Channel", "Rows", "Approval Gap", "Fraud Gap"]]

    top_bins = bin_summary.head(12).copy()
    top_bins["concern_edges"] = top_bins["concern_edges"].map(format_int)
    top_bins["concern_rows"] = top_bins["concern_rows"].map(format_int)
    top_bins = top_bins.rename(
        columns={
            "UserCardBIN": "BIN",
            "concern_edges": "Concern Edges",
            "concern_rows": "Concern Rows",
        }
    )[["BIN", "Concern Edges", "Concern Rows"]]

    top_channels = channel_summary.head(12).copy()
    top_channels["concern_edges"] = top_channels["concern_edges"].map(format_int)
    top_channels["concern_rows"] = top_channels["concern_rows"].map(format_int)
    top_channels = top_channels.rename(
        columns={
            "Channel": "Channel",
            "concern_edges": "Concern Edges",
            "concern_rows": "Concern Rows",
        }
    )[["Channel", "Concern Edges", "Concern Rows"]]

    stats = [
        ("High-Volume Concern Edges", format_int(len(concern))),
        ("BIN Nodes", format_int(len(bin_summary))),
        ("Channel Nodes", format_int(len(channel_summary))),
        ("Median Concern Rows per Edge", format_int(concern["rows"].median())),
        ("Median BIN Concern Degree", format_int(bin_summary["concern_edges"].median())),
        ("Median Channel Concern Degree", format_int(channel_summary["concern_edges"].median())),
    ]

    observations = [
        "This is a direct node-link view of the bad high-volume BIN-Channel edges only.",
        "BIN nodes are on the left and Channel nodes are on the right.",
        "Each red line is one concern edge: worse than expected on approval and worse than expected on fraud.",
        "The fraud side of that definition is benchmarked against the 45-day mature segment baselines, so recent fraud-label immaturity is partly controlled before the graph is drawn.",
        "Node size reflects how many concern rows that BIN or Channel carries inside this concern subgraph.",
        "Edge thickness reflects how many rows sit on that bad BIN-Channel edge.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> Node-link graph of high-volume concern edges with more than {HIGH_VOLUME_MIN_ROWS} rows, using the approval-side gaps and fraud-side gaps benchmarked to the 45-day mature segment baselines."
    )

    tables_html = (
        render_table("Top Concern Edges", top_edges)
        + render_table("Top BIN Nodes in Concern Graph", top_bins)
        + render_table("Top Channel Nodes in Concern Graph", top_channels)
    )

    html_content = build_page(
        title="BIN-Channel Concern Graph",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        tables_html=tables_html,
        observations_html=render_observations(observations),
    )
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    print(f"HTML report generated: {OUTPUT_HTML}")
    print(f"Edge CSV generated: {EDGE_OUTPUT_CSV}")
    print(f"BIN summary CSV generated: {BIN_OUTPUT_CSV}")
    print(f"Channel summary CSV generated: {CHANNEL_OUTPUT_CSV}")


if __name__ == "__main__":
    main()
