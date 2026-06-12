from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
MONTH_FILES = [
    ("March", "March_Deposits.csv"),
    ("April", "April_Deposits.csv"),
    ("May", "May_Deposits.csv"),
]
DATASET_LABEL = "March, April, and May deposit files (combined)"
OUTPUT_PATH = ROOT_DIR / "combined_deposits.csv"


def load_dataset():
    frames = []
    for _, file_name in MONTH_FILES:
        frame = pd.read_csv(ROOT_DIR / file_name)
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def main():
    df = load_dataset()
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Combined dataset saved to {OUTPUT_PATH}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {', '.join(df.columns)}")


if __name__ == "__main__":
    main()
