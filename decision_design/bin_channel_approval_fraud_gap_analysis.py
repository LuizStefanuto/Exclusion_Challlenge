from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parent
APPROVAL_CSV = ROOT_DIR / "bin_channel_segment_approval.csv"
FRAUD_CSV = ROOT_DIR / "bin_channel_segment_fraud.csv"
OUTPUT_HTML = ROOT_DIR / "bin_channel_approval_fraud_gap_analysis.html"
HIGH_VOLUME_MIN_ROWS = 100

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
        .chart-container, .observations {
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


def build_page(title, subtitle, stats_html, figure_html, observations_html):
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
            <div class="section-title">Combined Gap Chart</div>
        </div>
        {figure_html}
    </div>
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

    bad_both = ((merged["approval_relative_gap"] < 0) & (merged["fraud_relative_gap"] > 0)).sum()
    good_both = ((merged["approval_relative_gap"] > 0) & (merged["fraud_relative_gap"] < 0)).sum()
    approval_bad_fraud_good = ((merged["approval_relative_gap"] < 0) & (merged["fraud_relative_gap"] < 0)).sum()
    approval_good_fraud_bad = ((merged["approval_relative_gap"] > 0) & (merged["fraud_relative_gap"] > 0)).sum()

    x_min = merged["approval_relative_gap"].min()
    x_max = merged["approval_relative_gap"].max()
    y_min = merged["fraud_relative_gap"].min()
    y_max = merged["fraud_relative_gap"].max()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=merged["approval_relative_gap"],
            y=merged["fraud_relative_gap"],
            mode="markers",
            marker=dict(color=PRIMARY, size=7, opacity=0.28),
            customdata=merged[
                [
                    "UserCardBIN",
                    "Channel",
                    "rows",
                    "approval_relative_gap",
                    "fraud_relative_gap",
                    "approval_relative_index",
                    "fraud_relative_index",
                ]
            ].values,
            hovertemplate=(
                "<b>BIN:</b> %{customdata[0]}"
                "<br><b>Channel:</b> %{customdata[1]}"
                "<br><b>Rows:</b> %{customdata[2]:,}"
                "<br><b>Approval gap:</b> %{customdata[3]:.3f}"
                "<br><b>Fraud gap:</b> %{customdata[4]:.3f}"
                "<br><b>Approval index:</b> %{customdata[5]:.3f}"
                "<br><b>Fraud index:</b> %{customdata[6]:.3f}"
                "<extra></extra>"
            ),
        )
    )
    fig.add_shape(
        type="line",
        x0=0,
        x1=0,
        y0=y_min,
        y1=y_max,
        line=dict(color=ALERT, width=2, dash="dash"),
    )
    fig.add_shape(
        type="line",
        x0=x_min,
        x1=x_max,
        y0=0,
        y1=0,
        line=dict(color=ALERT, width=2, dash="dash"),
    )
    fig.update_layout(
        height=560,
        title_text="",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=60, r=30, t=30, b=50),
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

    stats = [
        ("High-Volume Nodes", format_int(len(merged))),
        ("Median Rows", format_int(merged["rows"].median())),
        ("Median Approval Gap", format_float(merged["approval_relative_gap"].median(), 3)),
        ("Median Fraud Gap", format_float(merged["fraud_relative_gap"].median(), 3)),
        ("Bad on Both Sides", format_int(bad_both)),
        ("Good on Both Sides", format_int(good_both)),
    ]

    observations = [
        "Each point is one BIN-Channel node from the high-volume population, meaning nodes with more than 100 rows.",
        "The horizontal axis shows approval relative gap. Values left of zero are approving worse than expected for the node's segment mix.",
        "The vertical axis shows fraud relative gap, but it is inverted so that worse-than-expected fraud appears lower on the chart.",
        f"The lower-left quadrant is the main concern area because it combines worse-than-expected approval with worse-than-expected fraud. It currently contains {format_int(bad_both)} high-volume nodes.",
        f"The upper-right quadrant is the best area because it combines better-than-expected approval with lower-than-expected fraud. It currently contains {format_int(good_both)} high-volume nodes.",
        f"The mixed quadrants still matter: {format_int(approval_bad_fraud_good)} nodes are weak on approval but better than expected on fraud, while {format_int(approval_good_fraud_bad)} are strong on approval but worse than expected on fraud.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> First combined view of approval and fraud gaps for high-volume nodes with more than {HIGH_VOLUME_MIN_ROWS} rows."
    )

    html_content = build_page(
        title="BIN-Channel Approval vs Fraud Gap Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    print(f"HTML report generated: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
