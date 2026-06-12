from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"
OUTPUT_DIR = ROOT_DIR
OUTPUT_HTML = OUTPUT_DIR / "segment_vs_fraud_analysis.html"
SUMMARY_CSV = OUTPUT_DIR / "segment_vs_fraud_summary.csv"

DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"

PRIMARY = "#4A90D9"
ACCENT = "#E8A87C"
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
        .chart-container, .table-container {
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
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px 14px;
            border-bottom: 1px solid #edf2f7;
            text-align: left;
            font-size: 0.95em;
        }
        th {
            background: #f8fafc;
            color: #475569;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            font-size: 0.8em;
        }
    </style>
"""


def format_int(value):
    return f"{int(value):,}"


def format_pct(value, decimals=2):
    return f"{float(value):.{decimals}f}%"


def format_ratio(value, decimals=2):
    return f"{float(value):.{decimals}f}x"


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


def render_table(df):
    headers = [
        "Segment",
        "Rows",
        "Volume Share",
        "Fraud Rows",
        "Fraud Share",
        "Fraud Rate",
        "Fraud Rate vs Overall",
    ]
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                format_int(row["Segment"]),
                format_int(row["rows"]),
                format_pct(row["share_pct"], 2),
                format_int(row["fraud_count"]),
                format_pct(row["fraud_share_pct"], 2),
                format_pct(row["fraud_rate_pct"], 3),
                format_ratio(row["fraud_rate_index"], 2),
            ]
        )

    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>"
        for row in rows
    )

    return f"""
    <div class="table-container">
        <div class="section-header">
            <div class="section-title">Segment Fraud Summary</div>
        </div>
        <table>
            <thead>
                <tr>{header_html}</tr>
            </thead>
            <tbody>
                {body_html}
            </tbody>
        </table>
    </div>
    """


def safe_write_csv(df, path, label):
    try:
        df.to_csv(path, index=False)
        print(f"{label} generated: {path}")
    except PermissionError:
        print(f"Warning: could not write {path.name} because the file is open in another program.")


def safe_write_text(path, content, label):
    try:
        path.write_text(content, encoding="utf-8")
        print(f"{label} generated: {path}")
    except PermissionError:
        print(f"Warning: could not write {path.name} because the file is open in another program.")


def build_page(title, subtitle, stats_html, figure_html, table_html, observations_html):
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
            <div class="section-title">Bivariate Charts</div>
        </div>
        {figure_html}
    </div>
    {table_html}
    {observations_html}
</body>
</html>"""


def apply_layout(fig):
    fig.update_layout(
        showlegend=True,
        height=860,
        title_text="",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=60, r=30, t=40, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET_PATH, usecols=["Segment", "Fraud"])
    df = df.dropna(subset=["Segment", "Fraud"]).copy()
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce")
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce")
    df = df.dropna(subset=["Segment", "Fraud"]).copy()
    df["Segment"] = df["Segment"].astype(int)
    df["Fraud"] = df["Fraud"].astype(int)

    overall_fraud_rate_pct = df["Fraud"].mean() * 100

    summary = (
        df.groupby("Segment")
        .agg(rows=("Fraud", "size"), fraud_count=("Fraud", "sum"))
        .reset_index()
        .sort_values("Segment")
    )
    summary["share_pct"] = summary["rows"] / len(df) * 100
    summary["fraud_share_pct"] = summary["fraud_count"] / summary["fraud_count"].sum() * 100
    summary["fraud_rate_pct"] = summary["fraud_count"] / summary["rows"] * 100
    summary["fraud_rate_index"] = summary["fraud_rate_pct"] / overall_fraud_rate_pct

    safe_write_csv(summary, SUMMARY_CSV, "Segment fraud summary")

    segment_labels = [f"Segment {segment}" for segment in summary["Segment"]]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>Observed Fraud Rate by Segment</b>",
            "<b>Fraud Rate Relative to Overall</b>",
        ),
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Bar(
            x=segment_labels,
            y=summary["fraud_rate_pct"],
            marker_color=ACCENT,
            text=[format_pct(value, 3) for value in summary["fraud_rate_pct"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br><b>Fraud rate:</b> %{y:.3f}%<extra></extra>",
            name="Fraud rate",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=segment_labels,
            y=summary["fraud_rate_index"],
            marker_color=PRIMARY,
            text=[format_ratio(value, 2) for value in summary["fraud_rate_index"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br><b>Fraud rate vs overall:</b> %{y:.2f}x<extra></extra>",
            name="Fraud rate vs overall",
        ),
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_layout(height=520)
    fig.update_xaxes(title_text="Segment", row=1, col=1)
    fig.update_yaxes(title_text="Observed fraud rate (%)", row=1, col=1)
    fig.update_xaxes(title_text="Segment", row=1, col=2)
    fig.update_yaxes(title_text="Multiple of overall fraud rate", row=1, col=2)

    highest_segment = summary.loc[summary["fraud_rate_pct"].idxmax()]
    lowest_segment = summary.loc[summary["fraud_rate_pct"].idxmin()]
    segment_1 = summary.loc[summary["Segment"] == 1].iloc[0]
    segment_4 = summary.loc[summary["Segment"] == 4].iloc[0]
    segment_4_vs_1 = segment_4["fraud_rate_pct"] / segment_1["fraud_rate_pct"]

    stats = [
        ("Rows Analyzed", format_int(len(df)), False),
        ("Fraud Rows", format_int(df["Fraud"].sum()), False),
        ("Overall Fraud Rate", format_pct(overall_fraud_rate_pct, 3), False),
        (
            "Highest Fraud Segment",
            f"Segment {int(highest_segment['Segment'])} ({format_pct(highest_segment['fraud_rate_pct'], 3)})",
            True,
        ),
        (
            "Lowest Fraud Segment",
            f"Segment {int(lowest_segment['Segment'])} ({format_pct(lowest_segment['fraud_rate_pct'], 3)})",
            True,
        ),
        ("Segment 4 vs Segment 1", format_ratio(segment_4_vs_1, 2), False),
    ]

    observations = [
        f"Observed fraud rate rises steadily from {format_pct(segment_1['fraud_rate_pct'], 3)} in Segment 1 to {format_pct(segment_4['fraud_rate_pct'], 3)} in Segment 4.",
        f"Segment 4's observed fraud rate is {format_ratio(segment_4_vs_1, 2)} Segment 1's rate.",
        "This confirms that client segmentation is also a material driver of fraud outcomes.",
        "These are full-dataset observed fraud rates, so later versions can add maturity filters for a cleaner segment comparison.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        "<strong>Scope:</strong> Raw observed fraud by client segment in the cleaned dataset."
    )

    html_content = build_page(
        title="Segment vs Fraud Bivariate Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        table_html=render_table(summary),
        observations_html=render_observations(observations),
    )

    safe_write_text(OUTPUT_HTML, html_content, "HTML report")


if __name__ == "__main__":
    main()
