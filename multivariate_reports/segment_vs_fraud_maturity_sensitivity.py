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
OUTPUT_HTML = OUTPUT_DIR / "segment_vs_fraud_maturity_sensitivity.html"
SUMMARY_CSV = OUTPUT_DIR / "segment_vs_fraud_maturity_sensitivity.csv"

DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
MAX_CUTOFF_DAYS = 60
SEGMENT_COLORS = {
    1: "#4A90D9",
    2: "#E8A87C",
    3: "#D9534F",
    4: "#27AE60",
}
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
        "Cutoff Days",
        "Rows Remaining",
        "Overall Fraud Rate",
        "Segment 1",
        "Segment 2",
        "Segment 3",
        "Segment 4",
    ]
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                format_int(row["cutoff_days"]),
                format_int(row["remaining_rows"]),
                format_pct(row["overall_fraud_rate_pct"], 3),
                format_pct(row["segment_1_observed_rate_pct"], 3),
                format_pct(row["segment_2_observed_rate_pct"], 3),
                format_pct(row["segment_3_observed_rate_pct"], 3),
                format_pct(row["segment_4_observed_rate_pct"], 3),
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
            <div class="section-title">Selected Cutoff Summary</div>
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


def render_relative_table(df):
    headers = [
        "Cutoff Days",
        "Segment 1",
        "Segment 2",
        "Segment 3",
        "Segment 4",
    ]
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                format_int(row["cutoff_days"]),
                format_ratio(row["segment_1_relative_rate"], 3),
                format_ratio(row["segment_2_relative_rate"], 3),
                format_ratio(row["segment_3_relative_rate"], 3),
                format_ratio(row["segment_4_relative_rate"], 3),
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
            <div class="section-title">Selected Relative-Rate Summary</div>
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
        height=720,
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


def build_summary(df):
    df = df.dropna(subset=["TransactionDate", "Segment", "Fraud"]).copy()
    df["TransactionDay"] = df["TransactionDate"].dt.floor("D")
    as_of_date = df["TransactionDay"].max()
    df["age_days"] = (as_of_date - df["TransactionDay"]).dt.days

    rows = []
    for cutoff_days in range(MAX_CUTOFF_DAYS + 1):
        subset = df.loc[df["age_days"] >= cutoff_days].copy()
        overall_fraud_rate_pct = subset["Fraud"].mean() * 100

        segment_rates = (
            subset.groupby("Segment")["Fraud"]
            .mean()
            .mul(100)
            .to_dict()
        )

        row = {
            "cutoff_days": cutoff_days,
            "remaining_rows": len(subset),
            "overall_fraud_rate_pct": overall_fraud_rate_pct,
        }
        for segment in [1, 2, 3, 4]:
            observed_rate = float(segment_rates.get(segment, float("nan")))
            row[f"segment_{segment}_observed_rate_pct"] = observed_rate
            row[f"segment_{segment}_relative_rate"] = observed_rate / overall_fraud_rate_pct
        rows.append(row)

    return pd.DataFrame(rows), as_of_date


def add_segment_lines(fig, summary_df, value_column_suffix, yaxis_title, row, col):
    for segment in [1, 2, 3, 4]:
        column = f"segment_{segment}_{value_column_suffix}"
        hover_unit = "%" if value_column_suffix == "observed_rate_pct" else "x"
        fig.add_trace(
            go.Scatter(
                x=summary_df["cutoff_days"],
                y=summary_df[column],
                mode="lines",
                line=dict(color=SEGMENT_COLORS[segment], width=3),
                name=f"Segment {segment}",
                hovertemplate=(
                    "<b>Cutoff:</b> %{x} days"
                    + f"<br><b>Segment {segment}:</b> "
                    + ("%{y:.3f}%" if hover_unit == "%" else "%{y:.3f}x")
                    + "<extra></extra>"
                ),
            ),
            row=row,
            col=col,
        )
    fig.update_yaxes(title_text=yaxis_title, row=row, col=col)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET_PATH, usecols=["TransactionDate", "Segment", "Fraud"])
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], errors="coerce")
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce")
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce")
    df = df.dropna(subset=["TransactionDate", "Segment", "Fraud"]).copy()
    df["Segment"] = df["Segment"].astype(int)
    df["Fraud"] = df["Fraud"].astype(int)

    summary_df, as_of_date = build_summary(df)
    safe_write_csv(summary_df, SUMMARY_CSV, "Maturity sensitivity summary")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>Observed Fraud Rate by Maturity Cutoff</b>",
            "<b>Relative Fraud Rate by Maturity Cutoff</b>",
        ),
        horizontal_spacing=0.12,
    )

    add_segment_lines(
        fig,
        summary_df,
        value_column_suffix="observed_rate_pct",
        yaxis_title="Observed fraud rate (%)",
        row=1,
        col=1,
    )
    add_segment_lines(
        fig,
        summary_df,
        value_column_suffix="relative_rate",
        yaxis_title="Multiple of overall fraud rate",
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_xaxes(title_text="Removed most recent days", autorange="reversed", row=1, col=1)
    fig.update_xaxes(title_text="Removed most recent days", autorange="reversed", row=1, col=2)

    selected_cutoffs = summary_df.loc[
        summary_df["cutoff_days"].isin([0, 7, 14, 30, 45, 60])
    ].copy()

    cutoff_0 = summary_df.loc[summary_df["cutoff_days"] == 0].iloc[0]
    cutoff_60 = summary_df.loc[summary_df["cutoff_days"] == 60].iloc[0]
    stats = [
        ("As-Of Date", pd.Timestamp(as_of_date).strftime("%Y-%m-%d"), False),
        ("Cutoff Range", f"0 to {MAX_CUTOFF_DAYS} days", False),
        ("Rows at 0 Days", format_int(cutoff_0["remaining_rows"]), False),
        ("Rows at 60 Days", format_int(cutoff_60["remaining_rows"]), False),
        ("Overall Fraud at 0 Days", format_pct(cutoff_0["overall_fraud_rate_pct"], 3), False),
        ("Overall Fraud at 60 Days", format_pct(cutoff_60["overall_fraud_rate_pct"], 3), False),
    ]

    observations = [
        "Changing the maturity cutoff affects the level of the observed fraud rates, but it does not overturn the relative ranking of the segments, which suggests the segment risk ranking is not only a recency artifact.",
        "The higher relative fraud rate for less mature Segment 4 transactions suggests that exclusion decisions for new BIN-Channel pairs in this segment should be more tolerant or require more maturity before acting.",
        "One possible explanation is that Segment 4 is more aggressive and its fraud tends to be detected faster, which would make it look disproportionately worse on more recent transaction cohorts.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        "<strong>Method:</strong> For each cutoff, remove the most recent transaction days and recompute fraud rates by segment."
    )

    html_content = build_page(
        title="Segment vs Fraud Maturity Sensitivity",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        table_html=render_table(selected_cutoffs) + render_relative_table(selected_cutoffs),
        observations_html=render_observations(observations),
    )

    safe_write_text(OUTPUT_HTML, html_content, "HTML report")


if __name__ == "__main__":
    main()
