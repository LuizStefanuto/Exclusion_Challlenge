import argparse
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
NODES_CSV = ROOT_DIR / "bin_channel_segment_approval.csv"
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"
DEFAULT_OUTPUT_HTML = ROOT_DIR / "approval_expectation_visualization.html"

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
        .stat-card.small .stat-value {
            font-size: 1.05em;
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
            font-size: 1.4em;
            font-weight: 600;
            line-height: 1.25;
            word-break: break-word;
        }
        .chart-container {
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
            background: white;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin: 20px 0;
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
    for label, value, small in cards:
        parts.append(
            f"""
            <div class="stat-card{' small' if small else ''}">
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
        <ul>
            {rows}
        </ul>
    </div>
    """


def safe_write_text(path, content):
    path.write_text(content, encoding="utf-8")


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
            <div class="section-title">Decision Design Charts</div>
        </div>
        {figure_html}
    </div>
    {observations_html}
</body>
</html>"""


def apply_layout(fig):
    fig.update_layout(
        showlegend=False,
        height=620,
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize observed vs expected approval for BIN-Channel nodes."
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=0,
        help="Minimum node row count to include in the report.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    nodes = pd.read_csv(NODES_CSV)
    min_rows = max(args.min_rows, 0)
    if min_rows > 0:
        nodes = nodes.loc[nodes["rows"] >= min_rows].copy()

    if nodes.empty:
        raise ValueError(f"No nodes remain after applying min_rows >= {min_rows}.")

    approval_series = pd.read_csv(DATASET_PATH, usecols=["Approved"])["Approved"]
    approval_series = pd.to_numeric(approval_series, errors="coerce").dropna()
    overall_approval_rate = approval_series.mean()

    output_html = (
        ROOT_DIR / f"approval_expectation_visualization_min_{min_rows}_rows.html"
        if min_rows > 0
        else DEFAULT_OUTPUT_HTML
    )

    nodes["expected_approval_rate"] = overall_approval_rate * nodes["expected_approval_relative"]
    nodes["approval_rate_gap_pp"] = (
        nodes["observed_approval_rate"] - nodes["expected_approval_rate"]
    ) * 100
    nodes["observed_approval_rate_pct"] = nodes["observed_approval_rate"] * 100
    nodes["expected_approval_rate_pct"] = nodes["expected_approval_rate"] * 100

    axis_min = min(
        nodes["expected_approval_rate_pct"].min(),
        nodes["observed_approval_rate_pct"].min(),
    )
    axis_max = max(
        nodes["expected_approval_rate_pct"].max(),
        nodes["observed_approval_rate_pct"].max(),
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>Observed vs Expected Approval Rate</b>",
            "<b>Approval Gap Distribution</b>",
        ),
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Scatter(
            x=nodes["expected_approval_rate_pct"],
            y=nodes["observed_approval_rate_pct"],
            mode="markers",
            marker=dict(color=PRIMARY, size=6, opacity=0.25),
            customdata=nodes[["UserCardBIN", "Channel", "rows"]].values,
            hovertemplate=(
                "<b>BIN:</b> %{customdata[0]}"
                "<br><b>Channel:</b> %{customdata[1]}"
                "<br><b>Rows:</b> %{customdata[2]:,}"
                "<br><b>Expected:</b> %{x:.2f}%"
                "<br><b>Observed:</b> %{y:.2f}%"
                "<extra></extra>"
            ),
        ),
        row=1,
        col=1,
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
        col=1,
    )

    fig.add_trace(
        go.Histogram(
            x=nodes["approval_rate_gap_pp"],
            nbinsx=50,
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            hovertemplate="<b>Approval gap:</b> %{x:.2f} pp<br><b>Nodes:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_xaxes(title_text="Expected approval rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="Observed approval rate (%)", row=1, col=1)
    fig.update_xaxes(title_text="Observed minus expected approval (pp)", row=1, col=2)
    fig.update_yaxes(title_text="Number of nodes", row=1, col=2)

    below_expected_pct = (nodes["approval_rate_gap_pp"] < 0).mean() * 100
    median_gap = nodes["approval_rate_gap_pp"].median()
    mean_gap = nodes["approval_rate_gap_pp"].mean()

    stats = [
        ("Nodes", format_int(len(nodes)), False),
        ("Min Rows Filter", format_int(min_rows), False),
        ("Overall Approval Rate", format_pct(overall_approval_rate * 100, 2), False),
        ("Median Expected Rate", format_pct(nodes["expected_approval_rate_pct"].median(), 2), False),
        ("Median Observed Rate", format_pct(nodes["observed_approval_rate_pct"].median(), 2), False),
        ("Median Gap", f"{median_gap:.2f} pp", False),
        ("Nodes Below Expected", format_pct(below_expected_pct, 2), False),
    ]

    observations = [
        "The scatter uses the diagonal reference line to separate nodes that approve better than expected from nodes that approve worse than expected.",
        f"The median approval gap is {median_gap:.2f} percentage points, and {format_pct(below_expected_pct, 2)} of nodes sit below expectation.",
        f"The mean approval gap is {mean_gap:.2f} percentage points, but this distribution is heavily influenced by sparse nodes with extreme observed rates.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> Observed approval vs segment-adjusted expected approval for each BIN-Channel node"
        f"{' with at least ' + format_int(min_rows) + ' rows' if min_rows > 0 else ''}."
    )

    html_content = build_page(
        title="Approval Expectation Visualization",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )
    safe_write_text(output_html, html_content)

    print(f"Nodes used: {len(nodes):,}")
    print(f"HTML report generated: {output_html}")


if __name__ == "__main__":
    main()
