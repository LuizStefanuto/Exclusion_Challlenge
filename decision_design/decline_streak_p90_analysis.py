import math
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"
NODES_CSV = ROOT_DIR / "bin_channel_segment_approval.csv"
OUTPUT_HTML = ROOT_DIR / "decline_streak_p90_analysis.html"
OUTPUT_THRESHOLDS_CSV = ROOT_DIR / "decline_streak_p90_thresholds.csv"
OUTPUT_FLAGGED_CSV = ROOT_DIR / "decline_streak_p90_flagged_nodes.csv"

LOW_VOLUME_MAX_ROWS = 100
DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
PRIMARY = "#4A90D9"
SECONDARY = "#7FB3D3"
ACCENT = "#E8A87C"
ALERT = "#D9534F"
TEXT = "#333333"
BACKGROUND = "#FAFAFA"
GRID = "rgba(0, 0, 0, 0.06)"

REPORT_STYLE = """
    <style>
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 1280px;
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
        .chart-container, .table-container, .observations {
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


def format_pct(value, decimals=2):
    return f"{float(value):.{decimals}f}%"


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
    <div class="table-container">
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
        <ul>
            {rows}
        </ul>
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
    <div class="chart-container">
        <div class="section-header">
            <div class="section-title">Threshold Charts</div>
        </div>
        {figure_html}
    </div>
    {tables_html}
    {observations_html}
</body>
</html>"""


def apply_layout(fig):
    fig.update_layout(
        showlegend=False,
        height=560,
        title_text="",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=60, r=30, t=40, b=50),
    )
    for annotation in fig.layout.annotations:
        annotation.font = dict(
            family="Segoe UI, -apple-system, sans-serif",
            size=13,
            color=TEXT,
        )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickcolor="#999", ticklen=4)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickcolor="#999", ticklen=4)


def compute_max_decline_streak(approved_values):
    max_streak = 0
    current_streak = 0
    for approved in approved_values:
        if approved == 0:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        else:
            current_streak = 0
    return max_streak


