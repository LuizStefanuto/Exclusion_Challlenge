from calendar import day_abbr
from datetime import datetime
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
COMBINED_DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"
REPORT_DIR = ROOT_DIR

PRIMARY = "#4A90D9"
SECONDARY = "#7FB3D3"
ACCENT = "#E8A87C"
ALERT = "#D9534F"
SUCCESS = "#27AE60"
TEXT = "#333333"
BACKGROUND = "#FAFAFA"
CARD_BACKGROUND = "#FFFFFF"
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
        .note {
            padding: 16px 20px;
            color: #4a5568;
            line-height: 1.7;
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
        .report-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 14px;
            padding: 20px;
        }
        .report-card {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 16px;
            background: #fbfdff;
        }
        .report-card a {
            color: #1d4ed8;
            text-decoration: none;
            font-weight: 600;
        }
        .report-card a:hover {
            text-decoration: underline;
        }
        .report-description {
            margin-top: 8px;
            color: #64748b;
            line-height: 1.6;
            font-size: 0.92em;
        }
    </style>
"""

BINARY_CONFIG = {
    "Approved": {
        "title": "Approved",
        "zero_label": "Declined (0)",
        "one_label": "Approved (1)",
        "positive_label": "Approval Rate",
    },
    "Fraud": {
        "title": "Fraud",
        "zero_label": "Non-Fraud (0)",
        "one_label": "Fraud (1)",
        "positive_label": "Fraud Rate",
    },
}


def format_int(value):
    return f"{int(value):,}"


def format_float(value, decimals=2):
    return f"{float(value):,.{decimals}f}"


def format_pct(value, decimals=2):
    return f"{float(value):.{decimals}f}%"


def format_timestamp(value):
    if pd.isna(value):
        return "-"
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


def format_month_period(period):
    return period.to_timestamp().strftime("%b %Y")


def slugify(name):
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")


def safe_write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_stats(cards):
    html_parts = ['<div class="stats-grid">']
    for label, value, small in cards:
        size_class = " small" if small else ""
        html_parts.append(
            f"""
            <div class="stat-card{size_class}">
                <div class="stat-label">{escape(str(label))}</div>
                <div class="stat-value">{escape(str(value))}</div>
            </div>
            """
        )
    html_parts.append("</div>")
    return "".join(html_parts)


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


def render_table(headers, rows):
    header_html = "".join(f"<th>{escape(str(header))}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(cell))}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    body_html = "".join(body_rows)
    return f"""
    <div class="table-container">
        <div class="section-header">
            <div class="section-title">Monthly Summary</div>
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


def build_page(title, subtitle, stats_html, figure_html, observations_html, extra_html=""):
    chart_section = ""
    if figure_html:
        chart_section = f"""
        <div class="chart-container">
            <div class="section-header">
                <div class="section-title">Distribution Charts</div>
            </div>
            {figure_html}
        </div>
        """

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
    {chart_section}
    {extra_html}
    {observations_html}
