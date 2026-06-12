from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
NODES_CSV = ROOT_DIR / "bin_channel_segment_fraud.csv"
OUTPUT_HTML = ROOT_DIR / "bin_channel_segment_fraud_analysis.html"
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
            <div class="section-title">Fraud Table Charts</div>
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
        height=520,
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


def main():
    nodes = pd.read_csv(NODES_CSV)
    nodes = nodes.loc[nodes["rows"] > HIGH_VOLUME_MIN_ROWS].copy()

    if nodes.empty:
        raise ValueError(f"No nodes remain after filtering rows > {HIGH_VOLUME_MIN_ROWS}.")

    nodes["expected_fraud_rate"] = (
        nodes["overall_fraud_rate_45d"] * nodes["expected_fraud_relative"]
    )
    nodes["observed_fraud_rate_pct"] = nodes["observed_fraud_rate"] * 100
    nodes["expected_fraud_rate_pct"] = nodes["expected_fraud_rate"] * 100

    axis_min = min(
        nodes["expected_fraud_rate_pct"].min(),
        nodes["observed_fraud_rate_pct"].min(),
    )
    axis_max = max(
        nodes["expected_fraud_rate_pct"].max(),
        nodes["observed_fraud_rate_pct"].max(),
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>Fraud Relative Gap Distribution</b>",
            "<b>Observed vs Expected Fraud Rate</b>",
        ),
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Histogram(
            x=nodes["fraud_relative_gap"],
            nbinsx=40,
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            hovertemplate="<b>Fraud relative gap:</b> %{x:.3f}<br><b>Nodes:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=nodes["expected_fraud_rate_pct"],
            y=nodes["observed_fraud_rate_pct"],
            mode="markers",
            marker=dict(color=PRIMARY, size=6, opacity=0.25),
            customdata=nodes[["UserCardBIN", "Channel", "rows"]].values,
            hovertemplate=(
                "<b>BIN:</b> %{customdata[0]}"
                "<br><b>Channel:</b> %{customdata[1]}"
                "<br><b>Rows:</b> %{customdata[2]:,}"
                "<br><b>Expected fraud:</b> %{x:.3f}%"
                "<br><b>Observed fraud:</b> %{y:.3f}%"
                "<extra></extra>"
            ),
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=[axis_min, axis_max],
            y=[axis_min, axis_max],
            mode="lines",
            line=dict(color=ALERT, width=2, dash="dash"),
            hoverinfo="skip",
        ),
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_xaxes(title_text="Observed relative minus expected relative", row=1, col=1)
    fig.update_yaxes(title_text="Number of nodes", row=1, col=1)
    fig.update_xaxes(title_text="Expected fraud rate (%)", row=1, col=2)
    fig.update_yaxes(title_text="Observed fraud rate (%)", row=1, col=2)

    above_expected_pct = (nodes["fraud_relative_gap"] > 0).mean() * 100
    stats = [
        ("Nodes", format_int(len(nodes))),
        ("Median Rows", format_int(nodes["rows"].median())),
        ("45-Day Overall Fraud", format_pct(nodes["overall_fraud_rate_45d"].iloc[0] * 100, 3)),
        ("Median Expected Relative", format_float(nodes["expected_fraud_relative"].median(), 3)),
        ("Median Fraud Index", format_float(nodes["fraud_relative_index"].median(), 3)),
        ("Nodes Above Expected Fraud", format_pct(above_expected_pct, 2)),
    ]

    context_table = pd.DataFrame(
        [
            (
                "What is a row?",
                "Each row in the fraud table is one BIN-Channel node, meaning one card BIN interacting with one routing channel.",
            ),
            (
                "Why a separate fraud table?",
                "Fraud is evaluated on a different benchmark from approval, so it needs its own node-level view and its own expected-performance fields.",
            ),
            (
                "How is maturity handled here?",
                "In this first version, maturity is handled in the benchmark only. The overall fraud rate and the segment fraud relatives come from the 45-day cutoff in the fraud maturity analysis.",
            ),
            (
                "What is not maturity-adjusted yet?",
                "The node's own observed fraud rate and its segment weights still come from the current full node, not from a node-specific mature subset.",
            ),
        ],
        columns=["Context", "Explanation"],
    )

    field_table = pd.DataFrame(
        [
            ("rows", "Total transaction attempts in the BIN-Channel node."),
            ("fraud_rows", "How many of those rows are currently tagged as fraud."),
            ("observed_fraud_rate", "Fraud rows divided by total rows in the node."),
            ("overall_fraud_rate_45d", "The overall fraud rate from the 45-day maturity cutoff."),
            ("observed_fraud_relative", "Observed node fraud rate divided by the 45-day overall fraud rate."),
            ("segment_1_rows ... segment_4_rows", "How many transactions in the node came from each segment."),
            ("segment_1_weight ... segment_4_weight", "The node's segment mix, expressed as the share of rows coming from each segment."),
            ("segment_1_fraud_relative ... segment_4_fraud_relative", "The segment fraud baselines taken from the 45-day maturity cutoff."),
            ("segment_1_weighted_fraud_relative ... segment_4_weighted_fraud_relative", "Each segment fraud baseline multiplied by the node's segment weight."),
            ("expected_fraud_relative", "The segment-adjusted fraud benchmark for the node, using the 45-day fraud baselines."),
            ("fraud_relative_gap", "Observed fraud relative minus expected fraud relative. Positive means more fraud than expected; negative means less."),
            ("fraud_relative_index", "Observed fraud relative divided by expected fraud relative. Values above 1 are worse than expected."),
        ],
        columns=["Field", "How To Read It"],
    )

    formula_table = pd.DataFrame(
        [
            ("observed_fraud_rate", "fraud_rows / rows"),
            ("observed_fraud_relative", "observed_fraud_rate / overall_fraud_rate_45d"),
            ("expected_fraud_relative", "sum(segment_weight_s * segment_fraud_relative_s)"),
            ("fraud_relative_gap", "observed_fraud_relative - expected_fraud_relative"),
            ("fraud_relative_index", "observed_fraud_relative / expected_fraud_relative"),
        ],
        columns=["Variable", "Formula"],
    )

    baseline_table = pd.DataFrame(
        [
            ("Overall", format_pct(nodes["overall_fraud_rate_45d"].iloc[0] * 100, 3), "1.000"),
            ("Segment 1", "-", format_float(nodes["segment_1_fraud_relative"].iloc[0], 3)),
            ("Segment 2", "-", format_float(nodes["segment_2_fraud_relative"].iloc[0], 3)),
            ("Segment 3", "-", format_float(nodes["segment_3_fraud_relative"].iloc[0], 3)),
            ("Segment 4", "-", format_float(nodes["segment_4_fraud_relative"].iloc[0], 3)),
        ],
        columns=["Baseline", "Fraud Rate", "Fraud Relative"],
    )

    observations = [
        "This report explains the fraud-side node table used in decision design. The key question is whether a BIN-Channel node shows more or less fraud than would be expected from its segment mix.",
        "In this first version, the maturity adjustment is in the benchmark, not yet in the node weights or the node's observed fraud numerator/denominator.",
        f"The report is filtered to high-volume nodes only, meaning nodes with more than {HIGH_VOLUME_MIN_ROWS} rows.",
        f"{format_pct(above_expected_pct, 2)} of high-volume nodes sit above their current segment-adjusted fraud expectation.",
        "When reading the histogram, values above zero are nodes with more observed fraud than expected, which is the bad side of the distribution.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> Explanation of the fraud-side BIN-Channel node table for high-volume nodes with more than {HIGH_VOLUME_MIN_ROWS} rows, using the 45-day fraud maturity baselines."
    )

    html_content = build_page(
        title="BIN-Channel Segment Fraud Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        tables_html=(
            render_table("Context", context_table)
            + render_table("How to Read the Fraud Table", field_table)
            + render_table("Main Formulas", formula_table)
            + render_table("45-Day Fraud Baselines", baseline_table)
        ),
        observations_html=render_observations(observations),
    )
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    print(f"HTML report generated: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
