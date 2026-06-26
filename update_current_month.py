import os
import json
import gzip
import time
from datetime import datetime

# ============================================
# CONFIG
# ============================================

DATA_DIR = "data"
MONTHLY_DIR = "monthly"
COMPRESS_LEVEL = 6

os.makedirs(MONTHLY_DIR, exist_ok=True)


# ============================================
# HELPERS
# ============================================

def load_gzip_json(filepath):
    """Safely load gzip json"""
    try:
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed reading {filepath}: {e}")
        return None


def save_gzip_json(filepath, data):
    """Save gzip json"""
    try:
        with gzip.open(
                filepath,
                "wt",
                encoding="utf-8",
                compresslevel=COMPRESS_LEVEL
        ) as f:
            json.dump(data, f, separators=(",", ":"))
        return True
    except Exception as e:
        print(f"[ERROR] Failed writing {filepath}: {e}")
        return False


def is_valid_candle(candle):
    """
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

    if len(date) != 10:
        return False

    if date[4] != "-" or date[7] != "-":
        return False

    return True


def get_current_month():
    return datetime.now().strftime("%Y-%m")


# ============================================
# MAIN
# ============================================

def update_current_month():

    start = time.time()

    print("=" * 60)
    print("DAILY MONTHLY UPDATE STARTED")
    print("=" * 60)
    print()

    current_month = get_current_month()
    monthly_file = os.path.join(
        MONTHLY_DIR,
        f"{current_month}.json.gz"
    )

    # Load existing current month file if present
    if os.path.exists(monthly_file):

        monthly_data = load_gzip_json(monthly_file)

        if monthly_data is None:
            monthly_data = {}

        print(f"[OK] Loaded existing {current_month}.json.gz")

    else:
        monthly_data = {}
        print(f"[NEW] Creating {current_month}.json.gz")

    print()

    # Get all stock files
    files = sorted(
        f for f in os.listdir(DATA_DIR)
        if f.endswith(".json.gz")
    )

    total_files = len(files)

    updated = 0
    skipped = 0
    no_change = 0

    print(f"Scanning {total_files} stock files...")
    print()

    # ============================================
    # READ LAST CANDLE FROM EACH STOCK
    # ============================================

    for idx, filename in enumerate(files, 1):

        symbol = filename.replace(".json.gz", "")
        filepath = os.path.join(DATA_DIR, filename)

        candles = load_gzip_json(filepath)

        if not candles:
            skipped += 1
            continue

        # Take only last candle
        last_candle = candles[-1]

        if not is_valid_candle(last_candle):
            skipped += 1
            continue

        candle_date = last_candle[0]
        candle_month = candle_date[:7]

        # Ignore old month candles
        if candle_month != current_month:
            continue

        # Existing monthly candles for stock
        existing = monthly_data.get(symbol, [])

        existing_dates = {c[0] for c in existing}

        # Update only if new date missing
        if candle_date not in existing_dates:

            existing.append(last_candle)

            # Keep sorted
            existing.sort(key=lambda x: x[0])

            monthly_data[symbol] = existing

            updated += 1

        else:
            no_change += 1

        if idx % 50 == 0 or idx == total_files:
            print(
                f"[PROGRESS] "
                f"{idx}/{total_files} "
                f"| Updated {updated}"
            )

    print()
    print("Saving current month file...")
    print()

    # ============================================
    # SAVE UPDATED MONTH FILE
    # ============================================

    changed = False

    if updated > 0:

        success = save_gzip_json(
            monthly_file,
            monthly_data
        )

        if success:

            size_mb = os.path.getsize(monthly_file) / (1024 * 1024)

            print(
                f"[OK] Saved {current_month}.json.gz | "
                f"{len(monthly_data)} stocks | "
                f"{size_mb:.2f} MB"
            )

            changed = True

    else:
        print("[INFO] No changes detected. No write needed.")

    # ============================================
    # SUMMARY
    # ============================================

    elapsed = time.time() - start

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"Stock files scanned  : {total_files}")
    print(f"Updated stocks       : {updated}")
    print(f"No change            : {no_change}")
    print(f"Skipped              : {skipped}")

    print()

    print(f"Current month file   : {current_month}.json.gz")
    print(f"Execution time       : {elapsed:.2f} sec")

    print("=" * 60)

    return changed


# ============================================
# ENTRY
# ============================================

if __name__ == "__main__":

    changed = update_current_month()

    # Always success for GitHub Actions
    # git commit step handles "no changes"

    exit(0)