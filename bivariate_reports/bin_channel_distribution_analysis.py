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
OUTPUT_HTML = OUTPUT_DIR / "bin_channel_distribution_analysis.html"
SUMMARY_CSV = OUTPUT_DIR / "bin_channel_pair_summary.csv"

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
            <div class="section-title">Bivariate Charts</div>
        </div>
        {figure_html}
    </div>
    {observations_html}
</body>
</html>"""


def apply_layout(fig):
    fig.update_layout(
        showlegend=False,
        height=940,
        title_text="",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=70, r=30, t=40, b=50),
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

    df = pd.read_csv(DATASET_PATH, usecols=["UserCardBIN", "Channel"])
    df = df.dropna(subset=["UserCardBIN", "Channel"]).copy()
    df["UserCardBIN"] = df["UserCardBIN"].astype(str)
    df["Channel"] = df["Channel"].astype(str)

    pair_summary = (
        df.groupby(["UserCardBIN", "Channel"])
        .size()
        .reset_index(name="rows")
        .sort_values("rows", ascending=False)
        .reset_index(drop=True)
    )
    pair_summary["rank"] = pair_summary.index + 1
    pair_summary["pair_label"] = pair_summary["UserCardBIN"] + " | " + pair_summary["Channel"]
    pair_summary["share_pct"] = pair_summary["rows"] / len(df) * 100
    pair_summary["cumulative_share_pct"] = pair_summary["share_pct"].cumsum()

    safe_write_csv(pair_summary, SUMMARY_CSV, "Pair summary")

    top_pairs_chart = pair_summary.head(20).iloc[::-1].copy()

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "<b>Top 20 BIN-Channel Pairs by Rows</b>",
            "<b>Rows per Pair Boxplot</b>",
            "<b>Cumulative Share by Ranked Pair</b>",
            "<b>Rows by Ranked Pair</b>",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.14,
    )

    fig.add_trace(
        go.Bar(
            x=top_pairs_chart["rows"],
            y=top_pairs_chart["pair_label"],
            orientation="h",
            marker_color=PRIMARY,
            text=[format_int(value) for value in top_pairs_chart["rows"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br><b>Rows:</b> %{x:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Box(
            y=pair_summary["rows"],
            marker_color=SECONDARY,
            boxpoints=False,
            hovertemplate="<b>Rows:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=pair_summary["rank"],
            y=pair_summary["cumulative_share_pct"],
            mode="lines",
            line=dict(color=ACCENT, width=3),
            hovertemplate="<b>Rank:</b> %{x:,}<br><b>Cumulative share:</b> %{y:.2f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=pair_summary["rank"],
            y=pair_summary["rows"],
            mode="lines",
            line=dict(color=ALERT, width=2),
            hovertemplate="<b>Rank:</b> %{x:,}<br><b>Rows:</b> %{y:,}<extra></extra>",
        ),
        row=2,
        col=2,
    )

    apply_layout(fig)
    fig.update_xaxes(title_text="Rows", row=1, col=1)
    fig.update_yaxes(title_text="BIN | Channel", row=1, col=1)
    fig.update_xaxes(title_text="", showticklabels=False, row=1, col=2)
    fig.update_yaxes(title_text="Rows per pair", type="log", row=1, col=2)
    fig.update_xaxes(title_text="Pair Rank", row=2, col=1)
    fig.update_yaxes(title_text="Cumulative share of rows (%)", row=2, col=1)
    fig.update_xaxes(title_text="Pair Rank", row=2, col=2)
    fig.update_yaxes(title_text="Rows", type="log", row=2, col=2)

    top_pair = pair_summary.iloc[0]
    top10_share = pair_summary.head(10)["share_pct"].sum()
    top100_share = pair_summary.head(100)["share_pct"].sum()
    median_rows = pair_summary["rows"].median()
    singletons = int(pair_summary["rows"].eq(1).sum())
    pairs_le_10 = int(pair_summary["rows"].le(10).sum())
    pairs_le_10_pct = pairs_le_10 / len(pair_summary) * 100

    stats = [
        ("Rows Analyzed", format_int(len(df)), False),
        ("Distinct BIN-Channel Pairs", format_int(len(pair_summary)), False),
        ("Top Pair", top_pair["pair_label"], True),
        ("Top Pair Share", format_pct(top_pair["share_pct"], 2), False),
        ("Top 10 Share", format_pct(top10_share, 2), False),
        ("Top 100 Share", format_pct(top100_share, 2), False),
        ("Median Rows / Pair", format_int(median_rows), False),
        ("Singleton Pairs", format_int(singletons), False),
    ]

    observations = [
        f"There are {format_int(len(pair_summary))} observed BIN-Channel pairs across {format_int(len(df))} transactions.",
        f"The top pair is {top_pair['pair_label']} with {format_int(top_pair['rows'])} rows, representing {format_pct(top_pair['share_pct'], 2)} of the dataset.",
        f"The distribution is very long-tailed: {format_int(singletons)} pairs occur only once, and {format_int(pairs_le_10)} pairs ({format_pct(pairs_le_10_pct, 2)}) have 10 rows or fewer.",
        f"The head still matters operationally: the top 10 pairs account for {format_pct(top10_share, 2)} of all rows, and the top 100 pairs account for {format_pct(top100_share, 2)}.",
        "This suggests later fraud and approval comparisons should use volume filters, because many BIN-Channel pairs have very little data.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        "<strong>Scope:</strong> Distribution of observed BIN-Channel combinations in the cleaned dataset."
    )

    html_content = build_page(
        title="BIN-Channel Distribution Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )

    safe_write_text(OUTPUT_HTML, html_content, "HTML report")


if __name__ == "__main__":
    main()
