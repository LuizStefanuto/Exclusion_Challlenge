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

SEGMENT_COLORS = {
    1: "#4A90D9",
    2: "#7FB3D3",
    3: "#E8A87C",
    4: "#D9534F",
}
PRIMARY = "#4A90D9"
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
        "title": "Channel vs Segment Bivariate Analysis",
        "scope_text": "Segment composition across channels in the cleaned dataset.",
        "html_path": ROOT_DIR / "channel_vs_segment_analysis.html",
        "summary_csv": ROOT_DIR / "channel_vs_segment_summary.csv",
    },
    {
        "entity_col": "UserCardBIN",
        "entity_label": "BIN",
        "title": "BIN vs Segment Bivariate Analysis",
        "scope_text": "Segment composition across BINs in the cleaned dataset.",
        "html_path": ROOT_DIR / "bin_vs_segment_analysis.html",
        "summary_csv": ROOT_DIR / "bin_vs_segment_summary.csv",
    },
]


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


def render_table(df, entity_label):
    display_df = df.copy()
    display_df = display_df.rename(
        columns={
            "entity_value": entity_label,
            "rows": "Rows",
            "segment_count": "Segments Present",
            "dominant_segment": "Dominant Segment",
            "dominant_share_pct": "Dominant Share",
            "segment_1_share_pct": "Segment 1 Share",
            "segment_2_share_pct": "Segment 2 Share",
            "segment_3_share_pct": "Segment 3 Share",
            "segment_4_share_pct": "Segment 4 Share",
        }
    )

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
        barmode="stack",
        showlegend=True,
        height=620,
        title_text="",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(family="Segoe UI, -apple-system, sans-serif", size=12, color=TEXT),
        margin=dict(l=70, r=30, t=40, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    for annotation in fig.layout.annotations:
        annotation.font = dict(family="Segoe UI, -apple-system, sans-serif", size=13, color=TEXT)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickcolor="#999", ticklen=4)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickcolor="#999", ticklen=4)


def prepare_summary(df, entity_col):
    counts = (
        df.groupby([entity_col, "Segment"])
        .size()
        .reset_index(name="rows")
    )
    pivot = counts.pivot(index=entity_col, columns="Segment", values="rows").fillna(0)
    pivot = pivot.reindex(columns=[1, 2, 3, 4], fill_value=0)
    pivot.columns = [f"segment_{segment}_rows" for segment in [1, 2, 3, 4]]
    summary = pivot.reset_index().rename(columns={entity_col: "entity_value"})

    summary["rows"] = summary[[f"segment_{segment}_rows" for segment in [1, 2, 3, 4]]].sum(axis=1)
    summary["segment_count"] = summary[[f"segment_{segment}_rows" for segment in [1, 2, 3, 4]]].gt(0).sum(axis=1)

    for segment in [1, 2, 3, 4]:
        summary[f"segment_{segment}_share_pct"] = summary[f"segment_{segment}_rows"] / summary["rows"] * 100

    dominant_row_cols = [f"segment_{segment}_rows" for segment in [1, 2, 3, 4]]
    summary["dominant_segment"] = (
        summary[dominant_row_cols].idxmax(axis=1).str.extract(r"segment_(\d+)_rows").astype(int)
    )
    summary["dominant_share_pct"] = summary[
        [f"segment_{segment}_share_pct" for segment in [1, 2, 3, 4]]
    ].max(axis=1)

    summary = summary.sort_values(["rows", "entity_value"], ascending=[False, True]).reset_index(drop=True)
    return summary


