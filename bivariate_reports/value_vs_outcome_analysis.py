from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parent
CHALLENGE_DIR = ROOT_DIR.parent
DATASET_PATH = CHALLENGE_DIR / "Data_Prep" / "combined_deposits_cleaned.csv"

DATASET_LABEL = "March, April, and May deposit files (combined, cleaned)"
PRIMARY = "#4A90D9"
SECONDARY = "#E8A87C"
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
            font-size: 1.35em;
            font-weight: 600;
            line-height: 1.25;
            word-break: break-word;
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

CONFIGS = [
    {
        "entity_col": "Channel",
        "entity_label": "Channel",
        "outcome_col": "Approved",
        "outcome_label": "Approved",
        "metric_label": "approval rate",
        "html_path": ROOT_DIR / "channel_vs_approved_analysis.html",
        "summary_csv": ROOT_DIR / "channel_vs_approved_summary.csv",
    },
    {
        "entity_col": "Channel",
        "entity_label": "Channel",
        "outcome_col": "Fraud",
        "outcome_label": "Fraud",
        "metric_label": "fraud rate",
        "html_path": ROOT_DIR / "channel_vs_fraud_analysis.html",
        "summary_csv": ROOT_DIR / "channel_vs_fraud_summary.csv",
    },
    {
        "entity_col": "UserCardBIN",
        "entity_label": "BIN",
        "outcome_col": "Approved",
        "outcome_label": "Approved",
        "metric_label": "approval rate",
        "html_path": ROOT_DIR / "bin_vs_approved_analysis.html",
        "summary_csv": ROOT_DIR / "bin_vs_approved_summary.csv",
    },
    {
        "entity_col": "UserCardBIN",
        "entity_label": "BIN",
        "outcome_col": "Fraud",
        "outcome_label": "Fraud",
        "metric_label": "fraud rate",
        "html_path": ROOT_DIR / "bin_vs_fraud_analysis.html",
        "summary_csv": ROOT_DIR / "bin_vs_fraud_summary.csv",
    },
]


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


def render_table(df, entity_label, outcome_rows_label, metric_label):
    display_df = df.copy()
    display_df = display_df.rename(
        columns={
            "entity_value": entity_label,
            "rows": "Rows",
            outcome_rows_label: outcome_rows_label.replace("_", " ").title(),
            "share_pct": "Volume Share",
            "observed_rate_pct": metric_label.title(),
            "rate_index": f"{metric_label.title()} vs Overall",
        }
    )

    display_df["Rows"] = display_df["Rows"].map(format_int)
    display_df[display_df.columns[2]] = display_df[display_df.columns[2]].map(format_int)
    display_df["Volume Share"] = display_df["Volume Share"].map(lambda value: format_pct(value, 2))
    display_df[metric_label.title()] = display_df[metric_label.title()].map(lambda value: format_pct(value, 3))
    display_df[f"{metric_label.title()} vs Overall"] = display_df[
        f"{metric_label.title()} vs Overall"
    ].map(lambda value: format_ratio(value, 2))

    headers = "".join(f"<th>{escape(str(column))}</th>" for column in display_df.columns)
    body_rows = []
    for row in display_df.itertuples(index=False):
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        body_rows.append(f"<tr>{cells}</tr>")
    body_html = "".join(body_rows)

    return f"""
    <div class="panel">
        <div class="section-header">
            <div class="section-title">Top {entity_label}s by Rows</div>
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
    <div class="panel">
        <div class="section-header">
            <div class="section-title">Bivariate Charts</div>
        </div>
        {figure_html}
    </div>
    {table_html}
    {observations_html}
</body>
</html>"""


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


def apply_layout(fig):
    fig.update_layout(
        showlegend=False,
        height=620,
        title_text="",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=70, r=30, t=40, b=50),
    )
    for annotation in fig.layout.annotations:
        annotation.font = dict(family="Segoe UI, -apple-system, sans-serif", size=13, color=TEXT)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickcolor="#999", ticklen=4)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickcolor="#999", ticklen=4)


def prepare_summary(df, entity_col, outcome_col):
    summary = (
        df.groupby(entity_col)
        .agg(
            rows=(outcome_col, "size"),
            positive_rows=(outcome_col, "sum"),
        )
        .reset_index()
        .rename(columns={entity_col: "entity_value"})
        .sort_values(["rows", "entity_value"], ascending=[False, True])
        .reset_index(drop=True)
    )
    summary["share_pct"] = summary["rows"] / len(df) * 100
    summary["observed_rate_pct"] = summary["positive_rows"] / summary["rows"] * 100
    overall_rate_pct = df[outcome_col].mean() * 100
    summary["rate_index"] = summary["observed_rate_pct"] / overall_rate_pct
    return summary, overall_rate_pct


