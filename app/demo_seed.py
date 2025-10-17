import os
import random
from datetime import date, timedelta
from typing import Tuple

from faker import Faker

from .database import db
from .models import User, Order
from .utils.products import load_products  # adjust import if your loader lives elsewhere

fake = Faker()

# Demo vocab
BUYERS = [
    "Acme Clinics GmbH", "HealthPlus Ltd", "BioCare AG", "Nova Pharma BV",
    "Medico Supplies Sp. z o.o.", "Wellness Partners SA", "PharmaLogis GmbH",
]
RESPONSIBLES = ["Anna Kramer", "Ben Schneider", "Carla Rossi", "David Weber", "Elena Nowak", "Felix Bauer"]
INCOTERMS = ["EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP", "FAS", "FOB", "CFR", "CIF"]
TRANSPORTS = ["sea", "air", "truck"]
STATUSES = ["in process", "en route", "arrived"]


def _ensure_demo_user() -> User:
    user = User.query.filter_by(username="demo").first()
    if not user:
        user = User(username="demo")
        # set email if your model has it (ignore otherwise)
        try:
            setattr(user, "email", "demo@portfolio.app")
        except Exception:
            pass
        user.set_password("demo1234")
        db.session.add(user)
        db.session.commit()
    return user


def _rand_order_number(idx: int, year: int) -> str:
    # PO-YYYY-XXX (zero-padded)
    return f"PO-{year}-{idx:03d}"


def _pick_dates(today: date) -> Tuple[date, date, date | None, str]:
    """
    Returns (etd, eta, ata, transit_status)
    - Ensure ETD <= ETA
    - If 'arrived', set ATA between ETD..ETA (or ETA..ETA+7) and return 'arrived'
    """
    # spread roughly within ±120 days around today
    start = today - timedelta(days=120)
    end = today + timedelta(days=120)
    etd = fake.date_between(start_date=start, end_date=end)
    # eta 5..30 days after etd
    eta = etd + timedelta(days=random.randint(5, 30))

    status = random.choices(STATUSES, weights=[0.4, 0.45, 0.15], k=1)[0]
    ata = None
    if status == "arrived":
        # allow ATA close to ETA (+/- 7 days)
        ata_window_start = max(etd, eta - timedelta(days=7))
        ata_window_end = eta + timedelta(days=7)
        ata = fake.date_between(start_date=ata_window_start, end_date=ata_window_end)

    return etd, eta, ata, status


def seed_orders(count: int | None = None) -> Tuple[str, int]:
    """
    Create demo user if needed and insert `count` random orders for that user.
    Respects env DEMO_SEED_COUNT if `count` is None.
    Returns: (username, inserted_count)
    """
    count = count or int(os.getenv("DEMO_SEED_COUNT", "50"))
    user = _ensure_demo_user()
    products = load_products() or ["Amoxicillin trihydrate"]

    today = date.today()
    year = today.year

    created = 0
    base_counter = Order.query.count() + 1

    for i in range(count):
        order_no = _rand_order_number(base_counter + i, year)
        etd, eta, ata, status = _pick_dates(today)

        # quantity: 1..1000 (integers) or 0.5 steps? Use int for simplicity.
        qty = random.randint(10, 2000)

        o = Order(
            order_date=fake.date_between(start_date=today - timedelta(days=150), end_date=today + timedelta(days=10)),
            order_number=order_no,
            product_name=random.choice(products),
            buyer=random.choice(BUYERS),
            responsible=random.choice(RESPONSIBLES),
            quantity=qty,
            required_delivery=random.choice([
                "ASAP",
                f"By Q{random.randint(1,4)} {year}",
                f"By {fake.month_name()} {year}",
            ]),
            terms_of_delivery=random.choice(INCOTERMS),
            payment_date=fake.date_between(start_date=today - timedelta(days=60), end_date=today + timedelta(days=60)),
            etd=etd,
            eta=eta,
            ata=ata,
            transit_status=status,
            transport=random.choice(TRANSPORTS),
            user_id=user.id,
        )
        db.session.add(o)
        created += 1

    db.session.commit()
    return user.username, created
