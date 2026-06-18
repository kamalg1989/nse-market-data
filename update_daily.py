import os
import json
import gzip
import pandas as pd
import yfinance as yf
import time
from symbols import get_nse_symbols

DATA_DIR = "data"


def load_existing_data(symbol):
    file = f"{DATA_DIR}/{symbol}.json.gz"

    if not os.path.exists(file):
        return []

    with gzip.open(file, "rt", encoding="utf-8") as f:
        return json.load(f)


def save_data(symbol, candles):
    file = f"{DATA_DIR}/{symbol}.json.gz"
    temp = file + ".tmp"

    with gzip.open(temp, "wt", encoding="utf-8") as f:
        json.dump(candles, f)

    os.replace(temp, file)


def fetch_recent_data(symbol):
    ticker = f"{symbol}.NS"

    print("Fetching:", ticker)

    df = yf.download(
        ticker,
        period="7d",
        auto_adjust=False,
        progress=False
    )

    if df.empty:
        return []

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    candles = []

    for date, row in df.iterrows():
        candles.append([
            date.strftime("%Y-%m-%d"),
            round(float(row["Open"]), 2),
            round(float(row["High"]), 2),
            round(float(row["Low"]), 2),
            round(float(row["Close"]), 2),
            int(row["Volume"])
        ])

    return candles


def main():

    allowed = set([s.replace(".NS", "") for s in get_nse_symbols()])

    updated = 0
    skipped = 0
    count = 0
    total = len(allowed)

    for symbol in allowed:
        count += 1
        print(f"[{count}/{total}] {symbol}")

        try:
            existing = load_existing_data(symbol)

            if len(existing) == 0:
                print("No local file:", symbol)
                time.sleep(1)
                continue

            last_local_date = existing[-1][0]

            print("Checking:", symbol)
            print("Last local:", last_local_date)

            recent = fetch_recent_data(symbol)

            if not recent:
                print("No Yahoo data")
                time.sleep(1)
                continue

            existing_dates = set([x[0] for x in existing])

            new_rows = []

            for candle in recent:
                if candle[0] not in existing_dates:
                    new_rows.append(candle)

            if len(new_rows) == 0:
                print("No new candles")
                skipped += 1
                time.sleep(1)
                continue

            existing.extend(new_rows)
            existing.sort(key=lambda x: x[0])

            save_data(symbol, existing)

            updated += 1
            print("Appended:", len(new_rows), symbol)
            time.sleep(1)

        except Exception as e:
            print("ERROR:", symbol, e)
            time.sleep(1)

    print("Done")
    print("Updated:", updated)
    print("Skipped:", skipped)


if __name__ == "__main__":
    main()