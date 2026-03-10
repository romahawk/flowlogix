# app/seed_boot.py
import calendar
import os
from datetime import date, timedelta
from typing import Optional, Tuple


# ── Date utilities ─────────────────────────────────────────────────────────────

def _start_end_of_iso_week(dt: date) -> Tuple[date, date]:
    start = dt - timedelta(days=(dt.isoweekday() - 1))
    end = start + timedelta(days=6)
    return start, end


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    try:
        if "." in s:
            d, m, y = s.split(".")
            y = int(y)
            y = 2000 + y if y < 100 else y
            return date(int(y), int(m), int(d))
        if "-" in s:
            y, m, d = s.split("-")
            return date(int(y), int(m), int(d))
    except Exception:
        return None
    return None


def _fmt_date(d: Optional[date]) -> Optional[str]:
    if not d:
        return None
    return d.strftime("%d.%m.%y")


def _mo(today: date, months_back: int, day: int) -> str:
    """Return dd.mm.yy string that is `months_back` months before today on `day`."""
    m = today.month - months_back
    y = today.year
    while m <= 0:
        m += 12
        y -= 1
    max_d = calendar.monthrange(y, m)[1]
    return date(y, m, min(day, max_d)).strftime("%d.%m.%y")


def _rel(today: date, delta_days: int) -> str:
    """Return dd.mm.yy string offset by delta_days from today."""
    return (today + timedelta(days=delta_days)).strftime("%d.%m.%y")


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

    if etd and not eta and ata:
        eta = min(ata, etd + timedelta(days=21))
    if not etd and eta:
        etd = eta - timedelta(days=7)

    if etd and eta and eta <= etd:
        eta = etd + timedelta(days=7)

    if ata and eta and ata < eta:
        ata = eta

    if ata and ata < wk_start:
        status = "arrived"
    elif not ata and eta and eta < today:
        status = "en route"
    elif etd and (etd > wk_end) and eta and (eta > wk_end):
        status = "in process"
    elif etd and (etd < wk_start) and eta and (eta > wk_end):
        status = "en route"
    else:
        if ata and wk_start <= ata <= wk_end:
            status = "arrived"
        elif eta and eta > wk_end:
            status = "in process"
        elif etd and etd < wk_start:
            status = "en route"
        else:
            status = "in process"

    return _fmt_date(etd), _fmt_date(eta), _fmt_date(ata), status


# ── Rich demo dataset builders (shared with demo_routes) ──────────────────────

