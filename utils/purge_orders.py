# purge_orders.py — clear business data (orders across tabs), keep users.
import re, sqlite3
from pathlib import Path

DB_PATH = Path("instance") / "supply_tracker.db"

# Name patterns to match business-data tables (case-insensitive)
PATTERNS = [
    r"\border\b",          # dashboard orders
    r"warehouse",          # warehouse* tables
    r"deliver",            # delivered / deliveries
    r"stockreport",        # stockreport / stock_report / entries
]

def main():
    if not DB_PATH.exists():
        raise SystemExit(f"❌ DB not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH.as_posix())
    cur = conn.cursor()
    cur.execute("""
      SELECT name FROM sqlite_master
      WHERE type='table' AND name NOT LIKE 'sqlite_%'
      ORDER BY name;
    """)
    all_tables = [r[0] for r in cur.fetchall()]
    rx = [re.compile(p, re.I) for p in PATTERNS]
    targets = [t for t in all_tables if any(r.search(t) for r in rx)]

    if not targets:
        print("ℹ️ No matching tables found. Adjust PATTERNS in the script.")
        return

    print("Will clear tables:")
    for t in targets: print(f" - {t}")

    cur.execute("PRAGMA foreign_keys=OFF;")
    for t in targets:
        try:
            cur.execute(f'DELETE FROM "{t}";')
        except Exception as e:
            print(f" ! Skip {t}: {e}")

    # reset AUTOINCREMENT counters if present
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
        if cur.fetchone():
            qmarks = ",".join(["?"] * len(targets))
            cur.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({qmarks});", tuple(targets))
    except Exception:
        pass

    conn.commit()
    try:
        cur.execute("VACUUM;")
    except Exception:
        pass
    conn.close()

    print("✅ Purge complete.")

if __name__ == "__main__":
    main()
