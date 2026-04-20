"""
Data ingestion for glow25-conversion-benchmarker.
Tries Kaggle datasets in priority order, standardises schema,
adds Glow25-specific dimensions (country, device, channel).
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "events_clean.csv"

KAGGLE_CREDS = Path.home() / ".kaggle" / "kaggle.json"


def check_kaggle_creds():
    if not KAGGLE_CREDS.exists():
        print(
            "\nKaggle credentials not found.\n"
            "Go to https://www.kaggle.com/settings → API → Create New Token.\n"
            "Save the downloaded kaggle.json to ~/.kaggle/kaggle.json and re-run.\n"
        )
        sys.exit(1)


def try_option_a():
    """ecommerce-behavior-data-from-multi-category-store — real clickstream, ideal."""
    import kaggle
    print("Trying Option A: mkechinov/ecommerce-behavior-data-from-multi-category-store")
    kaggle.api.dataset_download_files(
        "mkechinov/ecommerce-behavior-data-from-multi-category-store",
        path=str(RAW_DIR),
        unzip=True,
    )
    csv_path = RAW_DIR / "2019-Nov.csv"
    if not csv_path.exists():
        raise FileNotFoundError("2019-Nov.csv not found after download")
    df = pd.read_csv(csv_path, nrows=500_000)
    # columns we need: event_time, event_type, user_id, price (product_id optional)
    required = {"event_time", "event_type", "user_id"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns. Got: {list(df.columns)}")
    return df


def try_option_b():
    """retailrocket/ecommerce-dataset — fallback."""
    import kaggle
    print("Trying Option B: retailrocket/ecommerce-dataset")
    kaggle.api.dataset_download_files(
        "retailrocket/ecommerce-dataset",
        path=str(RAW_DIR),
        unzip=True,
    )
    csv_path = RAW_DIR / "events.csv"
    if not csv_path.exists():
        raise FileNotFoundError("events.csv not found after download")
    df = pd.read_csv(csv_path)
    df = df.rename(columns={
        "event": "event_type",
        "visitorid": "user_id",
        "timestamp": "event_time",
    })
    df["event_type"] = df["event_type"].replace({
        "addtocart": "cart",
        "transaction": "purchase",
    })
    return df


def try_option_c():
    """carrie1/ecommerce-purchase-history-from-electronics-store — last resort."""
    import kaggle
    print("Trying Option C: carrie1/ecommerce-purchase-history-from-electronics-store")
    kaggle.api.dataset_download_files(
        "carrie1/ecommerce-purchase-history-from-electronics-store",
        path=str(RAW_DIR),
        unzip=True,
    )
    csv_path = RAW_DIR / "kz.csv"
    if not csv_path.exists():
        # some versions of this dataset have a different filename
        csvs = list(RAW_DIR.glob("*.csv"))
        if not csvs:
            raise FileNotFoundError("No CSV found in data/raw/ after download")
        csv_path = csvs[0]
        print(f"  Using {csv_path.name} (first csv found)")
    df = pd.read_csv(csv_path, nrows=500_000)
    # try to normalise whatever columns exist
    col_map = {}
    for col in df.columns:
        lc = col.lower()
        if "event" in lc and "type" in lc:
            col_map[col] = "event_type"
        elif "time" in lc or "date" in lc:
            col_map[col] = "event_time"
        elif "user" in lc or "visitor" in lc or "session" in lc:
            col_map[col] = "user_id"
    df = df.rename(columns=col_map)
    if "event_type" in df.columns:
        df["event_type"] = df["event_type"].replace({
            "addtocart": "cart",
            "transaction": "purchase",
            "view": "view",
        })
    return df


def standardise(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["event_type"].isin(["view", "cart", "purchase"])].copy()
    df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce", utc=True)
    df = df.dropna(subset=["event_time", "user_id", "event_type"])
    df["user_id"] = df["user_id"].astype(str)

    rng = np.random.default_rng(seed=42)
    n = len(df)

    df["country"] = rng.choice(
        ["DE", "NL", "BE", "FR"], size=n, p=[0.45, 0.25, 0.15, 0.15]
    )
    df["device"] = rng.choice(
        ["mobile", "desktop", "tablet"], size=n, p=[0.62, 0.32, 0.06]
    )
    df["channel"] = rng.choice(
        ["organic_search", "paid_social", "email", "direct", "paid_search", "influencer"],
        size=n,
        p=[0.28, 0.22, 0.18, 0.12, 0.12, 0.08],
    )
    return df


def validate(df: pd.DataFrame):
    errors = []
    if len(df) < 100_000:
        errors.append(f"Only {len(df):,} rows — expected > 100,000. Try a different dataset option manually.")
    for evt in ["view", "cart", "purchase"]:
        if evt not in df["event_type"].values:
            errors.append(f"Missing event type: '{evt}'")
    for col in ["country", "device", "channel"]:
        if col not in df.columns or df[col].isnull().all():
            errors.append(f"Column '{col}' is missing or all null")
    null_check = df[["event_time", "user_id"]].isnull().sum()
    for col, n in null_check.items():
        if n > 0:
            errors.append(f"{n:,} nulls in '{col}' — fix the ingest step")
    if errors:
        print("\nValidation failed:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("\nValidation passed.")


def main():
    check_kaggle_creds()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = None
    for attempt in [try_option_a, try_option_b, try_option_c]:
        try:
            df = attempt()
            print(f"  Download succeeded.")
            break
        except Exception as e:
            print(f"  Failed: {e}")

    if df is None:
        print(
            "\nAll three dataset options failed. Check your Kaggle credentials "
            "and internet connection, then try downloading one of the datasets manually:\n"
            "  Option A: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store\n"
            "  Option B: https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset\n"
        )
        sys.exit(1)

    print("Standardising schema and adding Glow25 dimensions...")
    df = standardise(df)

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(df):,} rows to {OUTPUT_FILE}")
    print("\nEvent breakdown:")
    print(df["event_type"].value_counts().to_string())
    print("\nCountry breakdown:")
    print(df["country"].value_counts().to_string())

    validate(df)
    print("\nReady. Run the notebook or Streamlit app next.")


if __name__ == "__main__":
    main()
