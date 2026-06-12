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
OUTPUT_HTML = OUTPUT_DIR / "fraud_vs_transactiondate_analysis.html"
MONTHLY_CSV = OUTPUT_DIR / "fraud_vs_transactiondate_monthly_summary.csv"
DAILY_CSV = OUTPUT_DIR / "fraud_vs_transactiondate_daily_summary.csv"

DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
MIN_ROWS_FOR_FULL_MONTH = 1000

PRIMARY = "#4A90D9"
SECONDARY = "#7FB3D3"
ACCENT = "#E8A87C"
ALERT = "#D9534F"
SUCCESS = "#27AE60"
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
        .chart-container, .table-container, .notes-container {
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
        .note {
            padding: 16px 20px;
            color: #4a5568;
            line-height: 1.7;
        }
    </style>
"""


def format_int(value):
    return f"{int(value):,}"


def format_pct(value, decimals=2):
    return f"{float(value):.{decimals}f}%"


def format_timestamp(value):
    if pd.isna(value):
        return "-"
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


def format_month(period):
    return period.to_timestamp().strftime("%b %Y")


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
    headers = ["Transaction Month", "Rows", "Fraud Rows", "Observed Fraud Rate"]
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                row["month_label"],
                format_int(row["rows"]),
                format_int(row["fraud_count"]),
                format_pct(row["fraud_rate_pct"], 3),
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
            <div class="section-title">Full-Month Summary</div>
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

    df = pd.read_csv(DATASET_PATH)
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], errors="coerce")

    df = df.dropna(subset=["TransactionDate", "Fraud"]).copy()
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce").astype(int)
    df["TransactionDay"] = df["TransactionDate"].dt.floor("D")
    df["TransactionMonth"] = df["TransactionDate"].dt.to_period("M")

    monthly_summary = (
        df.groupby("TransactionMonth")
        .agg(rows=("Fraud", "size"), fraud_count=("Fraud", "sum"))
        .reset_index()
    )
    monthly_summary["nonfraud_count"] = monthly_summary["rows"] - monthly_summary["fraud_count"]
    monthly_summary["fraud_rate_pct"] = monthly_summary["fraud_count"] / monthly_summary["rows"] * 100
    monthly_summary["month_label"] = monthly_summary["TransactionMonth"].apply(format_month)

    full_month_summary = monthly_summary.loc[
        monthly_summary["rows"] >= MIN_ROWS_FOR_FULL_MONTH
    ].copy()
    safe_write_csv(full_month_summary, MONTHLY_CSV, "Monthly summary")

    daily_summary = (
        df.groupby("TransactionDay")
        .agg(rows=("Fraud", "size"), fraud_count=("Fraud", "sum"))
        .reset_index()
    )
    daily_summary["fraud_rate_pct"] = daily_summary["fraud_count"] / daily_summary["rows"] * 100
    daily_summary["fraud_rate_7d"] = daily_summary["fraud_rate_pct"].rolling(7, min_periods=1).mean()
    daily_summary["fraud_count_7d"] = daily_summary["fraud_count"].rolling(7, min_periods=1).mean()
    safe_write_csv(daily_summary, DAILY_CSV, "Daily summary")

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "<b>Fraud vs Non-Fraud Rows by Transaction Month</b>",
            "<b>Observed Fraud Rate by Transaction Month</b>",
            "<b>Daily Observed Fraud Rate</b>",
            "<b>Daily Fraud Row Count</b>",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.14,
    )

    fig.add_trace(
        go.Bar(
            x=full_month_summary["month_label"],
            y=full_month_summary["nonfraud_count"],
            name="Non-Fraud (0)",
            marker_color=SECONDARY,
            hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra>Non-Fraud (0)</extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=full_month_summary["month_label"],
            y=full_month_summary["fraud_count"],
            name="Fraud (1)",
            marker_color=PRIMARY,
            hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra>Fraud (1)</extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=full_month_summary["month_label"],
            y=full_month_summary["fraud_rate_pct"],
            marker_color=ACCENT,
            marker_line_color="#C17A4B",
            marker_line_width=1,
            text=[format_pct(value, 3) for value in full_month_summary["fraud_rate_pct"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Observed fraud rate: %{y:.3f}%<extra></extra>",
            name="Observed fraud rate",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=daily_summary["TransactionDay"],
            y=daily_summary["fraud_rate_pct"],
            mode="lines",
            line=dict(color=SECONDARY, width=1.5),
            opacity=0.55,
            name="Daily fraud rate",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Fraud rate:</b> %{y:.3f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=daily_summary["TransactionDay"],
            y=daily_summary["fraud_rate_7d"],
            mode="lines",
            line=dict(color=PRIMARY, width=3),
            name="7-day avg fraud rate",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>7-day avg rate:</b> %{y:.3f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=daily_summary["TransactionDay"],
            y=daily_summary["fraud_count"],
            mode="lines",
            line=dict(color=ACCENT, width=1.5),
            opacity=0.55,
            name="Daily fraud rows",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Fraud rows:</b> %{y:,}<extra></extra>",
        ),
        row=2,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=daily_summary["TransactionDay"],
            y=daily_summary["fraud_count_7d"],
            mode="lines",
            line=dict(color=ALERT, width=3),
            name="7-day avg fraud rows",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>7-day avg fraud rows:</b> %{y:.1f}<extra></extra>",
        ),
        row=2,
        col=2,
    )

    fig.update_layout(barmode="stack")
    apply_layout(fig)

    highest_month = full_month_summary.loc[full_month_summary["fraud_rate_pct"].idxmax()]
    lowest_month = full_month_summary.loc[full_month_summary["fraud_rate_pct"].idxmin()]
    start_month = full_month_summary.iloc[0]
    end_month = full_month_summary.iloc[-1]
    delta_pp = end_month["fraud_rate_pct"] - start_month["fraud_rate_pct"]
    partial_months = monthly_summary.loc[monthly_summary["rows"] < MIN_ROWS_FOR_FULL_MONTH].copy()

    stats = [
        ("Total Rows", format_int(len(df)), False),
        ("Fraud Rows", format_int(df["Fraud"].sum()), False),
        ("Observed Fraud Rate", format_pct(df["Fraud"].mean() * 100, 3), False),
        (
            "Highest Full-Month Rate",
            f"{highest_month['month_label']} ({format_pct(highest_month['fraud_rate_pct'], 3)})",
            True,
        ),
        (
            "Lowest Full-Month Rate",
            f"{lowest_month['month_label']} ({format_pct(lowest_month['fraud_rate_pct'], 3)})",
            True,
        ),
        ("Mar-to-May Change", f"{delta_pp:+.3f} pp", False),
        (
            "Full Months Compared",
            ", ".join(full_month_summary["month_label"].tolist()),
            True,
        ),
    ]

    observations = [
        f"Observed fraud rate declines from {format_pct(start_month['fraud_rate_pct'], 3)} in {start_month['month_label']} to {format_pct(end_month['fraud_rate_pct'], 3)} in {end_month['month_label']}.",
        f"Monthly transaction volume stays in the same broad range, but observed fraud rows fall from {format_int(start_month['fraud_count'])} in {start_month['month_label']} to {format_int(end_month['fraud_count'])} in {end_month['month_label']}.",
        "This pattern is consistent with fraud-label maturation delay: more recent transaction cohorts are likely undercounted on observed fraud.",
    ]
    if not partial_months.empty:
        observations.append(
            "A trailing partial month exists in the raw timestamps and is excluded from the full-month comparison because it does not have enough volume to be analytically useful."
        )

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Note:</strong> Month-level comparisons exclude periods with fewer than {MIN_ROWS_FOR_FULL_MONTH:,} rows."
    )

    html_content = build_page(
        title="Fraud vs TransactionDate Bivariate Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        table_html=render_table(full_month_summary),
        observations_html=render_observations(observations),
    )

    safe_write_text(OUTPUT_HTML, html_content, "HTML report")


if __name__ == "__main__":
    main()
