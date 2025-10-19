# app/seed_boot.py
from datetime import date, datetime, timedelta
import os
from typing import Optional, Tuple

def _start_end_of_iso_week(dt: date) -> Tuple[date, date]:
    # ISO week: Monday..Sunday
    start = dt - timedelta(days=(dt.isoweekday() - 1))
    end = start + timedelta(days=6)
    return start, end

def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    try:
        # dd.mm.yy or dd.mm.yyyy
        if "." in s:
            d, m, y = s.split(".")
            y = int(y)
            y = 2000 + y if y < 100 else y
            return date(int(y), int(m), int(d))
        # yyyy-mm-dd
        if "-" in s:
            y, m, d = s.split("-")
            return date(int(y), int(m), int(d))
    except Exception:
        return None
    return None

def _fmt_date(d: Optional[date]) -> Optional[str]:
    if not d: return None
    # store as dd.mm.yy (matches your UI)
    return d.strftime("%d.%m.%y")

def _enforce_timeline_rules(etd_s, eta_s, ata_s) -> Tuple[str, str, Optional[str], str]:
    """
    Returns (etd, eta, ata, transit_status) with rules applied:
      - ETD < ETA <= ATA (if ATA exists; if not, may stay None)
      - status by current ISO week
    """
    today = date.today()
    wk_start, wk_end = _start_end_of_iso_week(today)

    etd = _parse_date(etd_s)
    eta = _parse_date(eta_s)
    ata = _parse_date(ata_s)

    # 1) Ensure ETD & ETA exist and ETD < ETA
    #    If ETA missing but ATA present, use min(ATA, ETD+21) as ETA.
    if etd and not eta and ata:
        eta = min(ata, etd + timedelta(days=21))
    if not etd and eta:
        etd = eta - timedelta(days=7)  # conservative default

    if etd and eta and eta <= etd:
        eta = etd + timedelta(days=7)  # push ETA one week after ETD

    # 2) Ensure ETA <= ATA whenever ATA exists
    if ata and eta and ata < eta:
        ata = eta  # clamp ATA to ETA

    # 3) Compute status using "milestone date" = ATA if exists else ETA
    milestone = ata or eta
    if milestone and milestone < wk_start:
        status = "arrived"
    elif etd and (etd > wk_end) and eta and (eta > wk_end):
        status = "in process"
    elif etd and (etd < wk_start) and eta and (eta > wk_end):
        status = "en route"
    else:
        # fallback heuristics around this/near weeks
        if milestone and wk_start <= milestone <= wk_end:
            status = "en route"
        elif eta and eta > wk_end:
            status = "in process"
        elif etd and etd < wk_start:
            status = "en route"
        else:
            status = "in process"

    return _fmt_date(etd), _fmt_date(eta), _fmt_date(ata), status

def ensure_seed():
    """
    Seed only when there are no orders yet.
    Uses CSV in /data/orders.csv if present, otherwise seeds a tiny demo set.
    Enforces ETD < ETA <= ATA + status rules above.
    """
    from app import create_app, db
    from app.models import Order, User

    app = create_app()
    with app.app_context():
        if db.session.query(Order).count() > 0:
            return  # already seeded

        # Ensure at least one user exists (assign to orders)
        user = db.session.query(User).first()
        if not user:
            user = User(username="demo", role="admin")
            user.set_password("demo1234")
            db.session.add(user)
            db.session.commit()

        rows = []

        # 1) If you maintain a CSV at data/orders.csv (headers match model fields), load it:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "orders.csv")
        if os.path.exists(csv_path):
            import csv
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)
        else:
            # 2) Otherwise seed a small in-memory sample
            rows = [
                {
                    "order_date": "01.07.25", "order_number": "PO-2025-001",
                    "product_name": "Losartan potassium", "buyer": "Acme Clinics GmbH",
                    "responsible": "Anna Kramer", "quantity": "1000", "required_delivery": "By Q4 2025",
                    "terms_of_delivery": "FAS", "payment_date": "16.10.25",
                    "etd": "07.12.25", "eta": "10.12.25", "ata": "10.12.25",
                    "transport": "sea"
                },
                {
                    "order_date": "15.07.25", "order_number": "PO-2025-002",
                    "product_name": "Amlodipine besylate", "buyer": "BioCare AG",
                    "responsible": "Elena Nowak", "quantity": "300", "required_delivery": "By November 2025",
                    "terms_of_delivery": "CFR", "payment_date": "25.10.25",
                    "etd": "31.12.25", "eta": "12.01.26", "ata": None,
                    "transport": "sea"
                },
                {
                    "order_date": "05.06.25", "order_number": "PO-2025-003",
                    "product_name": "Hydrochlorothiazide", "buyer": "Nova Pharma BV",
                    "responsible": "Anna Kramer", "quantity": "1382",
                    "required_delivery": "ASAP", "terms_of_delivery": "EXW", "payment_date": "31.10.25",
                    "etd": "19.11.25", "eta": "17.12.25", "ata": None,
                    "transport": "sea"
                },
            ]

        # Normalize and insert
        for r in rows:
            etd, eta, ata, status = _enforce_timeline_rules(r.get("etd"), r.get("eta"), r.get("ata"))
            order = Order(
                order_date=r.get("order_date"),
                order_number=r.get("order_number"),
                product_name=r.get("product_name"),
                buyer=r.get("buyer"),
                responsible=r.get("responsible"),
                quantity=float(r.get("quantity") or 0),
                required_delivery=r.get("required_delivery"),
                terms_of_delivery=r.get("terms_of_delivery"),
                payment_date=r.get("payment_date"),
                etd=etd,
                eta=eta,
                ata=ata,
                transit_status=status,
                transport=r.get("transport") or "sea",
                user_id=user.id,
            )
            db.session.add(order)

        db.session.commit()

if __name__ == "__main__":
    ensure_seed()
