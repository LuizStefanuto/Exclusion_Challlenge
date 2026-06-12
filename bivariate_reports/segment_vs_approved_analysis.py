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
OUTPUT_HTML = OUTPUT_DIR / "segment_vs_approved_analysis.html"
SUMMARY_CSV = OUTPUT_DIR / "segment_vs_approved_summary.csv"

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
        "Approved Rows",
        "Approved Share",
        "Approval Rate",
        "Approval Rate vs Overall",
    ]
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                format_int(row["Segment"]),
                format_int(row["rows"]),
                format_pct(row["share_pct"], 2),
                format_int(row["approved_count"]),
                format_pct(row["approved_share_pct"], 2),
                format_pct(row["approval_rate_pct"], 3),
                format_ratio(row["approval_rate_index"], 2),
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
            <div class="section-title">Segment Approval Summary</div>
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

    df = pd.read_csv(DATASET_PATH, usecols=["Segment", "Approved"])
    df = df.dropna(subset=["Segment", "Approved"]).copy()
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce")
    df["Approved"] = pd.to_numeric(df["Approved"], errors="coerce")
    df = df.dropna(subset=["Segment", "Approved"]).copy()
    df["Segment"] = df["Segment"].astype(int)
    df["Approved"] = df["Approved"].astype(int)

    overall_approval_rate_pct = df["Approved"].mean() * 100

    summary = (
        df.groupby("Segment")
        .agg(rows=("Approved", "size"), approved_count=("Approved", "sum"))
        .reset_index()
        .sort_values("Segment")
    )
    summary["declined_count"] = summary["rows"] - summary["approved_count"]
    summary["share_pct"] = summary["rows"] / len(df) * 100
    summary["approved_share_pct"] = summary["approved_count"] / summary["approved_count"].sum() * 100
    summary["approval_rate_pct"] = summary["approved_count"] / summary["rows"] * 100
    summary["approval_rate_index"] = summary["approval_rate_pct"] / overall_approval_rate_pct

    safe_write_csv(summary, SUMMARY_CSV, "Segment approval summary")

    segment_labels = [f"Segment {segment}" for segment in summary["Segment"]]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>Observed Approval Rate by Segment</b>",
            "<b>Approval Rate Relative to Overall</b>",
        ),
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Bar(
            x=segment_labels,
            y=summary["approval_rate_pct"],
            marker_color=ACCENT,
            text=[format_pct(value, 3) for value in summary["approval_rate_pct"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br><b>Approval rate:</b> %{y:.3f}%<extra></extra>",
            name="Approval rate",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=segment_labels,
            y=summary["approval_rate_index"],
            marker_color=PRIMARY,
            text=[format_ratio(value, 2) for value in summary["approval_rate_index"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br><b>Approval rate vs overall:</b> %{y:.2f}x<extra></extra>",
            name="Approval rate vs overall",
        ),
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_layout(height=520)
    fig.update_xaxes(title_text="Segment", row=1, col=1)
    fig.update_yaxes(title_text="Observed approval rate (%)", row=1, col=1)
    fig.update_xaxes(title_text="Segment", row=1, col=2)
    fig.update_yaxes(title_text="Multiple of overall approval rate", row=1, col=2)

    highest_segment = summary.loc[summary["approval_rate_pct"].idxmax()]
    lowest_segment = summary.loc[summary["approval_rate_pct"].idxmin()]
    segment_1 = summary.loc[summary["Segment"] == 1].iloc[0]
    segment_4 = summary.loc[summary["Segment"] == 4].iloc[0]
    segment_1_vs_4 = segment_1["approval_rate_pct"] / segment_4["approval_rate_pct"]

    stats = [
        ("Rows Analyzed", format_int(len(df)), False),
        ("Approved Rows", format_int(df["Approved"].sum()), False),
        ("Overall Approval Rate", format_pct(overall_approval_rate_pct, 3), False),
        (
            "Highest Approval Segment",
            f"Segment {int(highest_segment['Segment'])} ({format_pct(highest_segment['approval_rate_pct'], 3)})",
            True,
        ),
        (
            "Lowest Approval Segment",
            f"Segment {int(lowest_segment['Segment'])} ({format_pct(lowest_segment['approval_rate_pct'], 3)})",
            True,
        ),
        ("Segment 1 vs Segment 4", format_ratio(segment_1_vs_4, 2), False),
    ]

    observations = [
        f"Observed approval rate declines steadily from {format_pct(segment_1['approval_rate_pct'], 3)} in Segment 1 to {format_pct(segment_4['approval_rate_pct'], 3)} in Segment 4.",
        f"Segment 1's observed approval rate is {format_ratio(segment_1_vs_4, 2)} Segment 4's rate.",
        "This confirms that client segmentation is also a material driver of approval outcomes.",
        "Raw BIN-Channel approval comparisons will be influenced by segment mix, so later pair-level work should control for it.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        "<strong>Scope:</strong> Raw observed approval by client segment in the cleaned dataset."
    )

    html_content = build_page(
        title="Segment vs Approved Bivariate Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        table_html=render_table(summary),
        observations_html=render_observations(observations),
    )

    safe_write_text(OUTPUT_HTML, html_content, "HTML report")


if __name__ == "__main__":
    main()
