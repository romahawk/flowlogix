# backup.py — SQLite backup + CSV dump for Supply Tracker
# Run:  python backup.py            (backup + CSVs)
#       python backup.py --no-csv   (backup only)
#       python backup.py --db instance/supply_tracker.db
#       python backup.py --out backups

import argparse
import os
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

try:
    import pandas as pd  # optional; used for CSV export
    HAVE_PANDAS = True
except Exception:
    HAVE_PANDAS = False


def detect_db_path(default: Path) -> Path:
    """Try to read SQLALCHEMY_DATABASE_URI, else return default."""
    uri = os.environ.get("SQLALCHEMY_DATABASE_URI", "").strip()
    if not uri:
        return default

    # Support forms like sqlite:///instance/supply_tracker.db
    m = re.match(r"sqlite:/*(.+)", uri)
    if m:
        # Normalize slashes and remove leading slashes that indicate absolute paths
        p = Path(m.group(1))
        return p
    # Fallback if not sqlite
    return default


def sqlite_consistent_backup(src_db: Path, dst_db: Path):
    """Create a consistent SQLite backup using the backup API."""
    dst_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(src_db.as_posix()) as src, sqlite3.connect(dst_db.as_posix()) as dst:
        src.backup(dst)
    # Preserve timestamps like copy2
    try:
        shutil.copystat(src_db, dst_db)
    except Exception:
        pass


def list_user_tables(db_path: Path):
    """Return non-internal table names."""
    with sqlite3.connect(db_path.as_posix()) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        return [r[0] for r in cur.fetchall()]


def export_all_tables_to_csv(db_path: Path, out_dir: Path):
    if not HAVE_PANDAS:
        print("ℹ️  pandas not installed: skipping CSV export. Run `pip install pandas` to enable.")
        return

    import pandas as pd  # for type checkers

    out_dir.mkdir(parents=True, exist_ok=True)
    tables = list_user_tables(db_path)
    if not tables:
        print("ℹ️  No user tables found to export.")
        return

    with sqlite3.connect(db_path.as_posix()) as conn:
        for t in tables:
            safe = re.sub(r"[^A-Za-z0-9_\-]+", "_", t)
            csv_path = out_dir / f"{safe}.csv"
            try:
                df = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
                df.to_csv(csv_path, index=False)
                print(f"   • {t} → {csv_path}")
            except Exception as e:
                print(f"   ! Failed to export {t}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Backup Supply Tracker SQLite DB (+ CSV export).")
    parser.add_argument("--db", type=str, default=None, help="Path to SQLite DB file.")
    parser.add_argument("--out", type=str, default="backups", help="Backup output directory.")
    parser.add_argument("--no-csv", action="store_true", help="Disable CSV export.")
    args = parser.parse_args()

    project_root = Path(__file__).parent
    default_db = project_root / "instance" / "supply_tracker.db"
    db_path = Path(args.db) if args.db else detect_db_path(default_db)
    out_dir = project_root / args.out

    if not db_path.exists():
        raise SystemExit(f"❌ Database not found at: {db_path}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_db = out_dir / f"supply_tracker_{ts}.db"
    csv_dir = out_dir / f"csv_{ts}"

    print(f"📦 Backing up DB from: {db_path}")
    sqlite_consistent_backup(db_path, backup_db)
    print(f"✅ DB backup created: {backup_db}")

    if not args.no_csv:
        print(f"🧾 Exporting tables to CSV: {csv_dir}")
        export_all_tables_to_csv(backup_db, csv_dir)
        print("✅ CSV export complete.")

    print("🎉 Done.")


if __name__ == "__main__":
    main()