def build_order_rows(today: date) -> list:
    """
    30 Orders spread across ~9 months.

    Groups (by order_date month):
      A  5 orders  ~7-9 months ago  arrived Q3
      B  5 orders  ~5-6 months ago  arrived Q4
      E  6 orders  ~2-4 months ago  recently arrived
      C  5 orders  last month       3 active + 2 delayed
      D  9 orders  this month       8 active + 1 delayed

    KPI dynamics (this month vs last month):
      In Transit  +80%   Warehouse  +67%
      Delivered   +67%   Delayed   -50%
    """
    def mo(back, day): return _mo(today, back, day)
    def rel(delta):    return _rel(today, delta)

    delayed_this_eta = rel(-10)
    delayed_this_etd = rel(-40)

    BUYERS = [
        "Acme Clinics GmbH", "BioCare AG", "Nova Pharma BV",
        "HealthPlus Ltd", "Medico Supplies Sp.", "Wellness Partners SA",
    ]
    RESP  = ["Anna Kramer", "Elena Nowak", "Ben Schneider",
             "Carla Rossi", "David Weber", "Felix Bauer"]
    TERMS = ["FOB", "CIF", "CFR", "EXW", "DAP", "DDP", "FAS", "CIP"]
    TR    = ["sea", "air", "truck"]

    def r(seq, od, pn, buyer, resp, qty, rd, terms, pd_, etd, eta, ata, transport):
        yr = today.year if seq >= 17 else today.year - 1
        return dict(
            order_date=od, order_number=f"PO-{yr}-{seq:03d}",
            product_name=pn, buyer=buyer, responsible=resp,
            quantity=qty, required_delivery=rd, terms_of_delivery=terms,
            payment_date=pd_, etd=etd, eta=eta, ata=ata, transport=transport,
        )

    B, R, T, TR_ = BUYERS, RESP, TERMS, TR
    return [
        # ── Group A: arrived Q3 ~7-9 months ago ──────────────────────────────
        r( 1, mo(9,10), "Losartan potassium",    B[0],R[0], 1000, "By Q3", T[0], mo(9,20), mo(8,1),  mo(7,10), mo(7,12), TR_[0]),
        r( 2, mo(8,20), "Amlodipine besylate",   B[1],R[1],  500, "ASAP",  T[1], mo(8,28), mo(7,15), mo(6,20), mo(6,22), TR_[1]),
        r( 3, mo(8, 5), "Hydrochlorothiazide",   B[2],R[2], 1382, "ASAP",  T[2], mo(8,15), mo(7,1),  mo(6, 8), mo(6,10), TR_[0]),
        r( 4, mo(7,18), "Cetirizine HCl 10 mg",  B[3],R[3], 1200, "Q3",   T[3], mo(7,28), mo(6,20), mo(5,25), mo(5,27), TR_[2]),
        r( 5, mo(7, 1), "Omeprazole 20 mg",      B[4],R[4],  750, "Q3",   T[4], mo(7,10), mo(6, 5), mo(5,10), mo(5,12), TR_[0]),
        # ── Group B: arrived Q4 ~5-6 months ago ──────────────────────────────
        r( 6, mo(6, 5), "Atorvastatin calcium",  B[5],R[5],  900, "Q4",   T[5], mo(6,15), mo(5,10), mo(4,15), mo(4,17), TR_[1]),
        r( 7, mo(6,20), "Pantoprazole sodium",   B[1],R[0],  600, "Q4",   T[6], mo(6,28), mo(5,20), mo(4,28), mo(4,30), TR_[0]),
        r( 8, mo(5,10), "Dexamethasone 4 mg/ml", B[2],R[1],  400, "Q4",   T[7], mo(5,20), mo(4,15), mo(3,20), mo(3,22), TR_[2]),
        r( 9, mo(5,25), "Ibuprofen 400 mg",      B[3],R[2], 3000, "Q4",   T[0], mo(6, 5), mo(5, 1), mo(4, 5), mo(4, 7), TR_[0]),
        r(10, mo(5, 8), "Amoxicillin 500 mg",    B[4],R[3],  800, "Q4",   T[1], mo(5,18), mo(4,10), mo(3,15), mo(3,17), TR_[1]),
        # ── Group E: recently arrived, ata last/this month ────────────────────
        r(11, mo(4,20), "Furosemide 40 mg",      B[5],R[4],  550, "ASAP", T[2], mo(4,28), mo(3,5),  mo(2, 5), mo(2, 7), TR_[0]),
        r(12, mo(4, 5), "Lisinopril 10 mg",      B[0],R[5],  700, "ASAP", T[3], mo(4,15), mo(3,1),  mo(1,15), mo(1,17), TR_[2]),
        r(13, mo(3,18), "Simvastatin 20 mg",     B[1],R[0],  450, "ASAP", T[4], mo(3,28), mo(2,20), mo(1,25), mo(1,27), TR_[1]),
        r(14, mo(3, 1), "Clopidogrel 75 mg",     B[2],R[1],  600, "ASAP", T[5], mo(3,10), mo(2, 5), mo(1, 8), mo(1,10), TR_[0]),
        r(15, mo(2,15), "Paracetamol 500 mg",    B[3],R[2], 2000, "ASAP", T[6], mo(2,25), mo(1,20), mo(0,10), mo(0,12), TR_[2]),
        r(16, mo(2, 1), "Azithromycin 250 mg",   B[4],R[3],  300, "ASAP", T[7], mo(2,10), mo(1, 5), mo(0,18), mo(0,20), TR_[1]),
        # ── Group C: last month (5) ───────────────────────────────────────────
        r(17, mo(1, 5), "Losartan potassium",    B[0],R[4], 1100, "Q2",   T[0], mo(1,15), mo(0,10), rel(+18), None,      TR_[0]),
        r(18, mo(1,12), "Metformin HCl 500 mg",  B[5],R[5], 2200, "Q2",   T[1], mo(1,22), mo(0,15), rel(+31), None,      TR_[1]),
        r(19, mo(1,22), "Diazepam 5 mg",         B[1],R[0],  280, "Q2",   T[2], mo(1,28), mo(0,20), rel(+38), None,      TR_[2]),
        r(20, mo(1, 8), "Pantoprazole sodium",   B[2],R[1],  650, "ASAP", T[3], mo(1,18), mo(2,25), mo(1,20), None,      TR_[0]),
        r(21, mo(1,15), "Omeprazole 20 mg",      B[3],R[2],  820, "ASAP", T[4], mo(1,23), mo(2, 1), mo(1,28), None,      TR_[1]),
        # ── Group D: this month (9) ───────────────────────────────────────────
        r(22, rel(-24), "Amlodipine besylate",   B[4],R[3],  510, "Q2",   T[5], rel(-18), rel(+8),  rel(+43), None,      TR_[0]),
        r(23, rel(-22), "Atorvastatin calcium",  B[5],R[4],  920, "Q2",   T[6], rel(-16), rel(+10), rel(+48), None,      TR_[1]),
        r(24, rel(-20), "Cetirizine HCl 10 mg",  B[0],R[5], 1300, "Q2",   T[7], rel(-14), rel(+3),  rel(+28), None,      TR_[2]),
        r(25, rel(-17), "Losartan potassium",    B[1],R[0], 1050, "Q2",   T[0], rel(-11), rel(+13), rel(+50), None,      TR_[0]),
        r(26, rel(-15), "Hydrochlorothiazide",   B[2],R[1], 1400, "Q2",   T[1], rel(-9),  rel(+15), rel(+52), None,      TR_[1]),
        r(27, rel(-12), "Furosemide 40 mg",      B[3],R[2],  570, "Q2",   T[2], rel(-6),  rel(+18), rel(+45), None,      TR_[0]),
        r(28, rel(-10), "Simvastatin 20 mg",     B[4],R[3],  460, "Q2",   T[3], rel(-4),  rel(+5),  rel(+32), None,      TR_[2]),
        r(29, rel( -7), "Amoxicillin 500 mg",    B[5],R[4],  830, "Q2",   T[4], rel(-2),  rel(+23), rel(+58), None,      TR_[1]),
        r(30, rel(-23), "Dexamethasone 4 mg/ml", B[0],R[5],  410, "ASAP", T[5], rel(-17), delayed_this_etd, delayed_this_eta, None, TR_[0]),
    ]