def main():
    nodes = pd.read_csv(NODES_CSV, usecols=["UserCardBIN", "Channel", "rows"])
    nodes["UserCardBIN"] = nodes["UserCardBIN"].astype(str)
    nodes["Channel"] = nodes["Channel"].astype(str)

    reference_nodes = nodes.loc[nodes["rows"] > LOW_VOLUME_MAX_ROWS].copy()
    low_volume_nodes = nodes.loc[nodes["rows"] <= LOW_VOLUME_MAX_ROWS].copy()

    transactions = pd.read_csv(
        DATASET_PATH,
        usecols=["UserCardBIN", "Channel", "Segment", "TransactionDate", "Approved"],
    )
    transactions["UserCardBIN"] = transactions["UserCardBIN"].astype(str)
    transactions["Channel"] = transactions["Channel"].astype(str)
    transactions["Segment"] = pd.to_numeric(transactions["Segment"], errors="coerce")
    transactions["Approved"] = pd.to_numeric(transactions["Approved"], errors="coerce")
    transactions["TransactionDate"] = pd.to_datetime(
        transactions["TransactionDate"], errors="coerce"
    )
    transactions = transactions.dropna(
        subset=["Segment", "Approved", "TransactionDate"]
    ).copy()
    transactions["Segment"] = transactions["Segment"].astype(int)
    transactions["Approved"] = transactions["Approved"].astype(int)

    streak_rows = []
    grouped = transactions.groupby(["UserCardBIN", "Channel", "Segment"], sort=False)
    for (bin_value, channel_value, segment), group in grouped:
        ordered = group.sort_values("TransactionDate")
        streak_rows.append(
            {
                "UserCardBIN": bin_value,
                "Channel": channel_value,
                "Segment": segment,
                "segment_rows": len(ordered),
                "segment_approval_rate": ordered["Approved"].mean(),
                "max_consecutive_declines": compute_max_decline_streak(
                    ordered["Approved"].tolist()
                ),
            }
        )

    streaks = pd.DataFrame(streak_rows)

    reference_streaks = streaks.merge(
        reference_nodes, how="inner", on=["UserCardBIN", "Channel"]
    )
    thresholds = (
        reference_streaks.groupby("Segment")
        .agg(
            reference_nodes_with_segment=("max_consecutive_declines", "size"),
            p90_decline_streak=(
                "max_consecutive_declines",
                lambda series: series.quantile(0.90),
            ),
            median_decline_streak=("max_consecutive_declines", "median"),
            max_decline_streak=("max_consecutive_declines", "max"),
        )
        .reset_index()
    )
    thresholds["decline_streak_threshold"] = thresholds["p90_decline_streak"].apply(
        lambda value: int(math.ceil(value))
    )

    low_volume_streaks = streaks.merge(
        low_volume_nodes, how="inner", on=["UserCardBIN", "Channel"]
    ).merge(
        thresholds[["Segment", "decline_streak_threshold"]],
        how="left",
        on="Segment",
    )
    low_volume_streaks["flagged"] = (
        low_volume_streaks["max_consecutive_declines"]
        >= low_volume_streaks["decline_streak_threshold"]
    )

    node_flags = (
        low_volume_streaks.groupby(["UserCardBIN", "Channel"])
        .agg(
            rows=("rows", "max"),
            flagged=("flagged", "max"),
            triggering_segments=(
                "Segment",
                lambda series: ", ".join(
                    str(value)
                    for value in sorted(
                        set(
                            series[
                                low_volume_streaks.loc[series.index, "flagged"].values
                            ]
                        )
                    )
                ),
            ),
        )
        .reset_index()
    )
    node_flags["triggering_segments"] = node_flags["triggering_segments"].replace("", pd.NA)

    flagged_nodes = (
        low_volume_streaks.loc[low_volume_streaks["flagged"]]
        .sort_values(
            ["rows", "segment_rows", "max_consecutive_declines", "UserCardBIN", "Channel"],
            ascending=[False, False, False, True, True],
        )
        .merge(
            node_flags[["UserCardBIN", "Channel", "triggering_segments"]],
            how="left",
            on=["UserCardBIN", "Channel"],
        )
    )
    flagged_nodes = flagged_nodes[
        [
            "UserCardBIN",
            "Channel",
            "rows",
            "Segment",
            "segment_rows",
            "segment_approval_rate",
            "max_consecutive_declines",
            "decline_streak_threshold",
            "triggering_segments",
        ]
    ].rename(
        columns={
            "Segment": "TriggerSegment",
            "segment_rows": "TriggerSegmentRows",
            "segment_approval_rate": "TriggerSegmentApprovalRate",
            "max_consecutive_declines": "TriggerSegmentMaxConsecutiveDeclines",
            "decline_streak_threshold": "TriggerSegmentThreshold",
        }
    )
    flagged_nodes = flagged_nodes.drop_duplicates(
        subset=["UserCardBIN", "Channel", "TriggerSegment"]
    )

    thresholds_export = thresholds.copy()
    thresholds_export["p90_decline_streak"] = thresholds_export["p90_decline_streak"].round(2)
    thresholds_export["median_decline_streak"] = thresholds_export[
        "median_decline_streak"
    ].round(2)
    thresholds_export.to_csv(OUTPUT_THRESHOLDS_CSV, index=False)
    flagged_nodes.to_csv(OUTPUT_FLAGGED_CSV, index=False)

    flagged_share = node_flags["flagged"].mean() * 100
    flagged_segment_counts = (
        low_volume_streaks.groupby("Segment")["flagged"]
        .agg(flagged_segment_rows="sum", total_segment_rows="size")
        .reset_index()
    )
    flagged_segment_counts["flagged_share_pct"] = (
        flagged_segment_counts["flagged_segment_rows"]
        / flagged_segment_counts["total_segment_rows"]
        * 100
    )

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=(
            "<b>Reference Decline-Streak Distribution by Segment</b>",
            "<b>Flagged Low-Volume Node-Segments</b>",
            "<b>Rows in Flagged Nodes</b>",
        ),
        horizontal_spacing=0.10,
    )
    segment_colors = {
        1: "#4A90D9",
        2: "#7FB3D3",
        3: "#E8A87C",
        4: "#D9534F",
    }
    for segment in [1, 2, 3, 4]:
        segment_distribution = reference_streaks.loc[
            reference_streaks["Segment"] == segment, "max_consecutive_declines"
        ]
        fig.add_trace(
            go.Box(
                y=segment_distribution,
                name=f"Segment {segment}",
                marker_color=segment_colors[segment],
                boxmean=True,
                hovertemplate=(
                    f"<b>Segment {segment}</b><br>"
                    "Max declines: %{y}<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=[f"Segment {segment}" for segment in thresholds["Segment"]],
            y=thresholds["p90_decline_streak"],
            mode="markers+text",
            marker=dict(color=ALERT, size=11, symbol="diamond"),
            text=[f"P90: {value:.1f}" for value in thresholds["p90_decline_streak"]],
            textposition="top center",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "P90 decline streak: %{y:.1f}<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=[f"Segment {segment}" for segment in flagged_segment_counts["Segment"]],
            y=flagged_segment_counts["flagged_segment_rows"],
            marker_color=ACCENT,
            text=flagged_segment_counts["flagged_segment_rows"].map(lambda value: f"{value:,}"),
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Flagged node-segments: %{y:,}<br>"
                "<extra></extra>"
            ),
        ),
        row=1,
        col=2,
    )
    flagged_node_rows = node_flags.loc[node_flags["flagged"], "rows"]
    fig.add_trace(
        go.Histogram(
            x=flagged_node_rows,
            nbinsx=25,
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            hovertemplate=(
                "<b>Rows:</b> %{x}<br>"
                "<b>Flagged nodes:</b> %{y:,}<extra></extra>"
            ),
        ),
        row=1,
        col=3,
    )
    apply_layout(fig)
    fig.update_xaxes(title_text="Segment", row=1, col=1)
    fig.update_yaxes(title_text="Max consecutive declines", row=1, col=1)
    fig.update_xaxes(title_text="Segment", row=1, col=2)
    fig.update_yaxes(title_text="Flagged node-segments", row=1, col=2)
    fig.update_xaxes(title_text="Rows in flagged node", row=1, col=3)
    fig.update_yaxes(title_text="Number of flagged nodes", row=1, col=3)

    stats = [
        ("Reference Nodes", format_int(len(reference_nodes))),
        ("Low-Volume Nodes", format_int(len(node_flags))),
        ("Flagged Low-Volume Nodes", format_int(int(node_flags["flagged"].sum()))),
        ("Flagged Share", format_pct(flagged_share, 2)),
        ("Segment 1 Threshold", format_int(thresholds.loc[thresholds["Segment"] == 1, "decline_streak_threshold"].iloc[0])),
        ("Segment 4 Threshold", format_int(thresholds.loc[thresholds["Segment"] == 4, "decline_streak_threshold"].iloc[0])),
    ]

    threshold_table = thresholds_export.rename(
        columns={
            "Segment": "Segment",
            "reference_nodes_with_segment": "Reference Nodes With Segment",
            "p90_decline_streak": "P90 Streak",
            "decline_streak_threshold": "Applied Threshold",
            "median_decline_streak": "Median Streak",
            "max_decline_streak": "Max Streak",
        }
    )

    flagged_table = flagged_nodes.head(12).copy()
    flagged_table = flagged_table[
        [
            "UserCardBIN",
            "Channel",
            "rows",
            "TriggerSegment",
            "TriggerSegmentMaxConsecutiveDeclines",
            "TriggerSegmentThreshold",
        ]
    ].rename(
        columns={
            "UserCardBIN": "BIN",
            "Channel": "Channel",
            "rows": "Rows",
            "TriggerSegment": "Segment",
            "TriggerSegmentMaxConsecutiveDeclines": "Max Declines",
            "TriggerSegmentThreshold": "Threshold",
        }
    )

    observations = [
        f"The segment-specific decline-streak thresholds are based on all BIN-Channel nodes with more than {format_int(LOW_VOLUME_MAX_ROWS)} rows, using the ceiling of the segment P90 streak.",
        f"Applying those thresholds to nodes with up to {format_int(LOW_VOLUME_MAX_ROWS)} rows flags {format_int(int(node_flags['flagged'].sum()))} nodes, or {format_pct(flagged_share, 2)} of the low-volume universe.",
        "The thresholds rise sharply by segment, which means a fixed decline-streak rule would over-penalize higher-risk segments.",
        "Most flagged low-volume node-segments come from Segments 1 and 2 because their acceptable streak thresholds are much tighter than Segment 4.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> Segment-specific P90 decline-streak rule from all nodes with more than {LOW_VOLUME_MAX_ROWS} rows, applied to nodes with up to {LOW_VOLUME_MAX_ROWS} rows."
    )

    html_content = build_page(
        title="Decline Streak P90 Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        tables_html=(
            render_table("Segment Thresholds", threshold_table)
            + render_table("Sample Flagged Nodes", flagged_table)
        ),
        observations_html=render_observations(observations),
    )
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    print(f"HTML report generated: {OUTPUT_HTML}")
    print(f"Thresholds CSV generated: {OUTPUT_THRESHOLDS_CSV}")
    print(f"Flagged nodes CSV generated: {OUTPUT_FLAGGED_CSV}")


if __name__ == "__main__":
    main()
