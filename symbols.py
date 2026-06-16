import requests
import pandas as pd
from io import StringIO


def get_nse_symbols():
    # Nifty 500 constituents CSV
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

    r = requests.get(url, timeout=30)

    df = pd.read_csv(StringIO(r.text))

    symbols = []

    for s in df["Symbol"].tolist():
        symbols.append(f"{s}.NS")

    return symbols