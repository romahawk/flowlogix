def serialize_order(o):
    return {
        "id": o.id,
        "order_date": o.order_date or "",
        "order_number": o.order_number,
        "product_name": o.product_name,
        "buyer": o.buyer,
        "responsible": o.responsible,
        "quantity": o.quantity,
        "required_delivery": o.required_delivery or "",
        "terms_of_delivery": o.terms_of_delivery or "",
        "payment_date": o.payment_date or "",
        "etd": o.etd or "",
        "eta": o.eta or "",
        "ata": o.ata or "",
        "transit_status": o.transit_status,
        "transport": o.transport,
    }