def build_warehouse_rows(today: date) -> list:
    """12 WarehouseStock rows (3 last month + 5 this month → +67% KPI)."""
    def mo(back, day): return _mo(today, back, day)
    return [
        dict(order_number="WH-001", product_name="Losartan potassium",   quantity="800",  ata=mo(3,10), transport="sea",   notes="Cold chain verified"),
        dict(order_number="WH-002", product_name="Atorvastatin calcium",  quantity="720",  ata=mo(3,22), transport="air",   notes=""),
        dict(order_number="WH-003", product_name="Omeprazole 20 mg",      quantity="600",  ata=mo(2,8),  transport="truck", notes="Pallet A3"),
        dict(order_number="WH-004", product_name="Cetirizine HCl 10 mg",  quantity="950",  ata=mo(2,21), transport="sea",   notes=""),
        dict(order_number="WH-005", product_name="Furosemide 40 mg",      quantity="500",  ata=mo(1,8),  transport="sea",   notes="Shelf B2"),
        dict(order_number="WH-006", product_name="Lisinopril 10 mg",      quantity="640",  ata=mo(1,18), transport="air",   notes=""),
        dict(order_number="WH-007", product_name="Simvastatin 20 mg",     quantity="410",  ata=mo(1,27), transport="truck", notes="Temp controlled"),
        dict(order_number="WH-008", product_name="Clopidogrel 75 mg",     quantity="580",  ata=mo(0,4),  transport="sea",   notes=""),
        dict(order_number="WH-009", product_name="Paracetamol 500 mg",    quantity="1800", ata=mo(0,9),  transport="air",   notes="Lot #2026-44"),
        dict(order_number="WH-010", product_name="Azithromycin 250 mg",   quantity="270",  ata=mo(0,13), transport="truck", notes=""),
        dict(order_number="WH-011", product_name="Metformin HCl 500 mg",  quantity="2100", ata=mo(0,18), transport="sea",   notes="Bulk pallet"),
        dict(order_number="WH-012", product_name="Hydrochlorothiazide",   quantity="1300", ata=mo(0,22), transport="air",   notes=""),
    ]


