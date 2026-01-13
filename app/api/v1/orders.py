from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Tuple, Dict, Any

from flask import request
from flask_login import current_user, login_required

from app.models import Order
from app.roles import can_view_all

from . import api_v1_bp
from .errors import ok, fail
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

_ALLOWED_FILTER_KEYS = {
    "transit_status",
    "year",
    "q",
    "transport",
    "buyer",
    "responsible",
}

_ALLOWED_TOP_LEVEL_PARAMS = {"page", "per_page", "sort"}  # plus filter[...] keys


def _err(details: List[Dict[str, Any]], field: str, issue: str):
    details.append({"field": field, "issue": issue})


def parse_int_strict(raw: Optional[str], field: str, details: List[Dict[str, Any]]) -> Optional[int]:
    """Parse int; if provided but invalid -> record error."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        _err(details, field, "Must be an integer.")
        return None


def validate_query_params() -> Tuple[Optional[int], Optional[int], List[SortItem], Dict[str, Any], Optional[Tuple[str, Any]]]:
    """
    Validates and parses:
    - page, per_page
    - sort
    - filter[...] keys

    Returns:
    (page, per_page, sort_items, filters_dict, error_tuple)
    where error_tuple is ("VALIDATION_ERROR", details) if invalid.
    """
    details: List[Dict[str, Any]] = []

    # ---- Reject unknown params early ----
    for key in request.args.keys():
        if key in _ALLOWED_TOP_LEVEL_PARAMS:
            continue
        if key.startswith("filter[") and key.endswith("]"):
            filter_key = key[len("filter["):-1]
            if filter_key not in _ALLOWED_FILTER_KEYS:
                _err(details, key, f"Unsupported filter. Allowed: {sorted(_ALLOWED_FILTER_KEYS)}")
            continue
        # unknown top-level param
        _err(details, key, "Unsupported query parameter.")

    # ---- page / per_page strict parsing ----
    page_raw = request.args.get("page")
    per_page_raw = request.args.get("per_page")

    page = parse_int_strict(page_raw, "page", details)
    per_page = parse_int_strict(per_page_raw, "per_page", details)

    if page is None:
        page = 1
    if per_page is None:
        per_page = 25

    if page < 1:
        _err(details, "page", "Must be >= 1.")
    if per_page < 1 or per_page > 100:
        _err(details, "per_page", "Must be between 1 and 100.")

    # ---- filters ----
    filters: Dict[str, Any] = {
        "transit_status": request.args.get("filter[transit_status]") or None,
        "transport": request.args.get("filter[transport]") or None,
        "buyer": request.args.get("filter[buyer]") or None,
        "responsible": request.args.get("filter[responsible]") or None,
        "q": request.args.get("filter[q]") or None,
        "year": None,
    }

    year_raw = request.args.get("filter[year]")
    year = parse_int_strict(year_raw, "filter[year]", details)
    if year is not None:
        if year < 1990 or year > 2100:
            _err(details, "filter[year]", "Year must be between 1990 and 2100.")
        else:
            filters["year"] = year

    # basic string constraints (avoid abuse + silly payloads)
    def _len_check(name: str, value: Optional[str], max_len: int):
        if value is None:
            return
        if len(value) > max_len:
            _err(details, f"filter[{name}]", f"Too long (max {max_len} chars).")

    _len_check("q", filters["q"], 100)
    _len_check("buyer", filters["buyer"], 100)
    _len_check("responsible", filters["responsible"], 100)
    _len_check("transport", filters["transport"], 30)
    _len_check("transit_status", filters["transit_status"], 30)

    # ---- sort strict parsing ----
    sort_raw = request.args.get("sort")
    sort_items, sort_errors = parse_sort_param_strict(sort_raw)
    for e in sort_errors:
        _err(details, "sort", e)

    if details:
        return None, None, [], {}, ("VALIDATION_ERROR", details)

    # safe parsed outputs
    return page, per_page, sort_items, filters, None


def parse_sort_param_strict(raw: Optional[str]) -> Tuple[List[SortItem], List[str]]:
    """
    Strict sort parsing:
    - sort=eta:desc,order_date:asc
    - any invalid segment -> error
    - if absent -> default canonical sort
    - always append id:desc tie-breaker
    """
    errors: List[str] = []
    items: List[SortItem] = []

    if not raw:
        items = [SortItem("eta", "desc"), SortItem("etd", "desc"), SortItem("order_date", "desc")]
    else:
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not parts:
            errors.append("Sort parameter is empty.")
        for p in parts:
            if ":" in p:
                field, direction = p.split(":", 1)
            else:
                field, direction = p, "asc"

            field = field.strip()
            direction = direction.strip().lower()

            if field not in _ALLOWED_SORT_FIELDS and field != "id":
                errors.append(f"Unsupported sort field '{field}'. Allowed: {sorted(_ALLOWED_SORT_FIELDS)}")
                continue
            if direction not in {"asc", "desc"}:
                errors.append(f"Unsupported sort direction '{direction}' for field '{field}'. Use asc|desc.")
                continue

            items.append(SortItem(field, direction))

        if not items and not errors:
            # defensive fallback
            items = [SortItem("eta", "desc"), SortItem("etd", "desc"), SortItem("order_date", "desc")]

    # Always enforce stable tie-breaker
    items.append(SortItem("id", "desc"))
    return items, errors


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
    page, per_page, sort_items, filters, err = validate_query_params()
    if err:
        code, details = err
        return fail(code, "Invalid query parameters.", details=details, status=400)

    # -------------------------
    # Base query + RBAC scope
    # -------------------------
    q = Order.query
    if not can_view_all(current_user.role):
        q = q.filter(Order.user_id == current_user.id)

    if filters["transit_status"]:
        q = q.filter(Order.transit_status == filters["transit_status"])

    if filters["transport"]:
        q = q.filter(Order.transport == filters["transport"])

    if filters["buyer"]:
        q = q.filter(Order.buyer == filters["buyer"])

    if filters["responsible"]:
        q = q.filter(Order.responsible == filters["responsible"])

    if filters["q"]:
        like = f"%{filters['q'].strip()}%"
        q = q.filter(
            Order.order_number.ilike(like) |
            Order.product_name.ilike(like) |
            Order.buyer.ilike(like) |
            Order.responsible.ilike(like)
        )

    # Pull rows (dates stored as strings -> Python sort & year check)
    rows = q.all()

    # Year filter (ANY date matches: legacy semantics)
    if filters["year"]:
        rows = [o for o in rows if order_matches_year(o, filters["year"])]

    # Stable multi-sort
    rows = apply_python_sort(rows, sort_items)

    # Pagination slice
    total = len(rows)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = rows[start:end]

    # Normalize true date fields to ISO for React safety.
    # NOTE: required_delivery is intentionally NOT normalized (often free text).
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
                "transit_status": filters["transit_status"],
                "transport": filters["transport"],
                "buyer": filters["buyer"],
                "responsible": filters["responsible"],
                "year": filters["year"],
                "q": filters["q"],
            },
        },
    )
