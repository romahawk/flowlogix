"""
Demo-mode only endpoints for seeding and clearing orders from the UI.
All routes are guarded by DEMO_MODE config flag + login_required.
"""
from datetime import date, timedelta
from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from app.models import Order, User
from app.database import db

demo_bp = Blueprint("demo", __name__)


def _build_seed_rows(year: int) -> list:
    """
    Return a list of order dicts anchored to *year* so the Timeline
    always shows realistic spread regardless of when the app is run.
    Dates are offsets from Jan 1 of the given year.
    """
    def d(month: int, day: int) -> str:
        return date(year, month, day).strftime("%d.%m.%y")

    return [
        # ── Q1 arrived ────────────────────────────────────────────────────────
        {"order_date": d(1, 8),  "order_number": f"PO-{year}-001",
         "product_name": "Losartan potassium",       "buyer": "Acme Clinics GmbH",
         "responsible": "Anna Kramer",   "quantity": 1000,
         "required_delivery": f"By Q1 {year}", "terms_of_delivery": "FAS",
         "payment_date": d(1, 20), "etd": d(1, 15), "eta": d(2, 10), "ata": d(2, 12),
         "transport": "sea"},
        {"order_date": d(1, 20), "order_number": f"PO-{year}-002",
         "product_name": "Amlodipine besylate",      "buyer": "BioCare AG",
         "responsible": "Elena Nowak",   "quantity": 500,
         "required_delivery": f"By Q1 {year}", "terms_of_delivery": "CIF",
         "payment_date": d(2, 1),  "etd": d(2, 1),  "eta": d(2, 20), "ata": d(2, 22),
         "transport": "air"},
        # ── Q2 arrived ────────────────────────────────────────────────────────
        {"order_date": d(3, 5),  "order_number": f"PO-{year}-003",
         "product_name": "Hydrochlorothiazide",      "buyer": "Nova Pharma BV",
         "responsible": "Ben Schneider", "quantity": 1382,
         "required_delivery": "ASAP",                "terms_of_delivery": "EXW",
         "payment_date": d(3, 15), "etd": d(3, 20), "eta": d(4, 15), "ata": d(4, 17),
         "transport": "sea"},
        {"order_date": d(4, 10), "order_number": f"PO-{year}-004",
         "product_name": "Metformin HCl 500 mg",     "buyer": "HealthPlus Ltd",
         "responsible": "Carla Rossi",   "quantity": 2000,
         "required_delivery": f"By Q2 {year}", "terms_of_delivery": "DAP",
         "payment_date": d(4, 20), "etd": d(4, 25), "eta": d(5, 20), "ata": d(5, 22),
         "transport": "truck"},
        # ── Q3 en route / arrived ─────────────────────────────────────────────
        {"order_date": d(5, 15), "order_number": f"PO-{year}-005",
         "product_name": "Omeprazole 20 mg",         "buyer": "Medico Supplies Sp.",
         "responsible": "David Weber",   "quantity": 750,
         "required_delivery": f"By Q3 {year}", "terms_of_delivery": "FOB",
         "payment_date": d(6, 1),  "etd": d(6, 10), "eta": d(7, 5),  "ata": d(7, 7),
         "transport": "sea"},
        {"order_date": d(6, 1),  "order_number": f"PO-{year}-006",
         "product_name": "Atorvastatin calcium",     "buyer": "Wellness Partners SA",
         "responsible": "Felix Bauer",   "quantity": 900,
         "required_delivery": f"By Q3 {year}", "terms_of_delivery": "CIP",
         "payment_date": d(6, 15), "etd": d(7, 1),  "eta": d(7, 28), "ata": d(7, 30),
         "transport": "air"},
        {"order_date": d(6, 20), "order_number": f"PO-{year}-007",
         "product_name": "Pantoprazole sodium",      "buyer": "BioCare AG",
         "responsible": "Anna Kramer",   "quantity": 600,
         "required_delivery": f"By Q3 {year}", "terms_of_delivery": "CFR",
         "payment_date": d(7, 5),  "etd": d(7, 15), "eta": d(8, 10), "ata": d(8, 12),
         "transport": "sea"},
        # ── Q3-Q4 en route ────────────────────────────────────────────────────
        {"order_date": d(7, 10), "order_number": f"PO-{year}-008",
         "product_name": "Cetirizine HCl 10 mg",    "buyer": "Acme Clinics GmbH",
         "responsible": "Elena Nowak",   "quantity": 1200,
         "required_delivery": f"By Q4 {year}", "terms_of_delivery": "FOB",
         "payment_date": d(8, 1),  "etd": d(8, 20), "eta": d(9, 20), "ata": None,
         "transport": "sea"},
        {"order_date": d(8, 1),  "order_number": f"PO-{year}-009",
         "product_name": "Dexamethasone 4 mg/ml",   "buyer": "Nova Pharma BV",
         "responsible": "Ben Schneider", "quantity": 400,
         "required_delivery": f"By Q4 {year}", "terms_of_delivery": "EXW",
         "payment_date": d(8, 20), "etd": d(9, 5),  "eta": d(9, 30), "ata": None,
         "transport": "air"},
        # ── Q4 in process ─────────────────────────────────────────────────────
        {"order_date": d(9, 1),  "order_number": f"PO-{year}-010",
         "product_name": "Ibuprofen 400 mg",         "buyer": "HealthPlus Ltd",
         "responsible": "Carla Rossi",   "quantity": 3000,
         "required_delivery": f"By Q4 {year}", "terms_of_delivery": "DDP",
         "payment_date": d(10, 1), "etd": d(10, 10), "eta": d(11, 5), "ata": None,
         "transport": "truck"},
        {"order_date": d(9, 15), "order_number": f"PO-{year}-011",
         "product_name": "Amoxicillin 500 mg",       "buyer": "Medico Supplies Sp.",
         "responsible": "David Weber",   "quantity": 800,
         "required_delivery": f"By Q4 {year}", "terms_of_delivery": "CIF",
         "payment_date": d(10, 15), "etd": d(10, 25), "eta": d(11, 20), "ata": None,
         "transport": "sea"},
        {"order_date": d(10, 5), "order_number": f"PO-{year}-012",
         "product_name": "Furosemide 40 mg",         "buyer": "Wellness Partners SA",
         "responsible": "Felix Bauer",   "quantity": 550,
         "required_delivery": f"By Q4 {year}", "terms_of_delivery": "FOB",
         "payment_date": d(11, 1), "etd": d(11, 10), "eta": d(12, 5), "ata": None,
         "transport": "truck"},
    ]


