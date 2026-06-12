# Exclusion Challenge

This repository contains the analysis subset of a larger working project for evaluating whether specific `UserCardBIN`-`Channel` combinations should be excluded from deposit routing.

The core problem is not to rank pairs by raw fraud or raw approval alone. The analysis tries to control for:

- transaction volume
- fraud-label delay
- customer segment mix

## Repository scope

Only the analysis-related folders are included here:

- `Data_Prep`
- `univariate_reports`
- `bivariate_reports`
- `multivariate_reports`
- `decision_design`

Generated HTML reports and CSV outputs are committed alongside the scripts that produced them.

## Problem framing

Working interpretation of the transaction flow:

1. A customer initiates a deposit transaction.
2. The company routes the transaction to a processing `Channel`.
3. The customer card determines the `UserCardBIN`.
4. The channel returns the immediate decision through `Approved`.
5. The banking system later determines the fraud outcome through `Fraud`.
6. `FraudDetectionDate` records that later fraud identification when available.

This makes the decision unit a `UserCardBIN`-`Channel` pair, but that pair has to be judged carefully because:

- most pairs have very low volume
- fraud labels mature after the transaction date
- approval and fraud differ materially by `Segment`

## Repository structure

### `Data_Prep`

Input data and cleaning scripts.

- `March_Deposits.csv`, `April_Deposits.csv`, `May_Deposits.csv`
- `unify_dataset.py`: stacks the three monthly files into `combined_deposits.csv`
- `data_quality_checks.py`: validates and cleans the unified file into `combined_deposits_cleaned.csv`

Quality-check outputs:

- `fraud_0_with_detection_date.csv`
- `approved_0_fraud_1.csv`
- `fraud_1_without_detection_date.csv`
- `fraud_detection_before_transaction.csv`

### `univariate_reports`

Single-variable exploratory reports.

- `generate_univariate_reports.py`
- `index.html` as the entry page

Variables covered:

- `Channel`
- `UserCardBIN`
- `Approved`
- `Fraud`
- `TransactionDate`
- `FraudDetectionDate`
- `Segment`

### `bivariate_reports`

Two-variable analysis used to establish the main structural controls:

- fraud maturity over time
- fraud detection delay
- segment effects on approval and fraud
- channel and BIN outcome distributions
- long-tail behavior of `BIN`-`Channel` nodes

### `multivariate_reports`

Sensitivity analysis for fraud maturity assumptions.

- `segment_vs_fraud_maturity_sensitivity.py`

### `decision_design`

Pair-level decision-support outputs for `UserCardBIN`-`Channel` nodes.

This folder contains:

- segment-adjusted approval tables
- maturity-aware fraud tables
- approval-vs-fraud gap views
- DBSCAN and HDBSCAN clustering outputs
- graph-based views of high-volume concern edges
- a low-volume decline-streak rule by segment

## Data pipeline

### 1. Prepare the monthly files

Before unifying the data:

- in `May_Deposits.csv`, rename the `BIN` column to `UserCardBIN`

### 2. Build the unified dataset

```powershell
python Data_Prep/unify_dataset.py
```

Output:

- `Data_Prep/combined_deposits.csv`

### 3. Run quality checks and cleaning

```powershell
python Data_Prep/data_quality_checks.py
```

Outputs:

- `Data_Prep/combined_deposits_cleaned.csv`
- the four QA exception files listed above

### 4. Generate univariate reports

```powershell
python univariate_reports/generate_univariate_reports.py
```

Main output:

- `univariate_reports/index.html`

### 5. Run the bivariate and decision-design scripts

Scripts can be executed individually from their folders, for example:

```powershell
python bivariate_reports/fraud_vs_transactiondate_analysis.py
python bivariate_reports/fraud_detection_delay_analysis.py
python bivariate_reports/segment_vs_approved_analysis.py
python bivariate_reports/segment_vs_fraud_analysis.py
python bivariate_reports/bin_channel_distribution_analysis.py

python multivariate_reports/segment_vs_fraud_maturity_sensitivity.py

python decision_design/bin_channel_segment_approval.py
python decision_design/bin_channel_segment_approval_analysis.py
python decision_design/bin_channel_segment_fraud.py
python decision_design/bin_channel_segment_mature_rates.py
python decision_design/bin_channel_segment_fraud_analysis.py
python decision_design/bin_channel_approval_fraud_gap_analysis.py
python decision_design/bin_channel_approval_fraud_cluster_analysis.py
python decision_design/bin_channel_approval_fraud_hdbscan_analysis.py
python decision_design/bin_channel_graph_analysis.py
python decision_design/decline_streak_p90_analysis.py
```

## Environment

The scripts use standard Python plus a small analysis stack:

- `pandas`
- `numpy`
- `plotly`
- `scikit-learn`
- `hdbscan`

Install example:

```powershell
pip install pandas numpy plotly scikit-learn hdbscan
```

## Notes

- This repository is a curated public subset of a larger local workspace.
- The large CSV files in `Data_Prep` are intentionally included because the analysis outputs depend on them.
- GitHub will warn about the size of `combined_deposits.csv` and `combined_deposits_cleaned.csv`, but both remain below the hard `100 MB` file limit.
