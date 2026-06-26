import os, json, gzip, time
from datetime import datetime, timedelta
from dhanhq import dhanhq
from collections import defaultdict

DATA_DIR = "data"
MONTHLY_DIR = "monthly"
COMPRESS_LEVEL = 6

DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")

SECURITY_IDS = {
    "RELIANCE": 5696, "TCS": 3019, "HDFCBANK": 2038, "ICICIBANK": 1113,
    "INFY": 1594, "KOTAKBANK": 4712, "SBIN": 4119, "BAJAJFINSV": 10584,
    "LT": 2099, "MARUTI": 4884, "AXISBANK": 1477, "WIPRO": 3428,
    "ONGC": 857, "SUNPHARMA": 3005, "BHARTIARTL": 2714, "HINDUNILVR": 4273,
    "TITAN": 4963, "NESTLEIND": 4897, "POWERGRID": 5642, "ITC": 1632,
}

os.makedirs(MONTHLY_DIR, exist_ok=True)

def load_gzip_json(filepath):
    try:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] {filepath}: {e}")
        return None

def save_gzip_json(filepath, data):
    try:
        with gzip.open(filepath, "wt", encoding="utf-8", compresslevel=COMPRESS_LEVEL) as f:
            json.dump(data, f, separators=(",", ":"))
        return True
    except Exception as e:
        print(f"[ERROR] {filepath}: {e}")
        return False

def dhan_candle_to_array(c):
    try:
        return [c.get("date") or c.get("candle_datetime", ""),
                float(c.get("open", 0)), float(c.get("high", 0)),
                float(c.get("low", 0)), float(c.get("close", 0)),
                int(c.get("volume", 0))]
    except: return None

def initialize_dhan():
    if not DHAN_CLIENT_ID or not DHAN_ACCESS_TOKEN:
        print("[ERROR] Dhan credentials not set"); return None
    try:
        return dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
    except Exception as e:
        print(f"[ERROR] Dhan init: {e}"); return None

def fetch_dhan(dhan, symbol, days=7):
    sid = SECURITY_IDS.get(symbol)
    if not sid: return []
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        candles = dhan.historical_candle_data(
            security_id=sid, exchange_token="NSE",
            from_date=from_date.strftime("%Y-%m-%d"),
            to_date=to_date.strftime("%Y-%m-%d"), interval="1D")
        if not candles or "data" not in candles: return []
        return [dhan_candle_to_array(c) for c in candles["data"] if dhan_candle_to_array(c)]
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}"); return []

def update():
    start = time.time()
    print("="*60)
    print("DHAN API MONTHLY UPDATE")
    print("="*60 + "\n")

    dhan = initialize_dhan()
    if not dhan: return False

    month = datetime.now().strftime("%Y-%m")
    mfile = os.path.join(MONTHLY_DIR, f"{month}.json.gz")
    mdata = load_gzip_json(mfile) if os.path.exists(mfile) else {}
    print(f"[{'OK' if os.path.exists(mfile) else 'NEW'}] {month}.json.gz\n")

    updated, skipped, failed = 0, 0, 0
    for idx, sym in enumerate(SECURITY_IDS.keys(), 1):
        candles = fetch_dhan(dhan, sym)
        if not candles: failed += 1; continue
        month_candles = [c for c in candles if c[0][:7] == month]
        if not month_candles: skipped += 1; continue

        exist = mdata.get(sym, [])
        exist_dates = {c[0] for c in exist}
        new = [c for c in month_candles if c[0] not in exist_dates]
        if new:
            exist.extend(new)
            exist.sort(key=lambda x: x[0])
            mdata[sym] = exist
            updated += 1

        if idx % 5 == 0 or idx == len(SECURITY_IDS):
            print(f"[PROGRESS] {idx}/{len(SECURITY_IDS)} | Updated: {updated}")
        time.sleep(0.5)

    if updated > 0:
        if save_gzip_json(mfile, mdata):
            size = os.path.getsize(mfile) / (1024 * 1024)
            print(f"\n[OK] Saved {month}.json.gz | {len(mdata)} stocks | {size:.2f} MB")
    else:
        print("\n[INFO] No changes")

    elapsed = time.time() - start
    print(f"\nProcessed: {len(SECURITY_IDS)} | Updated: {updated} | Skipped: {skipped} | Failed: {failed}")
    print(f"Time: {elapsed:.2f}s\n" + "="*60)
    return updated > 0

if __name__ == "__main__":
    update()
