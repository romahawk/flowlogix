import pandas as pd
from app import create_app, db
from app.models import Order

app = create_app()

def format_date(date):
    try:
        if pd.isnull(date):
            return ''
        parsed = pd.to_datetime(date, errors='coerce')
        if pd.isnull(parsed):
            return str(date).strip()  # fallback to raw string like "mid May"
        return parsed.strftime('%d.%m.%y')
    except:
        return str(date).strip()


with app.app_context():
    df = pd.read_excel("data/orders_2025.xlsx")

    for _, row in df.iterrows():
        order = Order(
            user_id=2,  # Replace with actual user ID if needed
            order_date=format_date(row['order_date']),
            order_number=row['order_number'],
            product_name=row['product_name'],
            buyer=row['buyer'],
            responsible=row['responsible'],
            quantity=row['quantity'],
            required_delivery=row['required_delivery'],
            terms_of_delivery=row['terms_of_delivery'],
            payment_date=format_date(row['payment_date']),
            etd=format_date(row['etd']),
            eta=format_date(row['eta']),
            ata=format_date(row['ata']),
            transit_status=row['transit_status'],
            transport=row['transport']
        )
        db.session.add(order)
    db.session.commit()
    print("✅ Orders imported successfully from data/orders_2025.xlsx.")