def build_figure(summary, entity_label):
    top = summary.head(20).copy().iloc[::-1]
    segment_count_distribution = (
        summary["segment_count"].value_counts().sort_index().reindex([1, 2, 3, 4], fill_value=0)
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            f"<b>Top 20 {entity_label}s by Rows and Segment Mix</b>",
            f"<b>{entity_label}s by Number of Segments Present</b>",
        ),
        horizontal_spacing=0.12,
    )

    for segment in [1, 2, 3, 4]:
        fig.add_trace(
            go.Bar(
                x=top[f"segment_{segment}_rows"],
                y=top["entity_value"],
                orientation="h",
                marker_color=SEGMENT_COLORS[segment],
                name=f"Segment {segment}",
                hovertemplate=(
                    f"<b>{entity_label}:</b> %{{y}}"
                    f"<br><b>Segment {segment} rows:</b> %{{x:,}}<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

    fig.add_trace(
        go.Bar(
            x=[str(value) for value in segment_count_distribution.index],
            y=segment_count_distribution.values,
            marker_color=PRIMARY,
            text=[format_int(value) for value in segment_count_distribution.values],
            textposition="outside",
            hovertemplate="<b>Segments present:</b> %{x}<br><b>Count:</b> %{y:,}<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    apply_layout(fig)
    fig.update_xaxes(title_text="Rows", row=1, col=1)
    fig.update_yaxes(title_text=entity_label, row=1, col=1)
    fig.update_xaxes(title_text="Segments present", row=1, col=2)
    fig.update_yaxes(title_text=f"Number of {entity_label.lower()}s", row=1, col=2)
    return fig


def generate_report(config, df):
    entity_col = config["entity_col"]
    entity_label = config["entity_label"]

    summary = prepare_summary(df, entity_col)
    safe_write_csv(summary, config["summary_csv"], f"{entity_label} vs segment summary")

    fig = build_figure(summary, entity_label)

    total_values = len(summary)
    one_segment = int((summary["segment_count"] == 1).sum())
    multi_segment = int((summary["segment_count"] > 1).sum())
    four_segments = int((summary["segment_count"] == 4).sum())
    mean_segment_count = summary["segment_count"].mean()
    top_value = summary.iloc[0]

    top_table = summary.head(12).copy()
    top_table["rows"] = top_table["rows"].map(format_int)
    top_table["dominant_segment"] = top_table["dominant_segment"].map(lambda value: f"Segment {int(value)}")
    for column in [
        "dominant_share_pct",
        "segment_1_share_pct",
        "segment_2_share_pct",
        "segment_3_share_pct",
        "segment_4_share_pct",
    ]:
        top_table[column] = top_table[column].map(lambda value: format_pct(value, 1))

    table_html = render_table(
        top_table[
            [
                "entity_value",
                "rows",
                "segment_count",
                "dominant_segment",
                "dominant_share_pct",
                "segment_1_share_pct",
                "segment_2_share_pct",
                "segment_3_share_pct",
                "segment_4_share_pct",
            ]
        ],
        entity_label,
    )

    stats = [
        ("Rows Analyzed", format_int(len(df)), False),
        (f"Distinct {entity_label}s", format_int(total_values), False),
        ("One-Segment Values", format_int(one_segment), False),
        ("Multi-Segment Values", format_int(multi_segment), False),
        ("Values in All 4 Segments", format_int(four_segments), False),
        ("Average Segments per Value", f"{mean_segment_count:.2f}", False),
        (f"Top {entity_label}", str(top_value["entity_value"]), True),
        ("Top Value Rows", format_int(top_value["rows"]), False),
    ]

    multi_share_pct = multi_segment / total_values * 100
    one_share_pct = one_segment / total_values * 100
    top_dominant_segment = int(top_value["dominant_segment"])
    top_dominant_share = top_value["dominant_share_pct"]

    observations = [
        f"{format_int(multi_segment)} of {format_int(total_values)} {entity_label.lower()}s ({format_pct(multi_share_pct, 2)}) appear in more than one segment.",
        f"{format_int(one_segment)} {entity_label.lower()}s ({format_pct(one_share_pct, 2)}) appear in only one segment.",
        f"The largest {entity_label.lower()} is {top_value['entity_value']} with {format_int(top_value['rows'])} rows, and its dominant segment is Segment {top_dominant_segment} with {format_pct(top_dominant_share, 2)} of that value's rows.",
        f"This means Segment is not a fixed {entity_label.lower()} attribute in many cases, so later performance comparisons should adjust for segment mix rather than assume a single built-in segment profile.",
    ]

    subtitle = (
        f"<strong>Dataset:</strong> {escape(DATASET_LABEL)} &nbsp;|&nbsp; "
        f"<strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp; "
        f"<strong>Scope:</strong> {escape(config['scope_text'])}"
    )

    html_content = build_page(
        title=config["title"],
        subtitle=subtitle,
        stats_html=render_stats(stats),
        figure_html=fig.to_html(full_html=False, include_plotlyjs="cdn"),
        table_html=table_html,
        observations_html=render_observations(observations),
    )
    safe_write_text(config["html_path"], html_content, "HTML report")


def main():
    df = pd.read_csv(DATASET_PATH, usecols=["UserCardBIN", "Channel", "Segment"], dtype={"UserCardBIN": str, "Channel": str})
    df = df.dropna(subset=["UserCardBIN", "Channel", "Segment"]).copy()
    df["Segment"] = pd.to_numeric(df["Segment"], errors="coerce")
    df = df.dropna(subset=["Segment"]).copy()
    df["Segment"] = df["Segment"].astype(int)

    for config in CONFIGS:
        generate_report(config, df[[config["entity_col"], "Segment"]].copy())


if __name__ == "__main__":
    main()