def _seed_in_context() -> int:
    """Insert demo orders into the current app context. Returns count inserted."""
    from app.seed_boot import _enforce_timeline_rules

    user = User.query.first()
    if not user:
        return 0

    year = date.today().year
    rows = _build_seed_rows(year)

    for r in rows:
        ata_raw = r.get("ata")
        etd, eta, ata, status = _enforce_timeline_rules(
            r.get("etd"), r.get("eta"),
            ata_raw.strftime("%d.%m.%y") if hasattr(ata_raw, "strftime") else ata_raw,
        )
        db.session.add(Order(
            order_date=r["order_date"],
            order_number=r["order_number"],
            product_name=r["product_name"],
            buyer=r["buyer"],
            responsible=r["responsible"],
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
        ))

    db.session.commit()
    return len(rows)


# ── Routes ────────────────────────────────────────────────────────────────────

@demo_bp.post("/demo/seed")
@login_required
def demo_seed():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "Not in demo mode"}), 403
    Order.query.delete()
    db.session.commit()
    n = _seed_in_context()
    return jsonify({"status": "seeded", "count": n})


@demo_bp.post("/demo/clear")
@login_required
def demo_clear():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "Not in demo mode"}), 403
    deleted = Order.query.delete()
    db.session.commit()
    return jsonify({"status": "cleared", "deleted": int(deleted)})


@demo_bp.post("/demo/reset")
@login_required
def demo_reset():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "Not in demo mode"}), 403
    deleted = Order.query.delete()
    db.session.commit()
    n = _seed_in_context()
    return jsonify({"status": "reset", "deleted": int(deleted), "seeded": n})