def build_delivered_rows(today: date) -> list:
    """11 DeliveredGoods rows (3 last month + 5 this month → +67% KPI)."""
    def mo(back, day): return _mo(today, back, day)
    return [
        dict(order_number="DG-001", product_name="Amlodipine besylate",   quantity="480",  delivery_source="From Warehouse",      delivery_date=mo(3,15), transport="sea",   notes="Delivered to Central"),
        dict(order_number="DG-002", product_name="Pantoprazole sodium",   quantity="590",  delivery_source="Direct from Transit",  delivery_date=mo(3,28), transport="air",   notes=""),
        dict(order_number="DG-003", product_name="Dexamethasone 4 mg/ml", quantity="370",  delivery_source="From Warehouse",      delivery_date=mo(2,15), transport="truck", notes="Signed by J. Muller"),
        dict(order_number="DG-004", product_name="Ibuprofen 400 mg",      quantity="2800", delivery_source="From Warehouse",      delivery_date=mo(1,10), transport="sea",   notes=""),
        dict(order_number="DG-005", product_name="Amoxicillin 500 mg",    quantity="750",  delivery_source="Direct from Transit",  delivery_date=mo(1,20), transport="air",   notes="Batch verified"),
        dict(order_number="DG-006", product_name="Losartan potassium",    quantity="900",  delivery_source="From Warehouse",      delivery_date=mo(1,28), transport="truck", notes=""),
        dict(order_number="DG-007", product_name="Atorvastatin calcium",  quantity="860",  delivery_source="Direct from Transit",  delivery_date=mo(0,5),  transport="sea",   notes=""),
        dict(order_number="DG-008", product_name="Omeprazole 20 mg",      quantity="570",  delivery_source="From Warehouse",      delivery_date=mo(0,10), transport="air",   notes="Cold chain OK"),
        dict(order_number="DG-009", product_name="Furosemide 40 mg",      quantity="490",  delivery_source="Direct from Transit",  delivery_date=mo(0,14), transport="truck", notes=""),
        dict(order_number="DG-010", product_name="Clopidogrel 75 mg",     quantity="540",  delivery_source="From Warehouse",      delivery_date=mo(0,18), transport="sea",   notes="POD uploaded"),
        dict(order_number="DG-011", product_name="Paracetamol 500 mg",    quantity="1700", delivery_source="Direct from Transit",  delivery_date=mo(0,22), transport="air",   notes=""),
    ]


# ── Main seeder ───────────────────────────────────────────────────────────────

def ensure_seed():
    """
    Seed only when there are no orders yet.
    Uses CSV in /data/orders.csv if present (orders only), otherwise seeds the
    full rich demo dataset: 30 orders + 12 warehouse rows + 11 delivered rows.
    """
    from app import create_app, db
    from app.models import Order, WarehouseStock, DeliveredGoods, User

    app = create_app()
    with app.app_context():
        if db.session.query(Order).count() > 0:
            return

        user = db.session.query(User).first()
        if not user:
            user = User(username="demo", role="admin")
            user.set_password("demo1234")
            db.session.add(user)
            db.session.commit()

        today = date.today()

        # 1) CSV path — orders only (legacy support)
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "orders.csv")
        if os.path.exists(csv_path):
            import csv
            with open(csv_path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    etd, eta, ata, status = _enforce_timeline_rules(r.get("etd"), r.get("eta"), r.get("ata"))
                    db.session.add(Order(
                        order_date=r.get("order_date"), order_number=r.get("order_number"),
                        product_name=r.get("product_name"), buyer=r.get("buyer"),
                        responsible=r.get("responsible"), quantity=float(r.get("quantity") or 0),
                        required_delivery=r.get("required_delivery"),
                        terms_of_delivery=r.get("terms_of_delivery"),
                        payment_date=r.get("payment_date"), etd=etd, eta=eta, ata=ata,
                        transit_status=status, transport=r.get("transport") or "sea",
                        user_id=user.id,
                    ))
            db.session.commit()
            return

        # 2) Rich in-memory demo dataset
        for r in build_order_rows(today):
            ata_raw = r.get("ata")
            etd, eta, ata, status = _enforce_timeline_rules(
                r.get("etd"), r.get("eta"),
                ata_raw if isinstance(ata_raw, str) else None,
            )
            db.session.add(Order(
                order_date=r["order_date"], order_number=r["order_number"],
                product_name=r["product_name"], buyer=r["buyer"],
                responsible=r["responsible"], quantity=float(r.get("quantity") or 0),
                required_delivery=r.get("required_delivery", ""),
                terms_of_delivery=r.get("terms_of_delivery", "FOB"),
                payment_date=r.get("payment_date"), etd=etd, eta=eta, ata=ata,
                transit_status=status, transport=r.get("transport") or "sea",
                user_id=user.id,
            ))

        for w in build_warehouse_rows(today):
            db.session.add(WarehouseStock(
                order_number=w["order_number"], product_name=w["product_name"],
                quantity=w["quantity"], ata=w["ata"], transit_status="In Stock",
                notes=w.get("notes", ""), transport=w.get("transport", "sea"),
                is_manual=True, is_archived=False, user_id=user.id,
            ))

        for dg in build_delivered_rows(today):
            db.session.add(DeliveredGoods(
                order_number=dg["order_number"], product_name=dg["product_name"],
                quantity=dg["quantity"], delivery_source=dg["delivery_source"],
                delivery_date=dg["delivery_date"], transport=dg.get("transport", "sea"),
                notes=dg.get("notes", ""), user_id=user.id,
            ))

        db.session.commit()


if __name__ == "__main__":
    ensure_seed()
