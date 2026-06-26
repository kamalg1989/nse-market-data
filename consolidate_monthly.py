import os
import json
import gzip
import time
from collections import defaultdict

# ============================================
# CONFIG
# ============================================

DATA_DIR = "data"
OUTPUT_DIR = "monthly"
COMPRESS_LEVEL = 6      # faster than 9, similar compression

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================
# HELPERS
# ============================================

def load_gzip_json(filepath):
    """Safely load gzip JSON"""
    try:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed reading {filepath}: {e}")
        return None


def save_gzip_json(filepath, data):
    """Save compressed JSON"""
    try:
        with gzip.open(
                filepath,
                "wt",
                encoding="utf-8",
                compresslevel=COMPRESS_LEVEL
        ) as f:
            json.dump(
                data,
                f,
                separators=(",", ":")   # compact JSON
            )
        return True
    except Exception as e:
        print(f"[ERROR] Failed writing {filepath}: {e}")
        return False


def is_valid_candle(candle):
    """
    Fast validation only.

    Expected:
    ["2026-06-25", open, high, low, close, volume]
    """
    if not isinstance(candle, list):
        return False

    if len(candle) < 6:
        return False

    date = candle[0]

    if not isinstance(date, str):
        return False

    # Cheap date check instead of datetime.strptime()
    if len(date) != 10:
        return False

    if date[4] != "-" or date[7] != "-":
        return False

    return True


def get_folder_size(folder):
    """Calculate folder size"""
    total = 0

    if not os.path.exists(folder):
        return 0

    for file in os.listdir(folder):
        filepath = os.path.join(folder, file)

        if os.path.isfile(filepath):
            total += os.path.getsize(filepath)

    return total


# ============================================
# MAIN
# ============================================

def consolidate_monthly():

    start_time = time.time()

    print("=" * 60)
    print("MONTHLY DATA CONSOLIDATION STARTED")
    print("=" * 60)
    print()

    # Structure:
    # {
    #   "2026-06": {
    #       "RELIANCE": [...],
    #       "TCS": [...]
    #   }
    # }

    monthly_data = defaultdict(dict)

    files = sorted(
        f for f in os.listdir(DATA_DIR)
        if f.endswith(".json.gz")
    )

    total_files = len(files)
    processed = 0
    skipped = 0
    invalid_candles = 0
    total_candles = 0

    print(f"Found {total_files} stock files")
    print()

    # ============================================
    # READ STOCK FILES
    # ============================================

    for idx, filename in enumerate(files, 1):

        symbol = filename.replace(".json.gz", "")
        filepath = os.path.join(DATA_DIR, filename)

        candles = load_gzip_json(filepath)

        if candles is None:
            skipped += 1
            print(f"[SKIP] {symbol}")
            continue

        stock_months = defaultdict(list)

        for candle in candles:

            if not is_valid_candle(candle):
                invalid_candles += 1
                continue

            month_key = candle[0][:7]

            stock_months[month_key].append(candle)
            total_candles += 1

        # Merge stock into month bucket
        for month, month_candles in stock_months.items():
            monthly_data[month][symbol] = month_candles

        processed += 1

        # Show progress every 25 files
        if idx % 25 == 0 or idx == total_files:

            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0

            remaining = total_files - idx
            eta = remaining / rate if rate > 0 else 0

            print(
                f"[PROGRESS] "
                f"{processed}/{total_files} "
                f"| ETA {eta:.0f}s"
            )

    print()
    print("=" * 60)
    print("WRITING MONTHLY FILES")
    print("=" * 60)
    print()

    # ============================================
    # WRITE MONTHLY FILES
    # ============================================

    months_written = 0

    for month in sorted(monthly_data.keys()):

        output_file = os.path.join(
            OUTPUT_DIR,
            f"{month}.json.gz"
        )

        data = monthly_data[month]

        if save_gzip_json(output_file, data):

            size_mb = os.path.getsize(output_file) / (1024 * 1024)

            print(
                f"[OK] {month:<10} | "
                f"{len(data):>4} stocks | "
                f"{size_mb:>6.2f} MB"
            )

            months_written += 1

    # ============================================
    # SUMMARY
    # ============================================

    original_size = get_folder_size(DATA_DIR)
    new_size = get_folder_size(OUTPUT_DIR)

    if original_size > 0:
        space_saved = (
                              1 - (new_size / original_size)
                      ) * 100
    else:
        space_saved = 0

    elapsed = time.time() - start_time

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"Files found          : {total_files}")
    print(f"Files processed      : {processed}")
    print(f"Files skipped        : {skipped}")
    print(f"Total candles        : {total_candles:,}")
    print(f"Invalid candles      : {invalid_candles}")
    print(f"Months created       : {months_written}")

    print()

    print(f"Original size        : {original_size / (1024**2):.2f} MB")
    print(f"Monthly size         : {new_size / (1024**2):.2f} MB")
    print(f"Space saved          : {space_saved:.2f}%")

    print()

    print(f"Execution time       : {elapsed:.2f} sec")

    print("=" * 60)
    print("DONE")
    print("=" * 60)


# ============================================
# ENTRY
# ============================================

if __name__ == "__main__":
    consolidate_monthly()