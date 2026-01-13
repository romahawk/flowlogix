from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Tuple

from flask import request
from flask_login import current_user, login_required

from app.models import Order
from app.roles import can_view_all

from . import api_v1_bp
from .errors import ok
from .schemas import serialize_order


# Accept mixed legacy formats, but emit consistent ISO for true date fields.
_INPUT_DATE_FORMATS: Tuple[str, ...] = ("%Y-%m-%d", "%d.%m.%y", "%d.%m.%Y", "%d/%m/%Y")


def parse_date(value: Optional[str]) -> Optional[date]:
    """Parse known date string formats into date. Returns None if empty/unparseable."""
    if not value:
        return None
    s = value.strip()
    if not s:
        return None
    for fmt in _INPUT_DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def to_iso(value: Optional[str]) -> str:
    """Normalize any supported date string to ISO (YYYY-MM-DD). Blank if missing/unparseable."""
    d = parse_date(value)
    return d.isoformat() if d else ""


def get_sort_date(o: Order, field: str) -> date:
    """Return sortable date for the given field; missing dates go to date.min."""
    d = parse_date(getattr(o, field, None))
    return d if d else date.min


@dataclass(frozen=True)
class SortItem:
    field: str
    direction: str  # "asc" | "desc"


_ALLOWED_SORT_FIELDS = {
    "eta", "etd", "ata", "order_date",
    "order_number", "buyer", "responsible",
    "transport", "transit_status",
}


def parse_sort_param(raw: Optional[str]) -> List[SortItem]:
    """
    Parse sort string like: "eta:desc,order_date:asc"
    If absent -> default sort (canonical).
    Always enforces stable tie-breaker by id desc.
    """
    if not raw:
        items = [SortItem("eta", "desc"), SortItem("etd", "desc"), SortItem("order_date", "desc")]
    else:
        items: List[SortItem] = []
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        for p in parts:
            if ":" in p:
                field, direction = p.split(":", 1)
            else:
                field, direction = p, "asc"
            field = field.strip()
            direction = direction.strip().lower()
            if field not in _ALLOWED_SORT_FIELDS:
                continue
            if direction not in {"asc", "desc"}:
                direction = "asc"
            items.append(SortItem(field, direction))

        if not items:
            items = [SortItem("eta", "desc"), SortItem("etd", "desc"), SortItem("order_date", "desc")]

    # Stable tie-breaker (always)
    items.append(SortItem("id", "desc"))
    return items


def order_matches_year(o: Order, year: int) -> bool:
    """Legacy behavior: include if ANY relevant date is in the requested year."""
    for fld in ("order_date", "etd", "eta", "ata"):
        d = parse_date(getattr(o, fld, None))
        if d and d.year == year:
            return True
    return False


def apply_python_sort(rows: List[Order], sort_items: List[SortItem]) -> List[Order]:
    """
    Python-side stable multi-sort.
    Apply sorts from last key to first to emulate multi-column sort.
    """
    def key_for(o: Order, field: str):
        if field == "id":
            return o.id
        if field in {"eta", "etd", "ata", "order_date"}:
            return get_sort_date(o, field)
        return (getattr(o, field, "") or "").lower()

    for item in reversed(sort_items):
        reverse = item.direction == "desc"
        rows.sort(key=lambda o, f=item.field: key_for(o, f), reverse=reverse)

    return rows


@api_v1_bp.route("/orders", methods=["GET"])
@login_required
def list_orders():
    # -------------------------
    # Pagination
    # -------------------------
    page = max(1, request.args.get("page", 1, type=int))
    per_page = request.args.get("per_page", 25, type=int)
    per_page = max(1, min(per_page, 100))

    # -------------------------
    # Filters
    # -------------------------
    transit_status = request.args.get("filter[transit_status]") or None
    year = request.args.get("filter[year]", type=int)
    q_text = request.args.get("filter[q]") or None
    transport = request.args.get("filter[transport]") or None
    buyer = request.args.get("filter[buyer]") or None
    responsible = request.args.get("filter[responsible]") or None

    # -------------------------
    # Sorting
    # -------------------------
    sort_raw = request.args.get("sort")
    sort_items = parse_sort_param(sort_raw)

    # -------------------------
    # Base query + RBAC scope
    # -------------------------
    q = Order.query
    if not can_view_all(current_user.role):
        q = q.filter(Order.user_id == current_user.id)

    if transit_status:
        q = q.filter(Order.transit_status == transit_status)

    if transport:
        q = q.filter(Order.transport == transport)

    if buyer:
        q = q.filter(Order.buyer == buyer)

    if responsible:
        q = q.filter(Order.responsible == responsible)

    if q_text:
        like = f"%{q_text.strip()}%"
        q = q.filter(
            Order.order_number.ilike(like) |
            Order.product_name.ilike(like) |
            Order.buyer.ilike(like) |
            Order.responsible.ilike(like)
        )

    # Pull rows (dates are stored as strings -> Python sort & year check)
    rows = q.all()

    # Year filter (ANY date matches: legacy semantics)
    if year:
        rows = [o for o in rows if order_matches_year(o, year)]

    # Stable multi-sort
    rows = apply_python_sort(rows, sort_items)

    # Pagination slice
    total = len(rows)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = rows[start:end]

    # Normalize true date fields to ISO for React safety.
    # NOTE: required_delivery is intentionally NOT normalized (often free text like "By Q3 2025").
    data = []
    for o in page_items:
        item = serialize_order(o)

        for fld in ("order_date", "payment_date", "etd", "eta", "ata"):
            if fld in item:
                item[fld] = to_iso(item.get(fld))

        data.append(item)

    return ok(
        data=data,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "sort": ",".join([f"{s.field}:{s.direction}" for s in sort_items]),
            "filters": {
                "transit_status": transit_status,
                "transport": transport,
                "buyer": buyer,
                "responsible": responsible,
                "year": year,
                "q": q_text,
            },
        },
    )
