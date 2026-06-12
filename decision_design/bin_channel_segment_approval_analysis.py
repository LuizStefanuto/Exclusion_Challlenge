from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
NODES_CSV = ROOT_DIR / "bin_channel_segment_approval.csv"
APPROVAL_SUMMARY_CSV = CHALLENGE_DIR / "bivariate_reports" / "segment_vs_approved_summary.csv"
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"
OUTPUT_HTML = ROOT_DIR / "bin_channel_segment_approval_analysis.html"
OLD_NODE_MIN_ROWS = 100

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
            <div class="section-title">Approval Table Charts</div>
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
    nodes = nodes.loc[nodes["rows"] > OLD_NODE_MIN_ROWS].copy()
    baselines = pd.read_csv(APPROVAL_SUMMARY_CSV)
    overall_approval_rate = pd.to_numeric(
        pd.read_csv(DATASET_PATH, usecols=["Approved"])["Approved"],
        errors="coerce",
    ).dropna().mean()

    dominant_segment = (
        nodes[[f"segment_{segment}_weight" for segment in [1, 2, 3, 4]]]
        .idxmax(axis=1)
        .str.extract(r"segment_(\d)_weight")[0]
        .astype(int)
    )
    nodes["dominant_segment"] = dominant_segment

    dominant_counts = (
        nodes["dominant_segment"]
        .value_counts()
        .reindex([1, 2, 3, 4], fill_value=0)
        .reset_index()
    )
    dominant_counts.columns = ["Segment", "NodeCount"]

    nodes["expected_approval_rate"] = nodes["expected_approval_relative"] * overall_approval_rate

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>Approval Relative Gap Distribution</b>",
            "<b>Observed vs Expected Approval Rate</b>",
        ),
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Histogram(
            x=nodes["approval_relative_gap"],
            nbinsx=40,
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            hovertemplate="<b>Approval relative gap:</b> %{x:.3f}<br><b>Nodes:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    axis_min = min(nodes["expected_approval_rate"].min(), nodes["observed_approval_rate"].min()) * 100
    axis_max = max(nodes["expected_approval_rate"].max(), nodes["observed_approval_rate"].max()) * 100

    fig.add_trace(
        go.Scatter(
            x=nodes["expected_approval_rate"] * 100,
            y=nodes["observed_approval_rate"] * 100,
            mode="markers",
            marker=dict(color=PRIMARY, size=6, opacity=0.25),
            customdata=nodes[["UserCardBIN", "Channel", "rows"]].values,
            hovertemplate=(
                "<b>BIN:</b> %{customdata[0]}"
                "<br><b>Channel:</b> %{customdata[1]}"
                "<br><b>Rows:</b> %{customdata[2]:,}"
                "<br><b>Expected approval:</b> %{x:.2f}%"
                "<br><b>Observed approval:</b> %{y:.2f}%"
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
    fig.update_xaxes(title_text="Expected approval rate (%)", row=1, col=2)
    fig.update_yaxes(title_text="Observed approval rate (%)", row=1, col=2)

    below_expected_pct = (nodes["approval_relative_gap"] < 0).mean() * 100
    stats = [
        ("Nodes", format_int(len(nodes))),
        ("Median Rows", format_int(nodes["rows"].median())),
        ("Median Observed Approval", format_pct(nodes["observed_approval_rate"].median() * 100, 2)),
        ("Median Expected Relative", format_float(nodes["expected_approval_relative"].median(), 3)),
        ("Median Approval Index", format_float(nodes["approval_relative_index"].median(), 3)),
        ("Nodes Below Expected", format_pct(below_expected_pct, 2)),
    ]

    context_table = pd.DataFrame(
        [
            (
                "What is a row?",
                "Each row in the approval table is one BIN-Channel node, meaning one card BIN interacting with one routing channel.",
            ),
            (
                "Why approval only?",
                "This table isolates the approval side of performance before bringing fraud into the decision. Approval is the immediate operational outcome returned by the channel.",
            ),
            (
                "Why segment-adjust?",
                "Segments have different baseline approval levels. A node should not be called bad just because it receives tougher segments.",
            ),
            (
                "Why higher-volume nodes only here?",
                f"This report is filtered to nodes with more than {OLD_NODE_MIN_ROWS} rows so the approval comparison is less dominated by sparse-node noise.",
            ),
        ],
        columns=["Context", "Explanation"],
    )

    field_table = pd.DataFrame(
        [
            ("rows", "Total transaction attempts routed through the BIN-Channel node."),
            ("approved_rows", "How many of those attempts were approved by the channel."),
            ("observed_approval_rate", "Approved rows divided by total rows in the node."),
            ("observed_approval_relative", "Observed node approval rate divided by the overall approval rate of the cleaned dataset."),
            ("segment_1_rows ... segment_4_rows", "How many transactions in the node came from each customer segment."),
            ("segment_1_weight ... segment_4_weight", "The node's client mix, expressed as the share of rows coming from each segment."),
            ("segment_1_approval_relative ... segment_4_approval_relative", "The segment approval baselines. For example, a value above 1 means that segment approves better than the overall dataset average."),
            ("segment_1_weighted_approval_relative ... segment_4_weighted_approval_relative", "Each segment baseline multiplied by the node's weight in that segment. These are the segment-level contributions to the node's expected approval."),
            ("expected_approval_relative", "The segment-adjusted approval benchmark for the node. It is the weighted average of the segment approval relatives using the node's own segment mix."),
            ("approval_relative_gap", "Observed approval relative minus expected approval relative. Negative means the node approves worse than expected for its mix; positive means better."),
            ("approval_relative_index", "Observed approval relative divided by expected approval relative. Values below 1 are underperforming; values above 1 are outperforming."),
        ],
        columns=["Field", "How To Read It"],
    )

    formula_table = pd.DataFrame(
        [
            ("observed_approval_rate", "approved_rows / rows"),
            ("observed_approval_relative", "observed_approval_rate / overall_approval_rate"),
            ("expected_approval_relative", "sum(segment_weight_s * segment_approval_relative_s)"),
            ("approval_relative_gap", "observed_approval_relative - expected_approval_relative"),
            ("approval_relative_index", "observed_approval_relative / expected_approval_relative"),
        ],
        columns=["Variable", "Formula"],
    )

    baseline_table = baselines[["Segment", "approval_rate_pct", "approval_rate_index"]].copy()
    baseline_table["approval_rate_pct"] = baseline_table["approval_rate_pct"].map(lambda value: format_pct(value, 3))
    baseline_table["approval_rate_index"] = baseline_table["approval_rate_index"].map(lambda value: format_float(value, 3))
    baseline_table = baseline_table.rename(
        columns={
            "Segment": "Segment",
            "approval_rate_pct": "Approval Rate",
            "approval_rate_index": "Approval Relative",
        }
    )

    observations = [
        "This report explains the approval-side node table used in decision design. The key question is whether a BIN-Channel node approves better or worse than would be expected from the type of customers routed into it.",
        "Expected approval is not a raw average. It is a segment-adjusted benchmark built from the node's own segment mix and the approval baseline of each segment.",
        f"The median higher-volume node has {format_int(nodes['rows'].median())} rows, which gives a more stable read than the full-node universe.",
        f"{format_pct(below_expected_pct, 2)} of higher-volume nodes sit below their segment-adjusted approval expectation.",
        "When reading the histogram, values below zero are nodes approving worse than expected for their segment mix. Values above zero are nodes approving better than expected.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> Explanation of the approval-side BIN-Channel node table for higher-volume nodes with more than {OLD_NODE_MIN_ROWS} rows, showing how observed approval is compared with a segment-adjusted approval benchmark."
    )

    html_content = build_page(
        title="BIN-Channel Segment Approval Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        tables_html=(
            render_table("Context", context_table)
            + render_table("How to Read the Approval Table", field_table)
            + render_table("Main Formulas", formula_table)
            + render_table("Segment Approval Baselines", baseline_table)
        ),
        observations_html=render_observations(observations),
    )
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    print(f"HTML report generated: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
