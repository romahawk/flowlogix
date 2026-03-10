"""
Demo-mode only endpoints for seeding and clearing orders from the UI.
All routes are guarded by DEMO_MODE config flag + login_required.

Seed dataset (relative to today, always):
  Orders        → 45 rows spanning ~9 months  (incl. 9 delayed, 15 active)
  WarehouseStock→ 20 rows
  DeliveredGoods→ 21 rows

KPI totals after seed:
  In Transit  45   Warehouse  20   Delivered  21   Delayed  9
"""
from datetime import date
from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from app.models import Order, WarehouseStock, DeliveredGoods, User
from app.database import db
from app.seed_boot import (
    build_order_rows, build_warehouse_rows, build_delivered_rows,
    _enforce_timeline_rules,
)

demo_bp = Blueprint("demo", __name__)


# ── Core seed/clear helpers ────────────────────────────────────────────────────

def _seed_in_context() -> int:
    user = User.query.first()
    if not user:
        return 0

    today = date.today()

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
    return len(build_order_rows(today))


def _clear_all():
    DeliveredGoods.query.delete()
    WarehouseStock.query.delete()
    Order.query.delete()
    db.session.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@demo_bp.post("/demo/seed")
@login_required
def demo_seed():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "Not in demo mode"}), 403
    _clear_all()
    n = _seed_in_context()
    return jsonify({"status": "seeded", "count": n})


@demo_bp.post("/demo/clear")
@login_required
def demo_clear():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "Not in demo mode"}), 403
    _clear_all()
    return jsonify({"status": "cleared"})


@demo_bp.post("/demo/reset")
@login_required
def demo_reset():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "Not in demo mode"}), 403
    _clear_all()
    n = _seed_in_context()
    return jsonify({"status": "reset", "seeded": n})
