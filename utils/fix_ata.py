# fix_ata.py

from app import create_app, db
from app.models import WarehouseStock
from datetime import date

app = create_app()

with app.app_context():
    updated = 0

    for item in WarehouseStock.query.all():
        ata_raw = item.ata

        if isinstance(ata_raw, str):
            parts = ata_raw.strip().split(".")
            if len(parts) == 2:
                try:
                    day = int(parts[0])
                    month = int(parts[1])
                    item.ata = date(2025, month, day)
                    updated += 1
                except Exception as e:
                    print(f"❌ Skipped string {ata_raw} – {e}")

        elif isinstance(ata_raw, float):
            try:
                day = int(ata_raw)
                month = int(round((ata_raw - day) * 100))
                item.ata = date(2025, month, day)
                updated += 1
            except Exception as e:
                print(f"❌ Skipped float {ata_raw} – {e}")

    db.session.commit()
    print(f"✅ ATA cleanup complete – {updated} records updated.")
