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
OUTPUT_HTML = OUTPUT_DIR / "fraud_detection_delay_analysis.html"
THRESHOLD_CSV = OUTPUT_DIR / "fraud_detection_delay_threshold_summary.csv"

DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
THRESHOLDS_DAYS = [1, 3, 7, 14, 21, 30, 45, 60, 90]

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


def format_days(value, decimals=2):
    return f"{float(value):.{decimals}f} days"


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


def build_threshold_summary(delay_series):
    rows = []
    for threshold in THRESHOLDS_DAYS:
        rows.append(
            {
                "threshold_days": threshold,
                "share_detected_pct": float((delay_series <= threshold).mean() * 100),
            }
        )
    return pd.DataFrame(rows)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET_PATH, usecols=["Fraud", "TransactionDate", "FraudDetectionDate"])
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce")
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], errors="coerce")
    df["FraudDetectionDate"] = pd.to_datetime(df["FraudDetectionDate"], errors="coerce")

    fraud_df = df.loc[df["Fraud"].eq(1)].copy()
    fraud_df = fraud_df.dropna(subset=["TransactionDate"]).copy()

    delay_df = fraud_df.dropna(subset=["FraudDetectionDate"]).copy()
    delay_df["delay_days"] = (
        delay_df["FraudDetectionDate"] - delay_df["TransactionDate"]
    ).dt.total_seconds() / 86400
    delay_df = delay_df.loc[delay_df["delay_days"] >= 0].copy()

    threshold_summary = build_threshold_summary(delay_df["delay_days"])
    safe_write_csv(threshold_summary, THRESHOLD_CSV, "Threshold summary")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>Observed Delay Distribution</b>",
            "<b>Cumulative Share Detected Within X Days</b>",
        ),
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Histogram(
            x=delay_df["delay_days"],
            nbinsx=40,
            marker_color=PRIMARY,
            opacity=0.85,
            name="Delay distribution",
            hovertemplate="<b>Delay:</b> %{x:.1f} days<br><b>Rows:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=threshold_summary["threshold_days"],
            y=threshold_summary["share_detected_pct"],
            mode="lines+markers+text",
            line=dict(color=ACCENT, width=3),
            marker=dict(size=8),
            text=[format_pct(value, 1) for value in threshold_summary["share_detected_pct"]],
            textposition="top center",
            name="Detected within threshold",
            hovertemplate="<b>Threshold:</b> %{x} days<br><b>Share:</b> %{y:.2f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_layout(height=520)
    fig.update_xaxes(title_text="Delay (days)", row=1, col=1)
    fig.update_yaxes(title_text="Rows", row=1, col=1)
    fig.update_xaxes(title_text="Threshold (days)", row=1, col=2)
    fig.update_yaxes(title_text="Share of detected fraud rows (%)", row=1, col=2)

    detection_coverage_pct = len(delay_df) / len(fraud_df) * 100
    median_delay = delay_df["delay_days"].median()
    mean_delay = delay_df["delay_days"].mean()
    p90_delay = delay_df["delay_days"].quantile(0.9)
    within_7_days = threshold_summary.loc[
        threshold_summary["threshold_days"] == 7, "share_detected_pct"
    ].iloc[0]
    within_30_days = threshold_summary.loc[
        threshold_summary["threshold_days"] == 30, "share_detected_pct"
    ].iloc[0]

    stats = [
        ("Fraud Rows", format_int(len(fraud_df)), False),
        ("Rows with Both Dates", format_int(len(delay_df)), False),
        ("Detection Timestamp Coverage", format_pct(detection_coverage_pct, 2), False),
        ("Mean Delay", format_days(mean_delay, 2), False),
        ("Median Delay", format_days(median_delay, 2), False),
        ("P90 Delay", format_days(p90_delay, 2), False),
        ("Within 7 Days", format_pct(within_7_days, 1), False),
        ("Within 30 Days", format_pct(within_30_days, 1), False),
    ]

    observations = [
        f"The observed median delay is {format_days(median_delay, 2)}, and the observed P90 delay is {format_days(p90_delay, 2)}.",
        f"Only {format_pct(detection_coverage_pct, 2)} of fraud-tagged rows currently have a populated detection timestamp, so delay analysis is based on a partial subset.",
        f"{format_pct(within_7_days, 1)} of detected fraud rows enter the system within 7 days, while {format_pct(within_30_days, 1)} appear within 30 days.",
        "The delay pattern has a long tail, so a meaningful share of fraud dates enters the system several weeks after the original transaction.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        "<strong>Scope:</strong> Fraud-tagged rows with both TransactionDate and FraudDetectionDate populated."
    )

    html_content = build_page(
        title="FraudDetectionDate vs TransactionDate Delay Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        table_html="",
        observations_html=render_observations(observations),
    )

    safe_write_text(OUTPUT_HTML, html_content, "HTML report")


if __name__ == "__main__":
    main()
