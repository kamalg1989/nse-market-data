import os
import time
import json
import gzip
import yfinance as yf
# from collections import defaultdict
from symbols import get_nse_symbols

symbols = get_nse_symbols()
# bucket = defaultdict(dict)

os.makedirs("data", exist_ok=True)

count = 0

for ticker in symbols:

    try:
        print("Downloading:", ticker)

        df = yf.download(
            ticker,
            period="15y",
            interval="1d",
            progress=False,
            auto_adjust=False
        )
        # Flatten MultiIndex columns returned by yfinance
        if df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)



        if df.empty:
            continue

        symbol = ticker.replace(".NS", "")

        candles = []

        for idx, row in df.iterrows():

            candles.append([
                idx.strftime("%Y-%m-%d"),
                round(float(row["Open"]), 2),
                round(float(row["High"]), 2),
                round(float(row["Low"]), 2),
                round(float(row["Close"]), 2),
                int(row["Volume"])
            ])

        filename = f"data/{symbol}.json.gz"

        with gzip.open(filename, "wt", encoding="utf-8") as f:
            json.dump(candles, f)

        count += 1

        print("Done:", count)


    except Exception as e:
        print("ERROR:", ticker, e)

print("Finished")