</body>
</html>"""


def apply_layout(fig, height=780):
    fig.update_layout(
        showlegend=False,
        height=height,
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


def prepare_dataset():
    df = pd.read_csv(COMBINED_DATASET_PATH).copy()
    df["UserCardBIN"] = pd.to_numeric(df["UserCardBIN"], errors="coerce").astype("Int64")
    df["Approved"] = pd.to_numeric(df["Approved"], errors="coerce").astype("Int64")
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce").astype("Int64")
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce").astype("Int64")
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], errors="coerce")
    df["FraudDetectionDate"] = pd.to_datetime(df["FraudDetectionDate"], errors="coerce")
    return df


def get_transaction_month_periods(df):
    return sorted(df["TransactionDate"].dropna().dt.to_period("M").unique())


def report_subtitle(note=None):
    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    if note:
        subtitle += f" &nbsp;|&nbsp; <strong>Note:</strong> {escape(note)}"
    return subtitle


def build_binary_report(df, column):
    config = BINARY_CONFIG[column]
    series = df[column]
    valid = series.dropna().astype(int)
    total_rows = len(df)
    valid_rows = len(valid)
    null_count = int(series.isna().sum())

    count_0 = int((valid == 0).sum())
    count_1 = int((valid == 1).sum())
    rate_0 = count_0 / valid_rows * 100 if valid_rows else 0.0
    rate_1 = count_1 / valid_rows * 100 if valid_rows else 0.0

    if column in {"Approved", "Fraud"}:
        fig = make_subplots(
            rows=1,
            cols=1,
            subplot_titles=(f"<b>{config['zero_label']} vs {config['one_label']}</b>",),
        )

        fig.add_trace(
            go.Bar(
                x=[config["zero_label"], config["one_label"]],
                y=[count_0, count_1],
                marker_color=[SECONDARY, PRIMARY],
                marker_line_color=["#5A8DB5", "#2C5F9E"],
                marker_line_width=1,
                text=[format_pct(rate_0, 1), format_pct(rate_1, 1)],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        apply_layout(fig, height=640)

        stats = [
            ("Total Rows", format_int(total_rows), False),
            ("Valid Rows", format_int(valid_rows), False),
            (config["zero_label"], format_int(count_0), False),
            (config["one_label"], format_int(count_1), False),
            (config["positive_label"], format_pct(rate_1, 2), False),
            ("Null Values", format_int(null_count), False),
        ]

        observations = [
            f"{config['positive_label']} is {format_pct(rate_1, 2)} across the combined dataset.",
            f"{config['one_label']} rows total {format_int(count_1)}, while {config['zero_label']} rows total {format_int(count_0)}.",
        ]
        if column == "Fraud":
            observations.append(
                "Fraud takes time to classify, so the most recent transactions, especially in May, may still have missing fraud outcomes."
            )

        html_content = build_page(
            title=f"{config['title']} Univariate Analysis",
            subtitle=report_subtitle(),
            stats_html=render_stats(stats),
            figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
            observations_html=render_observations(observations),
        )

        file_name = f"{slugify(column)}_analysis.html"
        safe_write_text(REPORT_DIR / file_name, html_content)
        return {
            "title": f"{config['title']} Univariate Analysis",
            "file_name": file_name,
            "description": f"Overall distribution for {column}.",
        }

    monthly_subset = df.dropna(subset=["TransactionDate", column]).copy()
    monthly_subset["TransactionMonth"] = monthly_subset["TransactionDate"].dt.to_period("M")
    month_order = get_transaction_month_periods(monthly_subset)
    month_labels = [format_month_period(period) for period in month_order]
    month_counts = (
        monthly_subset.groupby(["TransactionMonth", column])
        .size()
        .unstack(fill_value=0)
        .reindex(index=month_order, columns=[0, 1], fill_value=0)
    )
    month_rate = monthly_subset.groupby("TransactionMonth")[column].mean().reindex(month_order) * 100
    daily_subset = df.dropna(subset=["TransactionDate", column]).copy()
    daily_rate = (
        daily_subset.groupby(daily_subset["TransactionDate"].dt.floor("D"))[column]
        .mean()
        .sort_index()
        * 100
    )

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[{}, None], [{}, {}]],
        subplot_titles=(
            f"<b>{config['zero_label']} vs {config['one_label']}</b>",
            "<b>Counts by Transaction Month</b>",
            "<b>Daily Rate by Transaction Date</b>",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )

    fig.add_trace(
        go.Bar(
            x=[config["zero_label"], config["one_label"]],
            y=[count_0, count_1],
            marker_color=[SECONDARY, PRIMARY],
            marker_line_color=["#5A8DB5", "#2C5F9E"],
            marker_line_width=1,
            text=[format_pct(rate_0, 1), format_pct(rate_1, 1)],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=month_counts[0].tolist(),
            name=config["zero_label"],
            marker_color=SECONDARY,
            hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=month_counts[1].tolist(),
            name=config["one_label"],
            marker_color=PRIMARY,
            hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=list(daily_rate.index),
            y=daily_rate.values,
            mode="lines",
            line=dict(color=PRIMARY, width=2),
            fill="tozeroy",
            fillcolor="rgba(74, 144, 217, 0.18)",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Rate:</b> %{y:.2f}%<extra></extra>",
        ),
        row=2,
        col=2,
    )

    fig.update_layout(barmode="stack")
    apply_layout(fig)

    highest_month = format_month_period(month_rate.idxmax())
    lowest_month = format_month_period(month_rate.idxmin())

    stats = [
        ("Total Rows", format_int(total_rows), False),
        ("Valid Rows", format_int(valid_rows), False),
        (config["zero_label"], format_int(count_0), False),
        (config["one_label"], format_int(count_1), False),
        (config["positive_label"], format_pct(rate_1, 2), False),
        ("Null Values", format_int(null_count), False),
        ("Highest File-Month Rate", f"{highest_month} ({format_pct(month_rate.max(), 2)})", True),
        ("Lowest File-Month Rate", f"{lowest_month} ({format_pct(month_rate.min(), 2)})", True),
    ]

    observations = [
        f"{config['positive_label']} is {format_pct(rate_1, 2)} across the combined dataset.",
        f"{highest_month} has the highest file-month rate at {format_pct(month_rate.max(), 2)}, while {lowest_month} is lowest at {format_pct(month_rate.min(), 2)}.",
        f"Null coverage is {format_int(null_count)} rows, so this flag is effectively complete for exploratory work.",
        "Daily rate moves over time, so month-level aggregation alone hides variation inside each source file.",
    ]

    html_content = build_page(
        title=f"{config['title']} Univariate Analysis",
        subtitle=report_subtitle(),
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )

    file_name = f"{slugify(column)}_analysis.html"
    safe_write_text(REPORT_DIR / file_name, html_content)
    return {
        "title": f"{config['title']} Univariate Analysis",
        "file_name": file_name,
        "description": f"Overall distribution, file-month counts, and daily rate trend for {column}.",
    }


def build_high_cardinality_report(df, column, note=None):
    valid = df[column].dropna().astype(str)
    total_rows = len(df)
    valid_rows = len(valid)
    null_count = int(df[column].isna().sum())
    counts = valid.value_counts()

    top_15 = counts.head(15)
    top_10_share = counts.head(10).sum() / valid_rows * 100 if valid_rows else 0.0
    mode_value = counts.index[0]
    mode_count = int(counts.iloc[0])
    mode_share = mode_count / valid_rows * 100 if valid_rows else 0.0
    median_rows = float(counts.median()) if not counts.empty else 0.0

    cumulative_share = counts.cumsum() / valid_rows * 100 if valid_rows else counts.cumsum()

    include_boxplot = column in {"Channel", "UserCardBIN"}
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[{}, {}], [{}, {} if include_boxplot else None]],
        subplot_titles=(
            "<b>Top 15 Values by Row Count</b>",
            "<b>Rows per Value Distribution</b>",
            "<b>Cumulative Share by Ranked Value</b>",
            "<b>Rows per Value Boxplot</b>" if include_boxplot else "",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )

    fig.add_trace(
        go.Bar(
            x=top_15.index.tolist(),
            y=top_15.values.tolist(),
            marker_color=PRIMARY,
            marker_line_color="#2C5F9E",
            marker_line_width=1,
            hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Histogram(
            x=counts.values,
            nbinsx=30,
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            hovertemplate="<b>Rows per value:</b> %{x}<br><b>Values:</b> %{y}<extra></extra>",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(cumulative_share) + 1)),
            y=cumulative_share.values,
            mode="lines",
            line=dict(color=PRIMARY, width=2),
            fill="tozeroy",
            fillcolor="rgba(74, 144, 217, 0.18)",
            hovertemplate="<b>Ranked value:</b> %{x}<br><b>Cumulative share:</b> %{y:.2f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    if include_boxplot:
        fig.add_trace(
            go.Box(
                y=counts.values,
                marker_color=ACCENT,
                boxpoints=False,
                hovertemplate="<b>Rows per value:</b> %{y:,}<extra></extra>",
            ),
            row=2,
            col=2,
        )

    apply_layout(fig)
    if include_boxplot:
        fig.update_xaxes(title_text="", showticklabels=False, row=2, col=2)
        fig.update_yaxes(title_text="Rows per value", type="log", row=2, col=2)

    stats = [
        ("Total Rows", format_int(total_rows), False),
        ("Valid Rows", format_int(valid_rows), False),
        ("Unique Values", format_int(counts.size), False),
        ("Null Values", format_int(null_count), False),
        ("Mode", f"{mode_value} ({format_int(mode_count)})", True),
        ("Mode Share", format_pct(mode_share, 2), False),
        ("Top 10 Share", format_pct(top_10_share, 2), False),
        ("Median Rows / Value", format_float(median_rows, 1), False),
    ]

    concentration_observation = (
        f"The top 10 values contribute {format_pct(top_10_share, 2)} of all non-null rows, "
        "which shows the field is even more concentrated than Channel."
        if column == "UserCardBIN"
        else f"The top 10 values contribute {format_pct(top_10_share, 2)} of all non-null rows, which shows how concentrated the field is."
    )

    observations = [
        f"The most common value is {mode_value}, accounting for {format_pct(mode_share, 2)} of non-null rows.",
        concentration_observation,
    ]
    if note:
        observations.append(note)

    html_content = build_page(
        title=f"{column} Univariate Analysis",
        subtitle=report_subtitle(note=note),
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )

    file_name = f"{slugify(column)}_analysis.html"
    safe_write_text(REPORT_DIR / file_name, html_content)
    return {
        "title": f"{column} Univariate Analysis",
        "file_name": file_name,
        "description": f"Cardinality, concentration, and long-tail structure for {column}.",
    }


def build_segment_report(df):
    valid = df["Segment"].dropna().astype(int)
    total_rows = len(df)
    valid_rows = len(valid)
    null_count = int(df["Segment"].isna().sum())
    segment_order = [1, 2, 3, 4]
    counts = valid.value_counts().reindex(segment_order, fill_value=0)
    shares = counts / valid_rows * 100 if valid_rows else counts
    cumulative = shares.cumsum()

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[{}, {}], [{}, None]],
        subplot_titles=(
            "<b>Rows by Segment</b>",
            "<b>Share of Valid Rows by Segment</b>",
            "<b>Cumulative Segment Share</b>",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )

    fig.add_trace(
        go.Bar(
            x=[str(value) for value in segment_order],
            y=counts.values.tolist(),
            marker_color=PRIMARY,
            marker_line_color="#2C5F9E",
            marker_line_width=1,
            hovertemplate="<b>Segment %{x}</b><br>Rows: %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=[str(value) for value in segment_order],
            y=shares.values.tolist(),
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            text=[format_pct(value, 1) for value in shares.values],
            textposition="outside",
            hovertemplate="<b>Segment %{x}</b><br>Share: %{y:.2f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=[str(value) for value in segment_order],
            y=cumulative.values.tolist(),
            mode="lines+markers",
            line=dict(color=PRIMARY, width=2),
            marker=dict(size=8, color=PRIMARY),
            hovertemplate="<b>Up to segment %{x}</b><br>Cumulative share: %{y:.2f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    apply_layout(fig)

    dominant_segment = int(counts.idxmax())
    stats = [
        ("Total Rows", format_int(total_rows), False),
        ("Valid Rows", format_int(valid_rows), False),
        ("Unique Segments", format_int(counts.gt(0).sum()), False),
        ("Dominant Segment", f"Segment {dominant_segment}", False),
        ("Segment 1 Share", format_pct(shares.loc[1], 2), False),
    ]

    observations = [
        f"Segment {dominant_segment} is the largest segment in the combined data.",
        f"Segments 1 and 2 together contribute {format_pct(shares.loc[1] + shares.loc[2], 2)} of valid rows, so the dataset leans toward lower-risk customers.",
    ]

    html_content = build_page(
        title="Segment Univariate Analysis",
        subtitle=report_subtitle(),
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )

    file_name = "segment_analysis.html"
    safe_write_text(REPORT_DIR / file_name, html_content)
    return {
        "title": "Segment Univariate Analysis",
        "file_name": file_name,
        "description": "Volume, share, and cumulative distribution for customer segment.",
    }


def build_transaction_date_report(df):
    valid = df["TransactionDate"].dropna()
    total_rows = len(df)
    valid_rows = len(valid)
    null_count = int(df["TransactionDate"].isna().sum())

    hour_counts = valid.dt.hour.value_counts().sort_index()
    dow_counts = valid.dt.dayofweek.value_counts().sort_index()
    month_counts = valid.dt.to_period("M").value_counts().sort_index()
    daily_counts = valid.dt.floor("D").value_counts().sort_index()

    peak_hour = int(hour_counts.idxmax())
    busiest_day = daily_counts.idxmax()

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "<b>Rows by Hour of Day</b>",
            "<b>Rows by Day of Week</b>",
            "<b>Rows by Calendar Month</b>",
            "<b>Daily Transaction Volume</b>",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )

    fig.add_trace(
        go.Bar(
            x=list(range(24)),
            y=[hour_counts.get(hour, 0) for hour in range(24)],
            marker_color=PRIMARY,
            marker_line_color="#2C5F9E",
            marker_line_width=1,
            hovertemplate="<b>Hour:</b> %{x}:00<br><b>Rows:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=[day_abbr[index] for index in range(7)],
            y=[dow_counts.get(index, 0) for index in range(7)],
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            hovertemplate="<b>Day:</b> %{x}<br><b>Rows:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=[str(value) for value in month_counts.index],
            y=month_counts.values.tolist(),
            marker_color=ACCENT,
            marker_line_color="#C17A4B",
            marker_line_width=1,
            hovertemplate="<b>Month:</b> %{x}<br><b>Rows:</b> %{y:,}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=list(daily_counts.index),
            y=daily_counts.values,
            mode="lines",
            line=dict(color=PRIMARY, width=2),
            fill="tozeroy",
            fillcolor="rgba(74, 144, 217, 0.18)",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Rows:</b> %{y:,}<extra></extra>",
        ),
        row=2,
        col=2,
    )

    apply_layout(fig)

    stats = [
        ("Total Rows", format_int(total_rows), False),
        ("Valid Rows", format_int(valid_rows), False),
        ("Null Values", format_int(null_count), False),
        ("Min Timestamp", format_timestamp(valid.min()), True),
        ("Max Timestamp", format_timestamp(valid.max()), True),
        ("Date Range (days)", format_int((valid.max() - valid.min()).days), False),
        ("Peak Hour", f"{peak_hour}:00", False),
        ("Busiest Day", pd.Timestamp(busiest_day).strftime("%Y-%m-%d"), True),
        ("Avg Rows / Day", format_float(daily_counts.mean(), 0), False),
    ]

    observations = [
        f"Transaction timestamps span from {format_timestamp(valid.min())} to {format_timestamp(valid.max())}.",
        f"The busiest hour is {peak_hour}:00, which is where the intraday volume peaks in the combined files.",
        f"Average daily volume is {format_float(daily_counts.mean(), 0)} rows, but the daily trend shows material day-to-day variation.",
    ]

    html_content = build_page(
        title="TransactionDate Univariate Analysis",
        subtitle=report_subtitle(),
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )

    file_name = "transactiondate_analysis.html"
    safe_write_text(REPORT_DIR / file_name, html_content)
    return {
        "title": "TransactionDate Univariate Analysis",
        "file_name": file_name,
        "description": "Intraday, weekly, monthly, and daily volume distribution for transaction creation time.",
    }


def build_fraud_detection_report(df):
    valid = df["FraudDetectionDate"].dropna()
    total_rows = len(df)
    valid_rows = len(valid)
    null_count = int(df["FraudDetectionDate"].isna().sum())
    coverage_all_rows = valid_rows / total_rows * 100 if total_rows else 0.0

    hour_counts = valid.dt.hour.value_counts().sort_index()
    detection_days = valid.dt.floor("D").value_counts().sort_index()
    dow_counts = valid.dt.dayofweek.value_counts().sort_index()
    peak_hour = int(hour_counts.idxmax())
    peak_dow = day_abbr[int(dow_counts.idxmax())]
    avg_detections_per_active_day = detection_days.mean()

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "<b>Missing vs Populated</b>",
            "<b>Detections by Day of Week</b>",
            "<b>Detections by Hour of Day</b>",
            "<b>Daily Detection Volume</b>",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )

    fig.add_trace(
        go.Bar(
            x=["Missing", "Populated"],
            y=[null_count, valid_rows],
            marker_color=[SECONDARY, PRIMARY],
            marker_line_color=["#5A8DB5", "#2C5F9E"],
            marker_line_width=1,
            text=[format_pct(null_count / total_rows * 100, 1), format_pct(coverage_all_rows, 1)],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Rows: %{y:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=[day_abbr[index] for index in range(7)],
            y=[dow_counts.get(index, 0) for index in range(7)],
            marker_color=ACCENT,
            marker_line_color="#C17A4B",
            marker_line_width=1,
            hovertemplate="<b>Day:</b> %{x}<br><b>Detections:</b> %{y:,}<extra></extra>",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=list(range(24)),
            y=[hour_counts.get(hour, 0) for hour in range(24)],
            marker_color=SECONDARY,
            marker_line_color="#5A8DB5",
            marker_line_width=1,
            hovertemplate="<b>Hour:</b> %{x}:00<br><b>Detections:</b> %{y:,}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=list(detection_days.index),
            y=detection_days.values,
            mode="lines",
            line=dict(color=PRIMARY, width=2),
            fill="tozeroy",
            fillcolor="rgba(74, 144, 217, 0.18)",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Detections:</b> %{y:,}<extra></extra>",
        ),
        row=2,
        col=2,
    )

    apply_layout(fig)

    stats = [
        ("Total Rows", format_int(total_rows), False),
        ("Populated Rows", format_int(valid_rows), False),
        ("Null Values", format_int(null_count), False),
        ("Populated Share of All Rows", format_pct(coverage_all_rows, 2), False),
        ("Min Detection Timestamp", format_timestamp(valid.min()), True),
        ("Max Detection Timestamp", format_timestamp(valid.max()), True),
        ("Peak Hour", f"{peak_hour}:00", False),
        ("Peak Day", peak_dow, False),
        ("Avg Detections / Active Day", format_float(avg_detections_per_active_day, 1), False),
    ]

    observations = [
        f"Only {format_pct(coverage_all_rows, 2)} of all rows have a populated fraud detection timestamp, so this field is sparse in the dataset.",
        f"Detection timestamps span from {format_timestamp(valid.min())} to {format_timestamp(valid.max())}.",
        f"The busiest detection hour is {peak_hour}:00 and the busiest weekday is {peak_dow}.",
        f"Average daily detection volume across active days is {format_float(avg_detections_per_active_day, 1)} rows.",
    ]

    html_content = build_page(
        title="FraudDetectionDate Univariate Analysis",
        subtitle=report_subtitle(),
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        observations_html=render_observations(observations),
    )

    file_name = "frauddetectiondate_analysis.html"
    safe_write_text(REPORT_DIR / file_name, html_content)
    return {
        "title": "FraudDetectionDate Univariate Analysis",
        "file_name": file_name,
        "description": "Missingness and calendar distribution for fraud detection timestamps.",
    }


def build_index_page(df, reports):
    month_subset = df.dropna(subset=["TransactionDate"]).copy()
    month_subset["TransactionMonth"] = month_subset["TransactionDate"].dt.to_period("M")
    month_order = get_transaction_month_periods(month_subset)
    month_summary = (
        month_subset.groupby("TransactionMonth")
        .agg(
            rows=("TransactionMonth", "size"),
            approval_rate=("Approved", "mean"),
            fraud_rate=("Fraud", "mean"),
            min_transaction=("TransactionDate", "min"),
            max_transaction=("TransactionDate", "max"),
        )
        .reindex(month_order)
    )

    month_rows = []
    for transaction_month, row in month_summary.iterrows():
        month_rows.append(
            [
                format_month_period(transaction_month),
                format_int(row["rows"]),
                format_pct(row["approval_rate"] * 100, 2),
                format_pct(row["fraud_rate"] * 100, 3),
                format_timestamp(row["min_transaction"]),
                format_timestamp(row["max_transaction"]),
            ]
        )

    report_cards = []
    for report in reports:
        report_cards.append(
            f"""
            <div class="report-card">
                <a href="{escape(report['file_name'])}">{escape(report['title'])}</a>
                <div class="report-description">{escape(report['description'])}</div>
            </div>
            """
        )

    stats = [
        ("Total Rows", format_int(len(df)), False),
        ("Channels", format_int(df["Channel"].nunique()), False),
        ("UserCardBINs", format_int(df["UserCardBIN"].nunique()), False),
        ("Approval Rate", format_pct(df["Approved"].mean() * 100, 2), False),
        ("Fraud Rate", format_pct(df["Fraud"].mean() * 100, 3), False),
        ("Segment Nulls", format_int(df["Segment"].isna().sum()), False),
        ("Months Covered", ", ".join(format_month_period(period) for period in month_order), True),
        ("Schema Note", "May file should already use UserCardBIN", True),
    ]

    extra_html = (
        """
        <div class="notes-container">
            <div class="section-header">
            <div class="section-title">Report Index</div>
            </div>
            <div class="report-grid">
        """
        + "".join(report_cards)
        + """
            </div>
        </div>
        """
        + render_table(
            headers=[
                "Transaction Month",
                "Rows",
                "Approval Rate",
                "Fraud Rate",
                "Min TransactionDate",
                "Max TransactionDate",
            ],
            rows=month_rows,
        )
    )

    observations = [
        "This folder contains one report per original challenge variable, using the combined March-April-May dataset.",
        "The unification step assumes May already uses the same UserCardBIN header as March and April.",
        "The month summary lets you separate actual performance changes from simple differences in file size.",
        "FraudDetectionDate is sparse by design, so its report is the one place where lag-to-detection is added explicitly.",
    ]

    html_content = build_page(
        title="Challenge Univariate Analysis Index",
        subtitle=report_subtitle(note="Generated from the three raw challenge CSVs after header alignment."),
        stats_html=render_stats(stats),
        figure_html="",
        observations_html=render_observations(observations),
        extra_html=extra_html,
    )
    safe_write_text(REPORT_DIR / "index.html", html_content)


def main():
    df = prepare_dataset()

    reports = []
    reports.append(build_high_cardinality_report(df, "Channel"))
    reports.append(
        build_high_cardinality_report(
            df,
            "UserCardBIN",
        )
    )
    reports.append(build_binary_report(df, "Approved"))
    reports.append(build_binary_report(df, "Fraud"))
    reports.append(build_transaction_date_report(df))
    reports.append(build_fraud_detection_report(df))
    reports.append(build_segment_report(df))

    build_index_page(df, reports)

    print(f"Generated {len(reports)} univariate reports in {REPORT_DIR}")
    print("Open Challenge/univariate_reports/index.html to browse them.")


if __name__ == "__main__":
    main()