def build_figure(summary, entity_label, metric_label):
    top = summary.head(20).copy().iloc[::-1]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            f"<b>Top 20 {entity_label}s by Rows: {metric_label.title()}</b>",
            f"<b>Rows vs {metric_label.title()}</b>",
        ),
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Bar(
            x=top["observed_rate_pct"],
            y=top["entity_value"],
            orientation="h",
            marker_color=PRIMARY,
            text=[format_pct(value, 2) for value in top["observed_rate_pct"]],
            textposition="outside",
            customdata=top[["rows", "positive_rows"]].values,
            hovertemplate=(
                f"<b>{entity_label}:</b> %{{y}}"
                f"<br><b>{metric_label.title()}:</b> %{{x:.3f}}%"
                "<br><b>Rows:</b> %{customdata[0]:,}"
                "<br><b>Positive rows:</b> %{customdata[1]:,}<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=summary["rows"],
            y=summary["observed_rate_pct"],
            mode="markers",
            marker=dict(color=SECONDARY, size=7, opacity=0.38),
            customdata=summary[["entity_value", "positive_rows"]].values,
            hovertemplate=(
                f"<b>{entity_label}:</b> %{{customdata[0]}}"
                "<br><b>Rows:</b> %{x:,}"
                f"<br><b>{metric_label.title()}:</b> %{{y:.3f}}%"
                "<br><b>Positive rows:</b> %{customdata[1]:,}<extra></extra>"
            ),
        ),
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_xaxes(title_text=f"{metric_label.title()} (%)", row=1, col=1)
    fig.update_yaxes(title_text=entity_label, row=1, col=1)
    fig.update_xaxes(title_text="Rows", type="log", row=1, col=2)
    fig.update_yaxes(title_text=f"{metric_label.title()} (%)", row=1, col=2)
    return fig


def generate_report(config, df):
    entity_col = config["entity_col"]
    entity_label = config["entity_label"]
    outcome_col = config["outcome_col"]
    outcome_label = config["outcome_label"]
    metric_label = config["metric_label"]

    summary, overall_rate_pct = prepare_summary(df, entity_col, outcome_col)
    summary = summary.rename(columns={"positive_rows": f"{outcome_col.lower()}_rows"})
    safe_write_csv(summary, config["summary_csv"], f"{entity_label} vs {outcome_label.lower()} summary")

    fig = build_figure(summary.rename(columns={f"{outcome_col.lower()}_rows": "positive_rows"}), entity_label, metric_label)

    top_value = summary.iloc[0]
    highest_rate_value = summary.loc[summary["observed_rate_pct"].idxmax()]
    median_rate = summary["observed_rate_pct"].median()

    stats = [
        ("Rows Analyzed", format_int(len(df)), False),
        (f"Distinct {entity_label}s", format_int(len(summary)), False),
        (f"Overall {metric_label.title()}", format_pct(overall_rate_pct, 3), False),
        (f"Median {metric_label.title()}", format_pct(median_rate, 3), False),
        (f"Top {entity_label}", str(top_value["entity_value"]), True),
        ("Top Value Rows", format_int(top_value["rows"]), False),
        (f"Top Value {metric_label.title()}", format_pct(top_value["observed_rate_pct"], 3), False),
        (f"Highest {metric_label.title()} {entity_label}", str(highest_rate_value["entity_value"]), True),
    ]

    observations = [
        f"The largest {entity_label.lower()} is {top_value['entity_value']} with {format_int(top_value['rows'])} rows and an observed {metric_label} of {format_pct(top_value['observed_rate_pct'], 3)}.",
        f"The median {metric_label} across {format_int(len(summary))} {entity_label.lower()}s is {format_pct(median_rate, 3)}, while the overall dataset rate is {format_pct(overall_rate_pct, 3)}.",
        f"The scatterplot shows how much of the rate spread is happening in thin values versus higher-volume values.",
        "The top-20 chart is ordered by rows, so it prioritizes operationally relevant values rather than just extreme rates from tiny samples.",
    ]
    if outcome_col == "Fraud":
        observations.append(
            "This fraud view is still raw observed fraud by value. It is not maturity-adjusted and should be read as an exploratory bivariate cut, not as the final decision metric."
        )

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> Raw observed {metric_label} by {entity_label.lower()} in the cleaned dataset."
    )

    html_content = build_page(
        title=f"{entity_label} vs {outcome_label} Bivariate Analysis",
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        table_html=render_table(
            summary.head(15)[
                ["entity_value", "rows", f"{outcome_col.lower()}_rows", "share_pct", "observed_rate_pct", "rate_index"]
            ],
            entity_label,
            f"{outcome_col.lower()}_rows",
            metric_label,
        ),
        observations_html=render_observations(observations),
    )
    safe_write_text(config["html_path"], html_content, "HTML report")


def main():
    dtype_map = {"UserCardBIN": str, "Channel": str}
    df = pd.read_csv(DATASET_PATH, usecols=["UserCardBIN", "Channel", "Approved", "Fraud"], dtype=dtype_map)
    df = df.dropna(subset=["UserCardBIN", "Channel", "Approved", "Fraud"]).copy()
    df["Approved"] = pd.to_numeric(df["Approved"], errors="coerce")
    df["Fraud"] = pd.to_numeric(df["Fraud"], errors="coerce")
    df = df.dropna(subset=["Approved", "Fraud"]).copy()
    df["Approved"] = df["Approved"].astype(int)
    df["Fraud"] = df["Fraud"].astype(int)

    for config in CONFIGS:
        generate_report(config, df[[config["entity_col"], config["outcome_col"]]].copy())


if __name__ == "__main__":
    main()
